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
    """Coordinator fetching both sensors and control state."""

    def __init__(self, hass: HomeAssistant, api: SolarEdgeControllerApiClient, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval or DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

        # Best-effort upper bound for power_limit_W:
        # - if controller exposes explicit limits, use those
        # - otherwise keep max observed power_limit_W (controller defaults it to PEAK_PRODUCTION_W at startup)
        self._max_power_w: int | None = None

    @property
    def max_power_w(self) -> int | None:
        return self._max_power_w

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            status = await self.api.async_get_status()
            if not isinstance(status, dict):
                raise UpdateFailed("Unexpected /status/json response (expected dict)")

            # /sensors can return 503 during inverter identity init; treat as empty and keep retrying on future refreshes
            sensors: dict[str, Any] = {}
            try:
                s = await self.api.async_get_sensors()
                if isinstance(s, dict):
                    sensors = s
            except SolarEdgeControllerApiError as err:
                # Some errors should fail the update; 503 is wrapped as ClientResponseError.
                # We keep coordinator alive using status-only data and log the issue.
                _LOGGER.debug("Failed to fetch /sensors this cycle: %s", err)

            control = status.get("control") if isinstance(status.get("control"), dict) else {}
            limits = status.get("limits") if isinstance(status.get("limits"), dict) else {}

            # Update max_power_w:
            # 1) explicit limits if present
            max_from_limits = None
            try:
                max_from_limits = int(limits.get("power_limit_W", {}).get("max"))  # type: ignore[union-attr]
            except Exception:
                max_from_limits = None

            if max_from_limits and max_from_limits > 0:
                self._max_power_w = max_from_limits
            else:
                # 2) keep max observed control power_limit_W
                try:
                    pl = control.get("power_limit_W")
                    if pl is not None:
                        pl_i = int(round(float(pl)))
                        if pl_i > 0 and (self._max_power_w is None or pl_i > self._max_power_w):
                            self._max_power_w = pl_i
                except Exception:
                    pass

            return {
                "status": status.get("status", {}) if isinstance(status.get("status"), dict) else {},
                "history": status.get("history", {}) if isinstance(status.get("history"), dict) else {},
                "control": control,
                "limits": limits,
                "sensors": sensors,
            }
        except SolarEdgeControllerApiError as err:
            raise UpdateFailed(str(err)) from err
