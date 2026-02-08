from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolarEdgeControllerApiClient, SolarEdgeControllerApiError, SolarEdgeControllerAuthError
from .const import (
    CONF_BASE_URL,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_TOKEN,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SolarEdgeControllerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url: str = user_input[CONF_BASE_URL]
            token: str = user_input[CONF_TOKEN]
            verify_ssl: bool = user_input[CONF_VERIFY_SSL]

            session = async_get_clientsession(self.hass)
            api = SolarEdgeControllerApiClient(
                session=session,
                base_url=base_url,
                token=token,
                verify_ssl=verify_ssl,
                timeout=DEFAULT_TIMEOUT,
            )

            try:
                # /status/json is intentionally not auth-protected (in controller server.py).
                await api.async_get_status()

                # Validate token by hitting /sensors (auth protected), but allow 503 during identity init.
                try:
                    await api.async_get_sensors()
                except SolarEdgeControllerAuthError:
                    raise
                except SolarEdgeControllerApiError as err:
                    # /sensors returns 503 while inverter identity registers are not ready.
                    # Treat as OK for setup; entities will appear once /sensors stabilizes.
                    _LOGGER.debug("/sensors not ready yet during setup: %s", err)

            except SolarEdgeControllerAuthError:
                errors["base"] = "invalid_auth"
            except SolarEdgeControllerApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pragma: no cover
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(base_url)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"SolarEdgeController ({base_url})",
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_TOKEN: token,
                        CONF_VERIFY_SSL: verify_ssl,
                    },
                    options={
                        CONF_TIMEOUT: DEFAULT_TIMEOUT,
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=(user_input or {}).get(CONF_BASE_URL, "")): str,
                vol.Required(CONF_TOKEN, default=(user_input or {}).get(CONF_TOKEN, "")): str,
                vol.Required(CONF_VERIFY_SSL, default=(user_input or {}).get(CONF_VERIFY_SSL, True)): bool,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return SolarEdgeControllerOptionsFlow(config_entry)


class SolarEdgeControllerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_TIMEOUT,
                    default=self.config_entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                ): vol.Coerce(int),
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.Coerce(int),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
