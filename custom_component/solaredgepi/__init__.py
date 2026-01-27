"""SolarEdgeController integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolarEdgeControllerApiClient
from .const import (
    ATTR_CURRENT_PRICE,
    ATTR_ENTRY_ID,
    ATTR_NEGATIVE_PRICE,
    CONF_BASE_URL,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_TOKEN,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PLATFORMS,
    SERVICE_SET_CONTROL,
)
from .coordinator import SolarEdgeControllerCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTRY_ID): str,
        vol.Optional(ATTR_CURRENT_PRICE): vol.Coerce(float),
        vol.Optional(ATTR_NEGATIVE_PRICE): bool,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolarEdgeController from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)

    base_url: str = entry.data[CONF_BASE_URL]
    token: str = entry.data[CONF_TOKEN]
    verify_ssl: bool = entry.data[CONF_VERIFY_SSL]

    timeout: int = entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    scan_interval: int = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    api = SolarEdgeControllerApiClient(
        session=session,
        base_url=base_url,
        token=token,
        verify_ssl=verify_ssl,
        timeout=timeout,
    )

    coordinator = SolarEdgeControllerCoordinator(
        hass=hass,
        api=api,
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "entry": entry,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the service once globally
    if not hass.services.has_service(DOMAIN, SERVICE_SET_CONTROL):

        async def _handle_set_control(call: ServiceCall) -> None:
            entry_id = call.data.get(ATTR_ENTRY_ID)

            if entry_id:
                targets = [entry_id]
            else:
                targets = list(hass.data.get(DOMAIN, {}).keys())

            if not targets:
                raise HomeAssistantError("No SolarEdgeController config entries are loaded.")

            if not entry_id and len(targets) != 1:
                raise HomeAssistantError(
                    "Multiple SolarEdgeController entries exist; specify 'entry_id' in the service call."
                )

            payload: dict[str, Any] = {}
            if ATTR_CURRENT_PRICE in call.data:
                payload["current_price"] = call.data[ATTR_CURRENT_PRICE]
            if ATTR_NEGATIVE_PRICE in call.data:
                payload["negative_price"] = call.data[ATTR_NEGATIVE_PRICE]

            if not payload:
                raise HomeAssistantError("No fields provided. Set 'current_price' and/or 'negative_price'.")

            for tid in targets:
                api_client: SolarEdgeControllerApiClient = hass.data[DOMAIN][tid]["api"]
                await api_client.async_set_control(payload)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_CONTROL,
            _handle_set_control,
            schema=SERVICE_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
