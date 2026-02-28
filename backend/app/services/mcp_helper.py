import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from app.config import get_settings

settings = get_settings()

async def get_external_tools():
    """
    Fetch tools from all configured external MCP servers.
    """
    urls = [settings.d365_mcp_url, settings.workday_mcp_url]
    all_tools = []
    
    for url in urls:
        if not url: continue
        print(f"[MCP_HELPER] Fetching tools from: {url}")
        try:
            async with sse_client(url=url) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=5.0)
                    response = await asyncio.wait_for(session.list_tools(), timeout=5.0)
                    
                    for tool in response.tools:
                        all_tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                            "is_external": True,
                            "mcp_url": url  # Tag tool with its source
                        })
        except Exception as e:
            print(f"[MCP_HELPER] Error fetching from {url}: {e}")
            
    return all_tools

async def call_external_tool(tool_name: str, arguments: dict):
    """
    Execute a tool on the external MCP server that owns it.
    """
    # For now, we try both servers if we don't know who owns it.
    # In a more advanced version, we'd cache which tool belongs to which URL.
    urls = [settings.d365_mcp_url, settings.workday_mcp_url]
    
    last_error = None
    for url in urls:
        if not url: continue
        try:
            async with sse_client(url=url) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=5.0)
                    # Check if tool exists on this server first
                    tools_resp = await asyncio.wait_for(session.list_tools(), timeout=5.0)
                    if any(t.name == tool_name for t in tools_resp.tools):
                        print(f"[MCP_HELPER] Calling {tool_name} on {url}")
                        result = await asyncio.wait_for(session.call_tool(tool_name, arguments), timeout=30.0)
                        return {
                            "content": [c.model_dump() for c in result.content],
                            "is_external": True
                        }
        except Exception as e:
            last_error = e
            print(f"[MCP_HELPER] Tool {tool_name} not found or error on {url}: {e}")
            continue
            
    raise last_error or Exception(f"Tool {tool_name} not found on any MCP server")

