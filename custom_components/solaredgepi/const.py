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

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]

SERVICE_SET_CONTROL = "set_control"

ATTR_ENTRY_ID = "entry_id"
# Attributes for controll limit_export, auto_mode, auto_mode_threshold, power_limit_W
ATTR_LIMIT_EXPORT = "limit_export"
ATTR_AUTO_MODE = "auto_mode"
ATTR_AUTO_MODE_THRESHOLD = "auto_mode_threshold"
ATTR_POWER_LIMIT_W = "power_limit_W"
