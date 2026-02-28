"""
Mock data store for clients.
In production, this would be replaced with actual database or API calls.
"""
from datetime import datetime, timedelta
from app.schemas.client import Client, ClientStage


# Mock clients database
MOCK_CLIENTS: dict[str, Client] = {
    "acme-corp": Client(
        id="acme-corp",
        name="Acme Corporation",
        stage=ClientStage.PROSPECT,
        owner_id="user-001",
        owner_name="John Smith",
        email="contact@acme.com",
        phone="+1-555-0100",
        company_size="50-200",
        industry="Technology",
        last_activity=datetime.now() - timedelta(days=2),
        notes="High potential enterprise client",
    ),
    "global-tech": Client(
        id="global-tech",
        name="Global Tech Industries",
        stage=ClientStage.QUALIFIED,
        owner_id="user-002",
        owner_name="Sarah Wilson",
        email="sales@globaltech.io",
        phone="+1-555-0200",
        company_size="200-500",
        industry="Manufacturing",
        last_activity=datetime.now() - timedelta(hours=6),
        notes="Interested in enterprise package",
    ),
    "startup-xyz": Client(
        id="startup-xyz",
        name="Startup XYZ",
        stage=ClientStage.NEGOTIATION,
        owner_id="user-001",
        owner_name="John Smith",
        email="founders@startupxyz.co",
        phone="+1-555-0300",
        company_size="10-50",
        industry="Fintech",
        last_activity=datetime.now() - timedelta(days=1),
        notes="Price sensitive, wants startup discount",
    ),
}


# Mock team members for owner assignment
MOCK_TEAM_MEMBERS = {
    "user-001": "John Smith",
    "user-002": "Sarah Wilson",
    "user-003": "Mike Johnson",
    "user-004": "Emily Chen",
    "user-005": "David Brown",
}


def get_client_by_id(client_id: str) -> Client | None:
    """Get client by ID."""
    return MOCK_CLIENTS.get(client_id)


def get_client_by_name(name: str) -> Client | None:
    """Search client by name (case-insensitive partial match)."""
    name_lower = name.lower()
    for client in MOCK_CLIENTS.values():
        if name_lower in client.name.lower():
            return client
    return None


def update_client(client_id: str, updates: dict) -> Client | None:
    """Update client data."""
    if client_id not in MOCK_CLIENTS:
        return None
    
    client = MOCK_CLIENTS[client_id]
    client_data = client.model_dump()
    client_data.update(updates)
    client_data["last_activity"] = datetime.now()
    
    updated_client = Client(**client_data)
    MOCK_CLIENTS[client_id] = updated_client
    return updated_client
