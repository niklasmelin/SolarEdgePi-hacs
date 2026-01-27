from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "solaredgecontroller"

CONF_BASE_URL = "base_url"
CONF_TOKEN = "token"
CONF_VERIFY_SSL = "verify_ssl"
CONF_TIMEOUT = "timeout"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_TIMEOUT = 10
DEFAULT_SCAN_INTERVAL = 10  # seconds

PLATFORMS: list[Platform] = [Platform.SENSOR]

SERVICE_SET_CONTROL = "set_control"

ATTR_ENTRY_ID = "entry_id"
ATTR_CURRENT_PRICE = "current_price"
ATTR_NEGATIVE_PRICE = "negative_price"
