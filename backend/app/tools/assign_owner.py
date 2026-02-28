"""
MCP Tool: assign_owner
Reassign client to a new owner (Admin only).
"""
from fastapi import HTTPException, status

from app.middleware.auth import TokenData
from app.services.mock_data import get_client_by_id, update_client, MOCK_TEAM_MEMBERS


async def assign_owner_tool(
    user: TokenData,
    client_id: str,
    new_owner_id: str,
    new_owner_name: str,
    notes: str | None = None,
) -> dict:
    """
    Reassign client to a new owner.
    
    Args:
        user: Authenticated user (must have Admin role)
        client_id: Client ID to update
        new_owner_id: New owner's user ID
        new_owner_name: New owner's name
        notes: Optional notes
    
    Returns:
        dict with assignment result
    """
    # Check Admin permissions
    if "APP_ROLE_ADMIN" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Requires Admin role.",
        )
    
    # Get client
    client = get_client_by_id(client_id)
    if client is None:
        return {
            "success": False,
            "message": f"Client '{client_id}' not found",
        }
    
    # Validate new owner exists
    if new_owner_id not in MOCK_TEAM_MEMBERS:
        return {
            "success": False,
            "message": f"Team member '{new_owner_id}' not found. Available: {list(MOCK_TEAM_MEMBERS.keys())}",
        }
    
    previous_owner = client.owner_name
    
    # Update
    updated = update_client(client_id, {
        "owner_id": new_owner_id,
        "owner_name": new_owner_name,
        "notes": notes or client.notes,
    })
    
    return {
        "success": True,
        "client_id": client_id,
        "client_name": client.name,
        "previous_owner": previous_owner,
        "new_owner": new_owner_name,
        "message": f"Successfully reassigned {client.name} from {previous_owner} to {new_owner_name}",
    }
