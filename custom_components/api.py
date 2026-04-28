"""Async API client for getAir ventilation systems."""
from __future__ import annotations

import logging
from urllib.parse import urljoin

import aiohttp

from .const import AUTH_URL, API_URL, CLIENT_ID

_LOGGER = logging.getLogger(__name__)


class GetAirApiError(Exception):
    """Raised when an API call fails."""


class GetAirAuthError(GetAirApiError):
    """Raised when authentication fails."""


class GetAirClient:
    """Async client for the getAir REST API."""

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession) -> None:
        self._username = username
        self._password = password
        self._session = session
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    async def authenticate(self) -> None:
        """Authenticate and obtain an access token."""
        payload = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password,
            "client_id": CLIENT_ID,
            "scope": "offline_access",
        }
        url = urljoin(AUTH_URL + "/", "oauth/token")
        async with self._session.post(url, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise GetAirAuthError(f"Authentication failed ({resp.status}): {text}")
            data = await resp.json()
            self._access_token = data["access_token"]
            self._refresh_token = data.get("refresh_token")
            _LOGGER.debug("getAir authentication successful")

    async def _refresh(self) -> bool:
        """Try to refresh the access token. Returns True on success."""
        if not self._refresh_token:
            return False
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": CLIENT_ID,
            "scope": "offline_access",
        }
        url = urljoin(AUTH_URL + "/", "oauth/token")
        try:
            async with self._session.post(url, json=payload) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                self._access_token = data["access_token"]
                _LOGGER.debug("getAir token refreshed")
                return True
        except aiohttp.ClientError:
            return False

    async def _get(self, path: str) -> dict:
        """Make an authenticated GET request, refreshing token if needed."""
        url = urljoin(API_URL + "/", path.lstrip("/"))
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with self._session.get(url, headers=headers) as resp:
            if resp.status == 401:
                _LOGGER.debug("getAir token expired, refreshing...")
                if await self._refresh():
                    headers = {"Authorization": f"Bearer {self._access_token}"}
                    async with self._session.get(url, headers=headers) as resp2:
                        if resp2.status != 200:
                            raise GetAirApiError(f"GET {path} failed after refresh: {resp2.status}")
                        return await resp2.json()
                else:
                    await self.authenticate()
                    headers = {"Authorization": f"Bearer {self._access_token}"}
                    async with self._session.get(url, headers=headers) as resp3:
                        if resp3.status != 200:
                            raise GetAirApiError(f"GET {path} failed after re-auth: {resp3.status}")
                        return await resp3.json()
            if resp.status != 200:
                raise GetAirApiError(f"GET {path} failed: {resp.status}")
            return await resp.json()

    async def _put(self, path: str, data: dict) -> None:
        """Make an authenticated PUT request."""
        url = urljoin(API_URL + "/", path.lstrip("/"))
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        async with self._session.put(url, json=data, headers=headers) as resp:
            if resp.status == 401:
                _LOGGER.debug("getAir token expired on PUT, refreshing...")
                if await self._refresh():
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.put(url, json=data, headers=headers) as resp2:
                        if resp2.status not in (200, 204):
                            raise GetAirApiError(f"PUT {path} failed after refresh: {resp2.status}")
                        return
                else:
                    await self.authenticate()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    async with self._session.put(url, json=data, headers=headers) as resp3:
                        if resp3.status not in (200, 204):
                            raise GetAirApiError(f"PUT {path} failed after re-auth: {resp3.status}")
                        return
            if resp.status not in (200, 204):
                raise GetAirApiError(f"PUT {path} failed: {resp.status}")

    async def get_devices(self) -> list[dict]:
        """Return list of devices on the account."""
        return await self._get("api/v1/devices/")

    async def get_device_id(self) -> str:
        """Return the main device MAC (without zone prefix)."""
        devices = await self.get_devices()
        for d in devices:
            ident = d.get("deviceIdentifier", "")
            if "." not in ident:
                return ident
        raise GetAirApiError("No main device found")

    async def get_system_data(self, device_id: str) -> dict:
        """Fetch the System service data for a device."""
        return await self._get(f"api/v1/devices/{device_id}/services/System")

    async def get_zone_data(self, device_id: str, zone: int = 1) -> dict:
        """Fetch the Zone service data for a device."""
        return await self._get(f"api/v1/devices/{zone}.{device_id}/services/Zone")

    async def set_zone_property(self, device_id: str, data: dict, zone: int = 1) -> None:
        """Set one or more Zone properties."""
        await self._put(f"api/v1/devices/{zone}.{device_id}/services/Zone", data)
