"""Async HTTP client for RainMaker REST endpoints.

This client provides a small, well-typed surface used by the
Home Assistant integration: login, get_nodes, get_params, get_config,
set_params.

The implementation intentionally avoids any heavy crypto dependencies
and relies on simple HTTP calls using aiohttp.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from yarl import URL
import aiohttp

from .exceptions import (
    RainmakerAuthError,
    RainmakerConnectionError,
    RainmakerSetError,
)

_LOGGER = logging.getLogger(__name__)


class RainmakerClient:
    """Async client for RainMaker HTTP endpoints.

    Example usage:
        async with RainmakerClient("https://api.rainmaker.example/") as c:
            await c.async_login("user", "pass")
            nodes = await c.async_get_nodes()
    """

    def __init__(self, base_url: str, session: Optional[aiohttp.ClientSession] = None, timeout: int = 10) -> None:
        self._base_url = base_url.rstrip("/") + "/" if base_url else ""
        self._session = session
        self._owns_session = session is None
        self._headers: Dict[str, str] = {"Content-Type": "application/json"}
        self._timeout = timeout
        self._connected = False

    async def _ensure_session(self) -> None:
        if self._session is not None:
            return
        self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def __aenter__(self) -> "RainmakerClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def async_login(self, username: str, password: str) -> None:
        await self._ensure_session()
        url = URL(self._base_url) / "login2"
        try:
            resp = await self._session.post(
                str(url), json={"user_name": username, "password": password}, headers=self._headers, timeout=self._timeout
            )
            text = await resp.text()
            if getattr(resp, "status", None) != 200:
                _LOGGER.debug("Login failed HTTP %s: %s", getattr(resp, "status", None), text)
                raise RainmakerConnectionError("Login HTTP error")
            # Try parse JSON
            try:
                data = await resp.json()
            except Exception:
                _LOGGER.debug("Login response not JSON: %s", text)
                raise RainmakerConnectionError("Invalid login response")

            if not isinstance(data, dict) or data.get("status") != "success":
                _LOGGER.debug("Login rejected: %s", data)
                raise RainmakerAuthError("Authentication failed")

            token = (
                data.get("accesstoken")
                or data.get("access_token")
                or data.get("idtoken")
                or data.get("id_token")
                or data.get("token")
            )
            if not token:
                raise RainmakerAuthError("No token returned from login")
            self._headers["Authorization"] = token
            self._connected = True
        except aiohttp.ClientError as err:
            _LOGGER.debug("Login request failed: %s", err)
            raise RainmakerConnectionError("Login transport error") from err

    async def async_get_nodes(self, node_details: bool = True) -> List[Dict[str, Any]]:
        if not self._connected:
            raise RainmakerConnectionError("Not connected")
        url = URL(self._base_url) / "user/nodes"
        params = {"node_details": "true"} if node_details else None
        try:
            resp = await self._session.get(str(url), headers=self._headers, params=params, timeout=self._timeout)
            # Some session mocks or clients may not provide raise_for_status
            if hasattr(resp, "raise_for_status"):
                resp.raise_for_status()
            return await resp.json()
        except aiohttp.ClientError as err:
            _LOGGER.debug("get_nodes failed: %s", err)
            raise RainmakerConnectionError("Failed to fetch nodes") from err

    async def async_get_params(self, nodeid: str) -> Dict[str, Any]:
        if not self._connected:
            raise RainmakerConnectionError("Not connected")
        url = URL(self._base_url) / "user/nodes/params"
        try:
            resp = await self._session.get(str(url), headers=self._headers, params={"nodeid": nodeid}, timeout=self._timeout)
            if hasattr(resp, "raise_for_status"):
                resp.raise_for_status()
            return await resp.json()
        except aiohttp.ClientError as err:
            _LOGGER.debug("get_params failed: %s", err)
            raise RainmakerConnectionError("Failed to fetch params") from err

    async def async_get_config(self, nodeid: str) -> Dict[str, Any]:
        if not self._connected:
            raise RainmakerConnectionError("Not connected")
        url = URL(self._base_url) / "user/nodes/config"
        try:
            resp = await self._session.get(str(url), headers=self._headers, params={"nodeid": nodeid}, timeout=self._timeout)
            if hasattr(resp, "raise_for_status"):
                resp.raise_for_status()
            return await resp.json()
        except aiohttp.ClientError as err:
            _LOGGER.debug("get_config failed: %s", err)
            raise RainmakerConnectionError("Failed to fetch config") from err

    async def async_set_params(self, batch: List[Dict[str, Any]]) -> Any:
        if not self._connected:
            raise RainmakerConnectionError("Not connected")
        url = URL(self._base_url) / "user/nodes/params"
        try:
            resp = await self._session.put(str(url), headers=self._headers, json=batch, timeout=self._timeout)
            if hasattr(resp, "raise_for_status"):
                resp.raise_for_status()
            return await resp.json()
        except aiohttp.ClientResponseError as err:
            _LOGGER.debug("set_params HTTP error: %s", err)
            raise RainmakerSetError("Failed to set params") from err
        except aiohttp.ClientError as err:
            _LOGGER.debug("set_params transport error: %s", err)
            raise RainmakerConnectionError("Failed to set params") from err
