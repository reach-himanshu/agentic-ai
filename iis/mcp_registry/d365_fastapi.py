from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from integrations.d365.service import D365Client
import mcp.types as types
import logging

logger = logging.getLogger(__name__)

# FastApiMCP automatically converts FastAPI routes into MCP Tools.
# This fulfills the user's request to see "details of Tools" in standard docs.
sub_app = FastAPI(title="D365 FastApiMCP")
mcp = FastApiMCP(sub_app)

@sub_app.get("/accounts", summary="Get D365 Accounts", description="Fetch top 5 accounts from Dynamics 365")
async def d365_get_accounts() -> str:
    client = D365Client()
    try:
        accounts = await client.get_accounts()
        return f"Successfully retrieved accounts: {accounts}"
    except Exception as e:
        logger.error(f"Error retrieving accounts: {e}")  # Log full error for debugging
        return "Error: Failed to retrieve accounts. Please try again later."

@sub_app.get("/resolve-lookup", summary="Resolve D365 ID", description="Find the ID of a record using fuzzy search")
async def d365_resolve_lookup(entity: str, search_field: str, value: str) -> str:
    client = D365Client()
    try:
        entity_id = await client.resolve_lookup(entity, search_field, value)
        return str(entity_id)
    except Exception as e:
        logger.error(f"Error resolving lookup: {e}")  # Log full error for debugging
        return "Failed to resolve: Record not found or system error."

# Setup the MCP server and mount SSE endpoints
mcp.setup_server()
mcp.mount_sse()

# Since FastApiMCP doesn't have high-level decorators for Prompts/Resources,
# we use the low-level mcp.server to add them.
@mcp.server.list_prompts()
async def handle_list_prompts():
    return [
        types.Prompt(
            name="onboard-client",
            description="Guidance for creating a new D365 client",
            arguments=[types.PromptArgument(name="name", description="Client Name", required=True)]
        )
    ]

@mcp.server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict = None):
    if name == "onboard-client":
        client_name = arguments.get("name", "Unknown") if arguments else "Unknown"
        return types.GetPromptResult(
            description="Onboarding instructions",
            messages=[
                types.SamplingMessage(
                    role="user",
                    content=types.TextContent(type="text", text=f"How do I onboard {client_name} into D365?")
                )
            ]
        )
    raise ValueError(f"Prompt not found: {name}")

@mcp.server.list_resources()
async def handle_list_resources():
    return [
        types.Resource(
            uri="d365://metadata/entities",
            name="D365 Entity Metadata",
            description="Available entities in the CRM"
        )
    ]

@mcp.server.read_resource()
async def handle_read_resource(uri: str):
    if uri == "d365://metadata/entities":
        return types.ReadResourceResult(
            contents=[types.TextResourceContents(uri=uri, text="account, contact, opportunity, product-service")]
        )
    raise ValueError(f"Resource not found: {uri}")
