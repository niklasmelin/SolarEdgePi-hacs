# SolarEdgeController (Local API)

Home Assistant custom integration for a local SolarEdgeController HTTP(S) API.

## Features
- Creates one Home Assistant sensor entity per register from `GET /sensors`
- Polling via DataUpdateCoordinator
- History works out of the box (each register is its own entity)
- Service `solaredgecontroller.set_control` calls `POST /control`
- Supports HTTPS + Bearer token + optional SSL verification (for self-signed certs)

## API Requirements
The controller must expose:
- `GET /sensors` -> JSON dict of sensors
- `POST /control` -> accepts JSON payload like `{"current_price": 1.23, "negative_price": false}`

If API.TOKEN is set, endpoints require:
`Authorization: Bearer <token>`

## Setup
1) Install via HACS (custom repository), or copy `custom_components/solaredgecontroller` into your HA config.
2) Restart Home Assistant.
3) Add integration:
   Settings -> Devices & services -> Add Integration -> SolarEdgeController
4) Enter:
   - Base URL: `https://solaredgepi:8080`
   - Token: your API token
   - Verify SSL: disable if you use a self-signed certificate

## Example automation calling /control
Use service:
- service: `solaredgecontroller.set_control`
- data:
    current_price: 0.12
    negative_price: false
