from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SolarEdgeControllerApiClient
from .const import (
    DOMAIN,
    ATTR_AUTO_MODE,
    ATTR_AUTO_MODE_THRESHOLD,
    ATTR_POWER_LIMIT_W,
)
from .coordinator import SolarEdgeControllerCoordinator

_MIN_POWER_W = 500


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    api: SolarEdgeControllerApiClient = data["api"]
    coordinator: SolarEdgeControllerCoordinator = data["coordinator"]

    async_add_entities(
        [
            SolarEdgeControllerNumber(
                coordinator,
                api,
                entry,
                ATTR_AUTO_MODE_THRESHOLD,
                "SolarEdgeAuto mode threshold",
                min_value=0,
                max_value_fn=lambda: coordinator.max_power_w,
                step=100,
            ),
            SolarEdgeControllerNumber(
                coordinator,
                api,
                entry,
                ATTR_POWER_LIMIT_W,
                "SolarEdge Power limit",
                min_value=_MIN_POWER_W,
                max_value_fn=lambda: coordinator.max_power_w,
                step=100,
                block_when_auto_mode=True,
            ),
        ]
    )


class SolarEdgeControllerNumber(CoordinatorEntity[SolarEdgeControllerCoordinator], NumberEntity):
    def __init__(
        self,
        coordinator: SolarEdgeControllerCoordinator,
        api: SolarEdgeControllerApiClient,
        entry: ConfigEntry,
        control_key: str,
        name: str,
        *,
        min_value: int,
        max_value_fn,
        step: int = 100,
        block_when_auto_mode: bool = False,
    ) -> None:
        super().__init__(coordinator)
        self._api = api
        self._entry = entry
        self._control_key = control_key
        self._min = int(min_value)
        self._max_value_fn = max_value_fn
        self._step = int(step)
        self._block_when_auto_mode = block_when_auto_mode

        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{control_key}"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_mode = NumberMode.BOX
        self._attr_native_step = float(self._step)
        self._attr_native_min_value = float(self._min)

    @property
    def native_value(self) -> float | None:
        control = self.coordinator.data.get("control", {}) if self.coordinator.data else {}
        val = control.get(self._control_key)
        if val is None:
            return None
        try:
            return float(int(round(float(val))))
        except Exception:
            return None

    @property
    def native_max_value(self) -> float:
        max_w = self._max_value_fn()
        if max_w is None:
            # Fallback if we couldn't learn max power yet
            max_w = 10000
        try:
            max_i = int(max_w)
        except Exception:
            max_i = 10000

        # Ensure max is always >= min
        return float(max(max_i, self._min))

    async def async_set_native_value(self, value: float) -> None:
        if self._block_when_auto_mode:
            control = self.coordinator.data.get("control", {}) if self.coordinator.data else {}
            if bool(control.get(ATTR_AUTO_MODE, False)):
                raise HomeAssistantError("Auto mode is enabled; manual power limit is blocked.")

        # Coerce to int and clamp
        v = int(round(float(value)))
        v = max(self._min, min(v, int(self.native_max_value)))

        await self._api.async_set_control({self._control_key: v})
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id or self._entry.entry_id)},
            name="SolarEdgeController",
            manufacturer="SolarEdge",
        )
