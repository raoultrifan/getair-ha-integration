"""Sensor platform for getAir integration."""
from __future__ import annotations

from datetime import datetime, timezone

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODES_REVERSE


@dataclass
class GetAirSensorEntityDescription(SensorEntityDescription):
    """Describes a getAir sensor."""
    service: str = "zone"
    value_fn: Any = None


SENSOR_DESCRIPTIONS: tuple[GetAirSensorEntityDescription, ...] = (
    GetAirSensorEntityDescription(
        key="temperature",
        name="Indoor Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        service="zone",
        value_fn=lambda d: round(d["zone"].get("temperature", 0), 1),
    ),
    GetAirSensorEntityDescription(
        key="humidity",
        name="Indoor Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        service="zone",
        value_fn=lambda d: round(float(d["zone"].get("humidity", 0)), 1),
    ),
    GetAirSensorEntityDescription(
        key="indoor_air_quality",
        name="Indoor Air Quality",
        native_unit_of_measurement="IAQ",
        state_class=SensorStateClass.MEASUREMENT,
        service="system",
        value_fn=lambda d: d["system"].get("indoor-air-quality"),
    ),
    GetAirSensorEntityDescription(
        key="fan_speed",
        name="Fan Speed",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        service="zone",
        value_fn=lambda d: round(float(d["zone"].get("speed", 0)), 1),
    ),
    GetAirSensorEntityDescription(
        key="runtime",
        name="Runtime",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        service="zone",
        value_fn=lambda d: d["zone"].get("runtime"),
    ),
    GetAirSensorEntityDescription(
        key="iaq_accuracy",
        name="IAQ Accuracy",
        native_unit_of_measurement=None,
        state_class=SensorStateClass.MEASUREMENT,
        service="system",
        value_fn=lambda d: d["system"].get("iaq-accuracy"),
    ),
    GetAirSensorEntityDescription(
        key="boot_time",
        name="Last Boot",
        device_class=SensorDeviceClass.TIMESTAMP,
        service="system",
        value_fn=lambda d: datetime.fromtimestamp(d["system"].get("boot-time", 0), tz=timezone.utc),
    ),
    GetAirSensorEntityDescription(
        key="notification",
        name="Notification",
        service="system",
        value_fn=lambda d: d["system"].get("notification"),
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up getAir sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    device_id = data["device_id"]

    async_add_entities(
        GetAirSensor(coordinator, description, device_id, entry.entry_id)
        for description in SENSOR_DESCRIPTIONS
    )


class GetAirSensor(CoordinatorEntity, SensorEntity):
    """Representation of a getAir sensor."""

    entity_description: GetAirSensorEntityDescription

    def __init__(self, coordinator, description, device_id, entry_id):
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device_id)},
            "name": "getAir ComfortControl Pro BT",
            "manufacturer": "getAir",
            "model": "ComfortControl Pro BT",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        try:
            return self.entity_description.value_fn(self.coordinator.data)
        except Exception:
            return None
