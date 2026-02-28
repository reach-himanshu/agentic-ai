"""
MCP Tool: update_stage
Update client pipeline stage with validation.
"""
from fastapi import HTTPException, status

from app.middleware.auth import TokenData
from app.schemas.client import ClientStage, VALID_STAGE_TRANSITIONS
from app.services.mock_data import get_client_by_id, update_client


async def update_stage_tool(
    user: TokenData,
    client_id: str,
    new_stage: str,
    notes: str | None = None,
) -> dict:
    """
    Update client pipeline stage.
    
    Args:
        user: Authenticated user (must have Sales or Admin role)
        client_id: Client ID to update
        new_stage: New stage value
        notes: Optional notes
    
    Returns:
        dict with update result
    """
    # Check permissions
    allowed_roles = {"APP_ROLE_ADMIN", "APP_ROLE_SALES"}
    if not set(user.roles).intersection(allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Requires Sales or Admin role.",
        )
    
    # Get client
    client = get_client_by_id(client_id)
    if client is None:
        return {
            "success": False,
            "message": f"Client '{client_id}' not found",
        }
    
    # Parse and validate new stage
    try:
        target_stage = ClientStage(new_stage.lower())
    except ValueError:
        return {
            "success": False,
            "message": f"Invalid stage '{new_stage}'. Valid stages: {[s.value for s in ClientStage]}",
        }
    
    # Validate transition
    allowed_transitions = VALID_STAGE_TRANSITIONS.get(client.stage, [])
    if target_stage not in allowed_transitions:
        return {
            "success": False,
            "previous_stage": client.stage.value,
            "message": f"Invalid transition from '{client.stage.value}' to '{target_stage.value}'. "
                       f"Allowed: {[s.value for s in allowed_transitions]}",
        }
    
    # Update
    previous_stage = client.stage
    updated = update_client(client_id, {
        "stage": target_stage,
        "notes": notes or client.notes,
    })
    
    return {
        "success": True,
        "client_id": client_id,
        "client_name": client.name,
        "previous_stage": previous_stage.value,
        "new_stage": target_stage.value,
        "message": f"Successfully updated {client.name} from '{previous_stage.value}' to '{target_stage.value}'",
    }
