import httpx
from fastapi import Request
from typing import Optional, Dict, Any
from app.core.security_azure import get_service_token

class BaseService:
    """
    Base class for services connecting to external APIs.
    Handles token acquisition and common request logic.
    """
    
    def __init__(self, resource_url: str):
        self.resource_url = resource_url
        self.scope = f"{resource_url}/.default"

    async def get_authenticated_client(self, request: Request, user_assertion: str) -> httpx.AsyncClient:
        """
        Creates an httpx client with the appropriate bearer token.
        """
        token = get_service_token(request, user_assertion, self.scope)
        if not token:
            raise Exception(f"Failed to acquire token for scope: {self.scope}")
            
        return httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}"},
            base_url=self.resource_url,
            verify=False # Disabled for dev/troubleshooting
        )

    async def request(
        self, 
        request: Request, 
        user_assertion: str, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Makes an authenticated request to the external API.
        """
        async with await self.get_authenticated_client(request, user_assertion) as client:
            response = await client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
