"""
Rate Card Tool for Pricing MCP Server.

Provides rate card lookup functionality for different service lines and roles.
"""
import json
import os
from typing import Dict, Any, Optional

# Load rate cards from JSON file
_RATE_CARDS: Optional[Dict] = None

def _load_rate_cards() -> Dict:
    """Load rate cards from JSON file."""
    global _RATE_CARDS
    if _RATE_CARDS is None:
        current_dir = os.path.dirname(__file__)
        rate_card_path = os.path.join(current_dir, "..", "resources", "rate_cards.json")
        with open(rate_card_path, "r", encoding="utf-8") as f:
            _RATE_CARDS = json.load(f)
    return _RATE_CARDS


async def pricing_get_rate_card(
    service_line: str,
    role: str,
    geography: str = "US"
) -> Dict[str, Any]:
    """
    Get hourly rate for a specific service line and role.
    
    Args:
        service_line: Service line (tax, aa, managed_acct, consulting_snow, consulting_d365)
        role: Role level (Partner, Senior Manager, Manager, Senior, Staff)
        geography: Geographic region (US, UK, India) - currently only US supported
    
    Returns:
        Dict with role, hourly_rate, currency, effective_date, service_line
    
    Raises:
        ValueError: If service_line or role not found
    """
    rate_cards = _load_rate_cards()
    
    # Validate service line
    if service_line not in rate_cards:
        raise ValueError(
            f"Service line '{service_line}' not found. "
            f"Available: {', '.join(rate_cards.keys())}"
        )
    
    # Validate role
    if role not in rate_cards[service_line]:
        raise ValueError(
            f"Role '{role}' not found for service line '{service_line}'. "
            f"Available: {', '.join(rate_cards[service_line].keys())}"
        )
    
    # Get rate card
    rate_data = rate_cards[service_line][role]
    
    return {
        "role": role,
        "hourly_rate": rate_data["hourly_rate"],
        "currency": rate_data["currency"],
        "effective_date": rate_data["effective_date"],
        "service_line": service_line,
        "geography": geography
    }


async def pricing_get_all_rates(service_line: str) -> Dict[str, Any]:
    """
    Get all rates for a specific service line.
    
    Args:
        service_line: Service line (tax, aa, managed_acct, consulting_snow, consulting_d365)
    
    Returns:
        Dict with service_line and rates for all roles
    """
    rate_cards = _load_rate_cards()
    
    if service_line not in rate_cards:
        raise ValueError(
            f"Service line '{service_line}' not found. "
            f"Available: {', '.join(rate_cards.keys())}"
        )
    
    return {
        "service_line": service_line,
        "rates": rate_cards[service_line]
    }
