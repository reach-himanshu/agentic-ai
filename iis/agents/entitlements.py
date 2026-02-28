"""
Role-to-Agent entitlements mapping.

Uses Azure App Roles from JWT token to determine which agents a user can access.
"""
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# Azure App Roles → Agent IDs mapping
ROLE_TO_AGENTS = {
    "OpsIQ.SalesAgent": ["sales"],
    "OpsIQ.OnboardingAgent": ["onboarding"],
    "OpsIQ.ITAgent": ["it_support"],
    "OpsIQ.HRAgent": ["hr"],
    "OpsIQ.PricingAgent": ["pricing_assistant"],
}

# Agent metadata for UI display
AGENT_CATALOG = {
    "sales": {
        "id": "sales",
        "name": "Sales Agent",
        "icon": "🏢",
        "description": "Dynamics 365 CRM + CPQ operations",
        "systems": ["D365", "CPQ"],
    },
    "onboarding": {
        "id": "onboarding",
        "name": "Client Onboarding Agent",
        "icon": "🤝",
        "description": "Client onboarding with D365 + Workday",
        "systems": ["D365", "Workday"],
    },
    "it_support": {
        "id": "it_support",
        "name": "IT Support Agent",
        "icon": "🛠️",
        "description": "ServiceNow ticketing and IT help",
        "systems": ["ServiceNow"],
    },
    "hr": {
        "id": "hr",
        "name": "HR Agent",
        "icon": "👥",
        "description": "Workday HR self-service",
        "systems": ["Workday"],
    },
    "pricing_assistant": {
        "id": "pricing_assistant",
        "name": "Pricing Assistant",
        "icon": "💰",
        "description": "Guided pricing & scoping intake with ML recommendations",
        "systems": ["D365", "Pricing Engine"],
    },
}

# Alias for simpler access in planner
AGENT_METADATA = AGENT_CATALOG

# Base role required to access the app
BASE_ROLE = "OpsIQ.User"


def get_available_agents(jwt_roles: list[str]) -> list[str]:
    """
    Get list of agent IDs the user can access based on their JWT roles.
    
    Args:
        jwt_roles: List of role claims from the JWT token
        
    Returns:
        List of agent IDs (e.g., ["sales", "it_support", "hr"])
    """
    agents = set()
    for role in jwt_roles:
        if role in ROLE_TO_AGENTS:
            agents.update(ROLE_TO_AGENTS[role])
    
    return list(agents)


def has_app_access(jwt_roles: list[str]) -> bool:
    """
    Check if user has base access to the app.
    
    Args:
        jwt_roles: List of role claims from the JWT token
        
    Returns:
        True if user has OpsIQ.User role
    """
    return BASE_ROLE in jwt_roles


def get_agent_catalog(jwt_roles: list[str]) -> dict:
    """
    Get the agent catalog filtered by user entitlements.
    
    Returns:
        Dict with 'available' and 'locked' agent lists
    """
    available_ids = get_available_agents(jwt_roles)
    
    available = []
    locked = []
    
    for agent_id, metadata in AGENT_CATALOG.items():
        if agent_id in available_ids:
            available.append(metadata)
        else:
            locked.append({
                **metadata,
                "reason": f"Requires {_get_required_role(agent_id)} role"
            })
    
    return {
        "available": available,
        "locked": locked,
    }


def _get_required_role(agent_id: str) -> Optional[str]:
    """Get the required role for an agent."""
    for role, agents in ROLE_TO_AGENTS.items():
        if agent_id in agents:
            return role
    return None


def is_entitled_to_agent(jwt_roles: list[str], agent_id: str) -> bool:
    """
    Check if user is entitled to a specific agent.
    
    Args:
        jwt_roles: List of role claims from the JWT token
        agent_id: The agent ID to check
        
    Returns:
        True if user can access the agent
    """
    available = get_available_agents(jwt_roles)
    return agent_id in available
