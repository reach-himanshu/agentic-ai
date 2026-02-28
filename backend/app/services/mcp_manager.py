import asyncio
from typing import List, Dict, Any
from app.services.mcp_helper import get_external_tools, call_external_tool

class MCPManager:
    """
    Manager for external MCP server connections.
    Uses mcp_helper for reliable protocol handling.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPManager, cls).__new__(cls)
        return cls._instance

    async def connect(self):
        """No-op for this implementation as connection happens via helper."""
        pass

    async def disconnect(self):
        """No-op for this implementation."""
        pass

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Fetch available tools from the external MCP server via helper.
        """
        print("[MCP] list_tools: Fetching from helper...")
        return await get_external_tools()

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool on the external MCP server via helper.
        """
        print(f"[MCP] execute_tool: {tool_name} via helper...")
        return await call_external_tool(tool_name, arguments)

# Global instance
mcp_manager = MCPManager()
