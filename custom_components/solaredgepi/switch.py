from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SolarEdgeControllerApiClient
from .const import DOMAIN, ATTR_AUTO_MODE, ATTR_LIMIT_EXPORT
from .coordinator import SolarEdgeControllerCoordinator


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
            SolarEdgeControllerSwitch(coordinator, api, entry, ATTR_LIMIT_EXPORT, "SolarEdge Limit export"),
            SolarEdgeControllerSwitch(coordinator, api, entry, ATTR_AUTO_MODE, "SolarEdge Auto mode"),
        ]
    )


class SolarEdgeControllerSwitch(CoordinatorEntity[SolarEdgeControllerCoordinator], SwitchEntity):
    def __init__(
        self,
        coordinator: SolarEdgeControllerCoordinator,
        api: SolarEdgeControllerApiClient,
        entry: ConfigEntry,
        control_key: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._api = api
        self._entry = entry
        self._control_key = control_key

        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{control_key}"

    @property
    def is_on(self) -> bool:
        control = self.coordinator.data.get("control", {}) if self.coordinator.data else {}
        return bool(control.get(self._control_key, False))

    async def async_turn_on(self, **kwargs) -> None:
        await self._api.async_set_control({self._control_key: True})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self._api.async_set_control({self._control_key: False})
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id or self._entry.entry_id)},
            name="SolarEdgeController",
            manufacturer="SolarEdge",
        )
