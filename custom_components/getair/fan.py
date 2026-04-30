"""Fan platform for getAir integration."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import DOMAIN, MODES, MODES_REVERSE

_LOGGER = logging.getLogger(__name__)

# Speed range: 0.9 (min) to 4.0 (max), in 0.1 steps
SPEED_RANGE = (0.9, 4.0)
SPEED_COUNT = round((SPEED_RANGE[1] - SPEED_RANGE[0]) / 0.1)  # 31 steps


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up getAir fan entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        GetAirFan(
            coordinator=data["coordinator"],
            client=data["client"],
            device_id=data["device_id"],
            entry_id=entry.entry_id,
        )
    ])


class GetAirFan(CoordinatorEntity, FanEntity):
    """Representation of the getAir ventilation unit as a HA fan entity."""

    _attr_name = "getAir Fan"
    _attr_icon = "mdi:hvac"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_preset_modes = list(MODES.keys())

    def __init__(self, coordinator, client, device_id, entry_id):
        super().__init__(coordinator)
        self._client = client
        self._device_id = device_id
        self._attr_unique_id = f"{entry_id}_fan"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": "getAir ComfortControl Pro BT",
            "manufacturer": "getAir",
            "model": "ComfortControl Pro BT",
        }

    def _zone(self) -> dict:
        return self.coordinator.data["zone"] if self.coordinator.data else {}

    @property
    def is_on(self) -> bool:
        return float(self._zone().get("speed", 0)) > 0

    @property
    def percentage(self) -> int | None:
        speed = float(self._zone().get("speed", 0))
        if speed <= 0:
            return 0
        return ranged_value_to_percentage(SPEED_RANGE, speed)

    @property
    def speed_count(self) -> int:
        return SPEED_COUNT

    @property
    def preset_mode(self) -> str | None:
        api_mode = self._zone().get("mode")
        return MODES_REVERSE.get(api_mode, api_mode)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan, optionally at a given speed/mode."""
        if preset_mode:
            await self._set_mode(preset_mode)
        speed = None
        if percentage is not None:
            speed = self._percentage_to_speed(percentage)
        else:
            # Resume to speed 1.0 if no percentage given
            speed = 1.0
        await self._client.set_zone_property(self._device_id, {"speed": speed})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self._client.set_zone_property(self._device_id, {"speed": 0})
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed by percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return
        speed = self._percentage_to_speed(percentage)
        await self._client.set_zone_property(self._device_id, {"speed": speed})
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set ventilation mode."""
        await self._set_mode(preset_mode)
        await self.coordinator.async_request_refresh()

    async def _set_mode(self, preset_mode: str) -> None:
        api_mode = MODES.get(preset_mode)
        if not api_mode:
            _LOGGER.error("Unknown preset mode: %s", preset_mode)
            return
        await self._client.set_zone_property(self._device_id, {"mode": api_mode})

    def _percentage_to_speed(self, percentage: int) -> float:
        """Convert HA percentage (1-100) to getAir speed (0.9-4.0)."""
        raw = percentage_to_ranged_value(SPEED_RANGE, percentage)
        # Round to nearest 0.1
        return round(round(raw / 0.1) * 0.1, 1)
