import httpx
import websockets
from typing import Optional, Any
from .base_auth import BaseAuth

class BaseHttpClient:
    def __init__(self, base_url: str, auth: Optional[BaseAuth] = None, verify: bool = True):
        self.base_url = base_url
        self.auth = auth
        self.client = httpx.AsyncClient(base_url=base_url, verify=verify, timeout=60.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.auth:
            headers = await self.auth.authenticate_request(headers)
        return headers

    async def get(self, endpoint: str, params: Optional[dict] = None, **kwargs) -> Any:
        headers = await self._get_headers()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        response = await self.client.get(endpoint, params=params, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    async def post(self, endpoint: str, json: Optional[dict] = None, **kwargs) -> Any:
        headers = await self._get_headers()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        response = await self.client.post(endpoint, json=json, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    async def patch(self, endpoint: str, json: Optional[dict] = None, **kwargs) -> Any:
        headers = await self._get_headers()
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        response = await self.client.patch(endpoint, json=json, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()

class BaseWebSocketClient:
    def __init__(self, uri: str, auth: Optional[BaseAuth] = None):
        self.uri = uri
        self.auth = auth

    async def connect(self):
        headers = {}
        if self.auth:
            headers = await self.auth.authenticate_request(headers)
        # Note: websockets.connect extra_headers expects a dict or list of tuples
        return websockets.connect(self.uri, extra_headers=headers)
