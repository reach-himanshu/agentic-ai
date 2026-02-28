"""
MCP (Model Context Protocol) router for tool execution.
"""
from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status

from app.middleware.auth import CurrentUser
from app.tools.lookup_client import lookup_client_tool
from app.tools.update_stage import update_stage_tool
from app.tools.assign_owner import assign_owner_tool
from app.services.mcp_manager import mcp_manager

router = APIRouter()


class MCPToolRequest(BaseModel):
    """Request to execute an MCP tool."""
    tool_name: str
    arguments: dict[str, Any]


class MCPToolResponse(BaseModel):
    """Response from MCP tool execution."""
    success: bool
    tool_name: str
    result: dict[str, Any] | None = None
    error: str | None = None


# Registry of available LOCAL MCP tools
LOCAL_MCP_TOOLS = {
    "lookup_client": lookup_client_tool,
    "update_stage": update_stage_tool,
    "assign_owner": assign_owner_tool,
}


# Role-based tool permissions mapping
# Key: tool_name, Value: list of required roles (empty means any authenticated user)
TOOL_PERMISSIONS = {
    "assign_owner": ["APP_ROLE_ADMIN"],
    "update_stage": ["APP_ROLE_ADMIN", "APP_ROLE_SALES"],
    "lookup_client": [], # Any user
    
    # D365 Tools
    "d365_get_accounts": [], # Any user
    "d365_resolve_lookup": [], # Any user
    "d365_create_account": ["APP_ROLE_ADMIN"],
    "d365_create_opportunity": ["APP_ROLE_ADMIN"],
    "d365_deep_insert": ["APP_ROLE_ADMIN"],
}


@router.get("/tools")
async def list_tools(user: CurrentUser):
    """
    List available MCP tools filtered by user roles.
    """
    all_local_tools = [
        {
            "name": "lookup_client",
            "description": "Look up client information by ID or name",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string", "description": "Client ID"},
                    "name": {"type": "string", "description": "Client name (partial match)"},
                },
            },
        },
        {
            "name": "update_stage",
            "description": "Update client pipeline stage",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string", "description": "Client ID"},
                    "new_stage": {
                        "type": "string",
                        "enum": ["prospect", "qualified", "negotiation", "closed_won", "closed_lost"],
                        "description": "New pipeline stage",
                    },
                    "notes": {"type": "string", "description": "Optional notes"},
                },
                "required": ["client_id", "new_stage"],
            },
        },
        {
            "name": "assign_owner",
            "description": "Reassign client to a new owner (Admin only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {"type": "string", "description": "Client ID"},
                    "new_owner_id": {"type": "string", "description": "New owner's user ID"},
                    "new_owner_name": {"type": "string", "description": "New owner's name"},
                    "notes": {"type": "string", "description": "Optional notes"},
                },
                "required": ["client_id", "new_owner_id", "new_owner_name"],
            },
        },
    ]
    
    # Helper to check if tool is allowed for user
    def is_allowed(tool_name: str) -> bool:
        required = TOOL_PERMISSIONS.get(tool_name, [])
        if not required:
            return True
        return bool(set(user.roles).intersection(set(required)))

    # Filter local tools
    local_tools = [t for t in all_local_tools if is_allowed(t["name"])]
    
    # Fetch and filter external tools
    external_tools = await mcp_manager.list_tools()
    external_tools = [t for t in external_tools if is_allowed(t["name"])]
    
    return {
        "tools": local_tools + external_tools
    }


@router.post("/execute", response_model=MCPToolResponse)
async def execute_tool(
    request: MCPToolRequest,
    user: CurrentUser,
):
    """
    Execute an MCP tool by name after verifying role-based permissions.
    """
    # Verify permissions
    required_roles = TOOL_PERMISSIONS.get(request.tool_name, [])
    if required_roles and not set(user.roles).intersection(set(required_roles)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to execute '{request.tool_name}'. Required: {required_roles}",
        )

    # Check Local Tools First
    if request.tool_name in LOCAL_MCP_TOOLS:
        tool_fn = LOCAL_MCP_TOOLS[request.tool_name]
        try:
            result = await tool_fn(user=user, **request.arguments)
            return MCPToolResponse(
                success=True,
                tool_name=request.tool_name,
                result=result,
            )
        except HTTPException:
            raise # Re-raise auth/role errors from tool implementation
        except Exception as e:
            return MCPToolResponse(
                success=False,
                tool_name=request.tool_name,
                error=str(e),
            )
    
    # Fallback to External MCP Server
    try:
        result = await mcp_manager.execute_tool(request.tool_name, request.arguments)
        return MCPToolResponse(
            success=True,
            tool_name=request.tool_name,
            result=result,
        )
    except Exception as e:
        return MCPToolResponse(
            success=False,
            tool_name=request.tool_name,
            error=f"External tool execution failed: {str(e)}",
        )

