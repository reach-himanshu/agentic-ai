"""
Client API endpoints.
"""
from fastapi import APIRouter, HTTPException, status

from app.middleware.auth import CurrentUser, AdminUser, SalesUser
from app.schemas.client import (
    Client,
    ClientStage,
    ClientLookupResponse,
    StageUpdateRequest,
    StageUpdateResponse,
    OwnerAssignRequest,
    OwnerAssignResponse,
    VALID_STAGE_TRANSITIONS,
)
from app.services.mock_data import (
    get_client_by_id,
    get_client_by_name,
    update_client,
    MOCK_TEAM_MEMBERS,
)

router = APIRouter()


@router.get("/clients/{client_id}", response_model=ClientLookupResponse)
async def get_client(
    client_id: str,
    user: CurrentUser,
):
    """
    Lookup a client by ID.
    Requires authentication.
    """
    client = get_client_by_id(client_id)
    
    if client is None:
        # Try searching by name
        client = get_client_by_name(client_id)
    
    if client is None:
        return ClientLookupResponse(
            found=False,
            message=f"Client '{client_id}' not found",
        )
    
    return ClientLookupResponse(
        found=True,
        client=client,
        message=f"Found client: {client.name}",
    )


@router.patch("/clients/{client_id}/stage", response_model=StageUpdateResponse)
async def update_client_stage(
    client_id: str,
    request: StageUpdateRequest,
    user: SalesUser,  # Requires Admin or Sales role
):
    """
    Update client pipeline stage.
    Requires Sales or Admin role.
    Validates stage transition against state machine.
    """
    client = get_client_by_id(client_id)
    
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' not found",
        )
    
    # Validate stage transition
    allowed_transitions = VALID_STAGE_TRANSITIONS.get(client.stage, [])
    if request.new_stage not in allowed_transitions:
        return StageUpdateResponse(
            success=False,
            previous_stage=client.stage,
            message=f"Invalid stage transition from '{client.stage.value}' to '{request.new_stage.value}'. "
                    f"Allowed: {[s.value for s in allowed_transitions]}",
        )
    
    # Update the client
    previous_stage = client.stage
    updated_client = update_client(client_id, {
        "stage": request.new_stage,
        "notes": request.notes or client.notes,
    })
    
    return StageUpdateResponse(
        success=True,
        previous_stage=previous_stage,
        new_stage=request.new_stage,
        message=f"Successfully updated {client.name} from '{previous_stage.value}' to '{request.new_stage.value}'",
    )


@router.put("/clients/{client_id}/owner", response_model=OwnerAssignResponse)
async def assign_client_owner(
    client_id: str,
    request: OwnerAssignRequest,
    user: AdminUser,  # Requires Admin role only
):
    """
    Reassign client to a new owner.
    Requires Admin role.
    """
    client = get_client_by_id(client_id)
    
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client '{client_id}' not found",
        )
    
    # Validate new owner exists
    if request.new_owner_id not in MOCK_TEAM_MEMBERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Team member '{request.new_owner_id}' not found",
        )
    
    previous_owner = client.owner_name
    updated_client = update_client(client_id, {
        "owner_id": request.new_owner_id,
        "owner_name": request.new_owner_name,
        "notes": request.notes or client.notes,
    })
    
    return OwnerAssignResponse(
        success=True,
        previous_owner=previous_owner,
        new_owner=request.new_owner_name,
        message=f"Successfully reassigned {client.name} from {previous_owner} to {request.new_owner_name}",
    )


@router.get("/clients", response_model=list[Client])
async def list_clients(user: CurrentUser):
    """
    List all clients.
    Requires authentication.
    """
    from app.services.mock_data import MOCK_CLIENTS
    return list(MOCK_CLIENTS.values())


@router.get("/team-members")
async def list_team_members(user: AdminUser):
    """
    List available team members for owner assignment.
    Requires Admin role.
    """
    return [
        {"id": uid, "name": name}
        for uid, name in MOCK_TEAM_MEMBERS.items()
    ]
