"""
AutoGen-based Executor Agent with MCP tool bindings.
"""
from typing import Any, Callable
from autogen_core.tools import FunctionTool
from tools.mcp_client import MCPClient


async def create_mcp_tools(mcp_client: MCPClient) -> list[FunctionTool]:
    """Dynamically create AutoGen FunctionTools from all MCP tools in the backend."""
    try:
        raw_tools = await mcp_client.list_tools()
        print(f"[Executor] Fetched {len(raw_tools)} tools from backend.")
        
        tools = []
        for tool_def in raw_tools:
            name = tool_def["name"]
            description = tool_def.get("description", f"Execute {name}")
            parameters = tool_def.get("parameters", {})
            
            print(f"[Executor] Creating tool: {name}")
            
            # Create a closure to capture the specific tool definition
            def make_tool_func(t_name, t_params):
                # Use a specific signature that the agent might prefer, or just dict
                async def dynamic_tool_func(arguments: dict = None) -> str:
                    # Some agents might pass arguments as a dict, others might spread them
                    # If arguments is None, it means they might be in **kwargs if we used that
                    # But if we use 'arguments: dict', we handle the common case
                    actual_args = arguments or {}
                    result = await mcp_client.execute_tool(t_name, actual_args)
                    
                    if "content" in result:
                        content_list = []
                        for item in result["content"]:
                            if item.get("type") == "text":
                                content_list.append(item.get("text", ""))
                        return "\n".join(content_list) if content_list else str(result)
                    
                    return str(result)
                return dynamic_tool_func

            # If we could, we would pass the schema to FunctionTool here
            # But autogen-core FunctionTool usually derives it from type hints and docstrings
            tools.append(
                FunctionTool(
                    make_tool_func(name, parameters),
                    name=name,
                    description=description
                )
            )
        
        return tools
    except Exception as e:
        print(f"[Executor] Failed to dynamically create tools: {e}")
        return []


class ExecutorAgent:
    """
    Executor agent that manages MCP tools for AutoGen agents.
    """
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        self.tools: list[FunctionTool] = []

    async def initialize_tools(self):
        """Asynchronously initialize tools from the backend."""
        self.tools = await create_mcp_tools(self.mcp_client)
    
    def get_tools(self) -> list[FunctionTool]:
        """Get the list of AutoGen FunctionTools."""
        return self.tools
