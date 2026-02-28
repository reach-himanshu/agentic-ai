"""
Client data models and schemas.
"""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ClientStage(str, Enum):
    """Pipeline stages for clients."""
    PROSPECT = "prospect"
    QUALIFIED = "qualified"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


# Valid stage transitions (state machine)
VALID_STAGE_TRANSITIONS = {
    ClientStage.PROSPECT: [ClientStage.QUALIFIED, ClientStage.CLOSED_LOST],
    ClientStage.QUALIFIED: [ClientStage.NEGOTIATION, ClientStage.CLOSED_LOST],
    ClientStage.NEGOTIATION: [ClientStage.CLOSED_WON, ClientStage.CLOSED_LOST],
    ClientStage.CLOSED_WON: [],
    ClientStage.CLOSED_LOST: [],
}


class Client(BaseModel):
    """Client model."""
    id: str
    name: str
    stage: ClientStage
    owner_id: str
    owner_name: str
    email: str | None = None
    phone: str | None = None
    company_size: str | None = None
    industry: str | None = None
    last_activity: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    notes: str | None = None


class ClientLookupRequest(BaseModel):
    """Request to lookup a client."""
    client_id: str | None = None
    name: str | None = None


class ClientLookupResponse(BaseModel):
    """Response from client lookup."""
    found: bool
    client: Client | None = None
    message: str | None = None


class StageUpdateRequest(BaseModel):
    """Request to update client stage."""
    new_stage: ClientStage
    notes: str | None = None


class StageUpdateResponse(BaseModel):
    """Response from stage update."""
    success: bool
    previous_stage: ClientStage | None = None
    new_stage: ClientStage | None = None
    message: str


class OwnerAssignRequest(BaseModel):
    """Request to assign new owner."""
    new_owner_id: str
    new_owner_name: str
    notes: str | None = None


class OwnerAssignResponse(BaseModel):
    """Response from owner assignment."""
    success: bool
    previous_owner: str | None = None
    new_owner: str | None = None
    message: str
