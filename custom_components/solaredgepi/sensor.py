from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarEdgeControllerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: SolarEdgeControllerCoordinator = data["coordinator"]

    entities: list[SolarEdgeControllerSensor] = []
    for key in coordinator.data.keys():
        entities.append(SolarEdgeControllerSensor(coordinator, entry, key))

    async_add_entities(entities)


class SolarEdgeControllerSensor(CoordinatorEntity[SolarEdgeControllerCoordinator], SensorEntity):
    """Representation of a sensor exposed by SolarEdgeController."""

    def __init__(
        self,
        coordinator: SolarEdgeControllerCoordinator,
        entry: ConfigEntry,
        sensor_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_key = sensor_key

        meta = self._meta or {}

        self._attr_unique_id = meta.get("unique_id") or f"{entry.entry_id}_{sensor_key}"
        self._attr_name = meta.get("friendly_name") or sensor_key.replace("_", " ").title()

        # Device grouping in UI
        self._device_identifier = entry.unique_id or entry.entry_id

        self._attr_device_class = _safe_enum(SensorDeviceClass, meta.get("device_class"))
        self._attr_state_class = _safe_enum(SensorStateClass, meta.get("state_class"))
        self._attr_entity_category = _safe_enum(EntityCategory, meta.get("entity_category"))

        unit = meta.get("unit")
        if unit:
            self._attr_native_unit_of_measurement = unit

        icon = meta.get("icon")
        if icon:
            self._attr_icon = icon

    @property
    def _meta(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        meta = data.get(self._sensor_key, {})
        return meta if isinstance(meta, dict) else {}

    @property
    def native_value(self) -> Any:
        return self._meta.get("state")

    @property
    def available(self) -> bool:
        meta_available = self._meta.get("available", True)
        return bool(self.coordinator.last_update_success and meta_available)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        desc = self._meta.get("description")
        if desc:
            attrs["description"] = desc
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        uid = self._attr_unique_id or ""
        serial = uid.split("_", 1)[0] if "_" in uid else None
        name = f"SolarEdge Inverter {serial}" if serial else "SolarEdge Inverter"

        return DeviceInfo(
            identifiers={(DOMAIN, serial or self._device_identifier)},
            name=name,
            manufacturer="SolarEdge",
        )


def _safe_enum(enum_cls: Any, value: Any) -> Any:
    if value is None:
        return None
    try:
        return enum_cls(value)
    except Exception:
        return None
