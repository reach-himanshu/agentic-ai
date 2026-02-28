"""
MCP Tool: lookup_client
Look up client information by ID or name.
"""
from app.middleware.auth import TokenData
from app.services.mock_data import get_client_by_id, get_client_by_name


async def lookup_client_tool(
    user: TokenData,
    client_id: str | None = None,
    name: str | None = None,
) -> dict:
    """
    Look up a client by ID or name.
    
    Args:
        user: Authenticated user
        client_id: Client ID to look up
        name: Client name to search (partial match)
    
    Returns:
        dict with client data or error message
    """
    client = None
    
    if client_id:
        client = get_client_by_id(client_id)
    
    if client is None and name:
        client = get_client_by_name(name)
    
    if client is None:
        return {
            "found": False,
            "message": f"Client not found. Searched for: {client_id or name}",
        }
    
    return {
        "found": True,
        "client": client.model_dump(mode='json'),
        "message": f"Found client: {client.name}",
    }
