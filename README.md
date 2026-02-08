# SolarEdgeController (Local API)

Home Assistant custom integration for a local SolarEdgeController HTTP(S) API.

This integration requires the SolarEdgeController backend to be running and exposing the HTTP endpoints described below:

- https://github.com/niklasmelin/SolarEdgeController

---

## Features

- Creates Home Assistant **Sensor** entities from `GET /sensors`
- Creates Home Assistant **Switch** entities for:
  - `limit_export`
  - `auto_mode`
- Creates Home Assistant **Number** entities (integers) for:
  - `auto_mode_threshold`
  - `power_limit_W` (clamped to an allowed range)
- Polling via `DataUpdateCoordinator`
- History works out of the box (each sensor register is its own entity)
- Optional service `solaredgecontroller.set_control` calls `POST /control`
- Supports HTTPS + Bearer token + optional SSL verification (useful for self-signed certs)

---

## Entities created

### Sensors (from `/sensors`)
- One `sensor.*` entity per key returned by `GET /sensors`

### Switches (from `/status/json -> control`)
- `switch.solaredge_auto_mode` (default name: “SolarEdge Auto mode”)
- `switch.solaredge_limit_export` (default name: “SolarEdge Limit export”)

### Numbers (from `/status/json -> control`)
- `number.solaredge_auto_mode_threshold` (integer, W)
- `number.solaredge_power_limit` (integer, W)

> Note: If you installed an earlier version, existing entity_ids in Home Assistant won’t automatically rename. Rename them once in the UI if needed.

---

## API requirements

The SolarEdgeController backend must expose:

### Read endpoints

#### `GET /status/json`
Must return JSON including:
- `control.limit_export` (bool)
- `control.auto_mode` (bool)
- `control.auto_mode_threshold` (number; treated as int in HA)
- `control.power_limit_W` (number; treated as int in HA)
- `status.inverter_min_power_W` (number)
- `status.inverter_max_power_W` (number)

Example (trimmed):

```json
{
  "status": {
    "inverter_min_power_W": 500,
    "inverter_max_power_W": 10500
  },
  "control": {
    "limit_export": false,
    "auto_mode": true,
    "auto_mode_threshold": 200.0,
    "power_limit_W": 10500.0
  }
}
```

#### `GET /sensors`
Returns a JSON dict of sensors. Each value should include at least `state`. If `friendly_name` exists, it will be used as the sensor name.

### Write endpoint

#### `POST /control`
Accepts JSON payload updates, e.g.:

```json
{
  "auto_mode": true,
  "power_limit_W": 3500
}
```

### Authentication

If the controller is configured with `API.TOKEN`, the integration will send:

- `Authorization: Bearer <token>`

`GET /status/json` may be public in your controller setup; `GET /sensors` and `POST /control` are typically protected.

---

## Power limit bounds

The integration enforces:
- `power_limit_W >= 500`
- `power_limit_W <= inverter_max_power_W` (read from `/status/json -> status.inverter_max_power_W`)

If `auto_mode` is enabled, manual writes to `power_limit_W` are blocked (by design).

---

## Setup

1) Install via HACS (custom repository), or copy `custom_components/solaredgecontroller` into your HA config.
2) Restart Home Assistant.
3) Add integration:
   **Settings → Devices & services → Add Integration → SolarEdgeController**
4) Enter:
   - Base URL: e.g. `https://solaredgepi:8080`
   - Token: your API token
   - Verify SSL: disable if you use a self-signed certificate

---

## Example: service call to `/control` (optional)

Service: `solaredgecontroller.set_control`

```yaml
service: solaredgecontroller.set_control
data:
  auto_mode: false
  power_limit_W: 3500
```

In normal usage you should control these through the created switch/number entities; the service exists mainly for advanced automation workflows.
