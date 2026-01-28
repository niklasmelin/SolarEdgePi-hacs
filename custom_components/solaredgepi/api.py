from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession


class SolarEdgeControllerApiError(Exception):
    """Base error for API problems."""


class SolarEdgeControllerAuthError(SolarEdgeControllerApiError):
    """Raised on 401/403."""


@dataclass(frozen=True)
class SolarEdgeControllerApiClient:
    session: ClientSession
    base_url: str
    token: str
    verify_ssl: bool
    timeout: int = 10

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _ssl_param(self) -> Any:
        # aiohttp: ssl=False disables certificate verification (useful for self-signed certs)
        return None if self.verify_ssl else False

    async def async_get_sensors(self) -> dict[str, Any]:
        try:
            async with self.session.get(
                self._url("/sensors"),
                headers=self._headers(),
                ssl=self._ssl_param(),
                timeout=self.timeout,
            ) as resp:
                if resp.status in (401, 403):
                    raise SolarEdgeControllerAuthError("Unauthorized")
                resp.raise_for_status()
                return await resp.json()
        except SolarEdgeControllerAuthError:
            raise
        except (asyncio.TimeoutError, ClientResponseError, ClientError, json.JSONDecodeError) as err:
            raise SolarEdgeControllerApiError(str(err)) from err

    async def async_set_control(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with self.session.post(
                self._url("/control"),
                headers={**self._headers(), "Content-Type": "application/json"},
                json=payload,
                ssl=self._ssl_param(),
                timeout=self.timeout,
            ) as resp:
                if resp.status in (401, 403):
                    raise SolarEdgeControllerAuthError("Unauthorized")
                resp.raise_for_status()
                return await resp.json()
        except SolarEdgeControllerAuthError:
            raise
        except (asyncio.TimeoutError, ClientResponseError, ClientError, json.JSONDecodeError) as err:
            raise SolarEdgeControllerApiError(str(err)) from err
