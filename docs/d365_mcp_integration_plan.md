# D365 MCP Server Integration Plan

Integrate an external D365 MCP server running at `http://127.0.0.1:8006/mcp/d365/sse` into the existing FastAPI backend to allow the AI agents to interact with Dynamics 365 data.

## User Review Required

> [!IMPORTANT]
> This integration requires the `mcp[sse]` package. I will install this in the backend's virtual environment.
> Please ensure the D365 MCP server is running at the specified URL before testing.

## Proposed Changes

### Backend

#### [MODIFY] [pyproject.toml](file:///c:/Users/himanshu.nigam/..gemini/antigravity/scratch/agent-ui/backend/pyproject.toml)
- Add `mcp[sse]` to dependencies.

#### [MODIFY] [app/config.py](file:///c:/Users/himanshu.nigam/..gemini/antigravity/scratch/agent-ui/backend/app/config.py)
- Add `d365_mcp_url` setting.

#### [NEW] [mcp_manager.py](file:///c:/Users/himanshu.nigam/..gemini/antigravity/scratch/agent-ui/backend/app/services/mcp_manager.py)
- Implement a singleton manager that maintains an SSE session with the D365 server.
- Methods to `get_tools()` and `call_tool()`.

#### [MODIFY] [app/routers/mcp.py](file:///c:/Users/himanshu.nigam/..gemini/antigravity/scratch/agent-ui/backend/app/routers/mcp.py)
- Integrate `MCPManager` to merge external tools into the `/tools` endpoint.
- Proxy tool execution to the external server if the tool is not found locally.

## Verification Plan

### Automated Tests
- Component test to verify that calling `/api/v1/mcp/tools` returns both local and external tools.

### Manual Verification
- Start the D365 MCP server.
- Use the Chat UI to ask about Dynamics 365 data (e.g., "List accounts from D365").
- Verify the orchestrator uses the new tools.
