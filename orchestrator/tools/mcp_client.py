"""
MCP Client for communicating with the backend API.
"""
import httpx
from typing import Any

from config import config


class MCPClient:
    """HTTP client for backend MCP API."""
    
    def __init__(self, base_url: str = None, auth_token: str = None, auth_flow: str = "CLIENT_CREDENTIALS"):
        self.base_url = base_url or config.backend_url
        self.auth_token = auth_token
        self.auth_flow = auth_flow
        self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            # Add OpsIQ Auth Flow header
            headers["X-OpsIQ-Auth-Flow"] = self.auth_flow
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def set_auth_info(self, token: str, flow: str = "CLIENT_CREDENTIALS"):
        """Update auth token and flow preference (recreates client)."""
        self.auth_token = token
        self.auth_flow = flow
        self._client = None  # Force recreation
    
    async def list_tools(self) -> list[dict]:
        """Get available MCP tools from backend."""
        response = await self.client.get("/api/v1/mcp/tools")
        response.raise_for_status()
        return response.json().get("tools", [])
    
    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict:
        """Execute an MCP tool."""
        response = await self.client.post(
            "/api/v1/mcp/execute",
            json={"tool_name": tool_name, "arguments": arguments},
        )
        response.raise_for_status()
        return response.json()
    
    async def lookup_client(self, client_id: str = None, name: str = None) -> dict:
        """Lookup a client by ID or name."""
        params = {}
        if client_id:
            # Direct API call
            response = await self.client.get(f"/api/v1/clients/{client_id}")
        elif name:
            response = await self.client.get(f"/api/v1/clients/{name}")
        else:
            return {"found": False, "message": "No client ID or name provided"}
        
        response.raise_for_status()
        return response.json()
    
    async def update_stage(self, client_id: str, new_stage: str, notes: str = None) -> dict:
        """Update client stage."""
        return await self.execute_tool("update_stage", {
            "client_id": client_id,
            "new_stage": new_stage,
            "notes": notes,
        })
    
    async def assign_owner(
        self, client_id: str, new_owner_id: str, new_owner_name: str, notes: str = None
    ) -> dict:
        """Assign new owner to client."""
        return await self.execute_tool("assign_owner", {
            "client_id": client_id,
            "new_owner_id": new_owner_id,
            "new_owner_name": new_owner_name,
            "notes": notes,
        })
