"""
AutoGen-based Executor Agent with Local MCP tool bindings for IIS.
Collapses the network hop by calling BOML tools directly.
"""
from typing import Any, Callable, Optional
from autogen_core.tools import FunctionTool, BaseTool, ToolSchema
from pydantic import BaseModel
import httpx
from urllib.parse import quote
from traceloop.sdk.decorators import task
import asyncio
import logging

logger = logging.getLogger(__name__)

# Import local MCP servers
try:
    from mcp_registry.d365 import mcp as d365_mcp
    from mcp_registry.workday import mcp as workday_mcp
    from mcp_registry.servicenow import mcp as servicenow_mcp
    from mcp_registry.msgraph import mcp as msgraph_mcp
    from mcp_registry.knowledge_hub import mcp as knowledge_hub_mcp
    from mcp_registry.time_entry import mcp as time_entry_mcp
except ImportError as e:
    print(f"[Executor] Warning: Could not import local MCP modules: {e}")
    d365_mcp = None
    workday_mcp = None
    servicenow_mcp = None
    msgraph_mcp = None
    knowledge_hub_mcp = None
    time_entry_mcp = None

# TOOL EXPOSURE CONTROL: Add tool names here to restrict what the Agent can see. 
# If empty, all tools from registered MCP servers are exposed.
EXPOSED_TOOLS = [] # Example: ["d365_search_accounts", "search_kb"]

# MCPArgs moved to module level for Pydantic 2.x compatibility
# (Pydantic cannot properly validate classes defined inside functions)
class MCPArgs(BaseModel):
    """Dynamic argument container for MCP tool calls."""
    model_config = {"extra": "allow"}

@task(name="initialize_mcp_tools")
async def create_local_mcp_tools() -> list[FunctionTool]:
    """Dynamically create AutoGen FunctionTools from local FastMCP instances."""

    class MCPTool(BaseTool[MCPArgs, str]):
        def __init__(self, instance, name: str, description: str, input_schema: dict):
            super().__init__(args_type=MCPArgs, return_type=str, name=name, description=description)
            self.instance = instance
            self.mcp_name = name
            self.input_schema = input_schema

        @property
        def schema(self) -> ToolSchema:
            return ToolSchema(
                name=self.name,
                description=self.description,
                parameters=self.input_schema
            )

        async def run(self, args: MCPArgs, cancellation_token: Any) -> str:
            # MCP call_tool expects a dict of arguments
            # args.model_dump() gives us the data passed by the LLM
            try:
                result = await self.instance.call_tool(self.mcp_name, args.model_dump())
                
                # Convert MCP result to string for AutoGen
                if hasattr(result, 'content'):
                    content_list = []
                    for item in result.content:
                        if hasattr(item, 'text'):
                            content_list.append(item.text)
                    return "\n".join(content_list) if content_list else str(result)
                
                return str(result)
            except Exception as e:
                logger.error(f"[Executor] MCP Tool {self.mcp_name} execution error: {e}")
                return f"Error executing tool: {str(e)}"

    all_fastmcp_instances = []
    if d365_mcp: all_fastmcp_instances.append(d365_mcp)
    if workday_mcp: all_fastmcp_instances.append(workday_mcp)
    if servicenow_mcp: all_fastmcp_instances.append(servicenow_mcp)
    if msgraph_mcp: all_fastmcp_instances.append(msgraph_mcp)
    if knowledge_hub_mcp: all_fastmcp_instances.append(knowledge_hub_mcp)
    if time_entry_mcp: all_fastmcp_instances.append(time_entry_mcp)
    
    tools = []
    
    for mcp_instance in all_fastmcp_instances:
        mcp_tools = await mcp_instance.list_tools()
        print(f"[Executor] Found {len(mcp_tools)} tools in {mcp_instance.name}")
        
        for mcp_tool in mcp_tools:
            name = mcp_tool.name
            
            # Exposure Filter
            if EXPOSED_TOOLS and name not in EXPOSED_TOOLS:
                continue
                
            description = mcp_tool.description or f"Execute {name}"
            
            tools.append(
                MCPTool(
                    instance=mcp_instance,
                    name=name,
                    description=description,
                    input_schema=mcp_tool.inputSchema
                )
            )
            
    async def d365_get_environments() -> str:
        """List all available Dynamics 365 environments for the logged-in user."""
        from integrations.d365.discovery import D365DiscoveryService
        import json
        disco = D365DiscoveryService()
        instances = await disco.get_instances()
        if not instances:
            return "No Dynamics 365 environments found for your account."
        
        # Format for LLM
        output = ["Available D365 Environments:"]
        for inst in instances:
            name = inst.get("FriendlyName") or inst.get("UniqueName")
            url = inst.get("ApiUrl")
            tenant = inst.get("TenantId")
            output.append(f"- {name}: {url} (Tenant: {tenant})")
        
        return "\n".join(output)

    tools.append(FunctionTool(d365_get_environments, name="d365_get_environments", description="Find and list all Dynamics 365 instances/environments you have access to."))

    return tools

class ExecutorAgent:
    """
    Executor agent that manages LOCAL MCP tools for IIS.
    """
    
    def __init__(self, mcp_client=None):
        # mcp_client is kept for backward compatibility in constructor signatures
        # but is no longer used for core tool execution in IIS.
        self.tools: list[FunctionTool] = []
        self.auth_token: str | None = None

    def set_auth_token(self, token: str):
        """Update the auth token for tool execution context."""
        self.auth_token = token

    async def initialize_tools(self):
        """Asynchronously initialize tools from local BOML."""
        self.tools = await create_local_mcp_tools()
    
    @task(name="execute_mcp_tool")
    async def execute_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool directly by name from local MCP servers."""
        from opentelemetry import trace
        span = trace.get_current_span()
        if span:
            span.set_attribute("tool.name", name)
            span.set_attribute("tool.arguments", str(arguments))

        all_fastmcp_instances = []
        if d365_mcp: all_fastmcp_instances.append(d365_mcp)
        if workday_mcp: all_fastmcp_instances.append(workday_mcp)
        if servicenow_mcp: all_fastmcp_instances.append(servicenow_mcp)
        if msgraph_mcp: all_fastmcp_instances.append(msgraph_mcp)
        if knowledge_hub_mcp: all_fastmcp_instances.append(knowledge_hub_mcp)
        if time_entry_mcp: all_fastmcp_instances.append(time_entry_mcp)

        for mcp_instance in all_fastmcp_instances:
            mcp_tools = await mcp_instance.list_tools()
            for t in mcp_tools:
                if t.name == name:
                    print(f"[Executor] Executing local tool: {name}")
                    result = await mcp_instance.call_tool(name, arguments)
                    
                    # Wrap in MCP-like structure for backward compatibility with Planner
                    content = []
                    if hasattr(result, 'content'):
                        for item in result.content:
                            if hasattr(item, 'text'):
                                content.append({"type": "text", "text": item.text})
                    
                    return {"content": content} if content else {"content": [{"type": "text", "text": str(result)}]}
        
        # Try alias resolution if exact match not found
        tool_aliases = {
            "servicenow_create_incident": "snow_create_incident",
            "servicenow_search_incidents": "snow_search_incidents",
            "servicenow_update_incident": "snow_update_incident",
            "servicenow_list_approvals": "snow_list_approvals",
            "servicenow_approve_request": "snow_approve_request",
            "servicenow_search_knowledge": "snow_search_knowledge",
            "create_incident": "snow_create_incident",
            "search_incidents": "snow_search_incidents",
        }
        if name in tool_aliases:
            aliased_name = tool_aliases[name]
            print(f"[Executor] Alias resolution: {name} -> {aliased_name}")
            return await self.execute_tool(aliased_name, arguments)
                    
        raise ValueError(f"Tool {name} not found in local MCP servers.")

    def get_tools(self) -> list[FunctionTool]:
        """Get the list of AutoGen FunctionTools."""
        return self.tools
