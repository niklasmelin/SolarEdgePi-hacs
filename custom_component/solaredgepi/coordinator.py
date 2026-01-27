from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolarEdgeControllerApiClient, SolarEdgeControllerApiError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SolarEdgeControllerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch sensor data from the SolarEdgeController API."""

    def __init__(self, hass: HomeAssistant, api: SolarEdgeControllerApiClient, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval or DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_get_sensors()
            if not isinstance(data, dict):
                raise UpdateFailed("Unexpected API response (expected dict)")
            return data
        except SolarEdgeControllerApiError as err:
            raise UpdateFailed(str(err)) from err
