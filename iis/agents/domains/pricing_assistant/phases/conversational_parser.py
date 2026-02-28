"""
Conversational Parser - Extract structured fields from natural language.

Uses simple keyword matching for now. In production, would use LLM.
"""
from typing import Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


async def extract_fields_from_text(text: str) -> Dict[str, Any]:
    """
    Extract structured pricing fields from conversational text.
    
    Examples:
        "I need a ServiceNow quote for 500 users" → {service_portfolio: "consulting_snow", user_count: 500}
        "Fixed fee D365 implementation" → {service_portfolio: "consulting_d365", revenue_model: "fixed"}
    
    Args:
        text: User's conversational input
    
    Returns:
        Dict of extracted fields
    """
    extracted = {}
    text_lower = text.lower()
    
    # Service portfolio detection
    if "servicenow" in text_lower or "snow" in text_lower or "itsm" in text_lower:
        extracted["service_portfolio"] = "consulting_snow"
    elif "d365" in text_lower or "dynamics" in text_lower or "crm" in text_lower:
        extracted["service_portfolio"] = "consulting_d365"
    elif "salesforce" in text_lower or "sfdc" in text_lower:
        extracted["service_portfolio"] = "consulting_sfdc"
    elif "tax" in text_lower and "return" in text_lower:
        extracted["service_portfolio"] = "tax"
    elif "audit" in text_lower or "assurance" in text_lower:
        extracted["service_portfolio"] = "aa"
    elif "managed accounting" in text_lower or "bookkeeping" in text_lower:
        extracted["service_portfolio"] = "managed_acct"
    
    # Revenue model detection
    if "fixed fee" in text_lower or "fixed price" in text_lower:
        extracted["revenue_model"] = "fixed"
    elif "t&m" in text_lower or "time and materials" in text_lower or "hourly" in text_lower:
        extracted["revenue_model"] = "tm"
    elif "milestone" in text_lower:
        extracted["revenue_model"] = "milestone"
    elif "retainer" in text_lower:
        extracted["revenue_model"] = "retainer"
    
    # User count extraction
    user_match = re.search(r'(\d+)\s*users?', text_lower)
    if user_match:
        extracted["user_count"] = int(user_match.group(1))
    
    # Integration count
    integration_match = re.search(r'(\d+)\s*integrations?', text_lower)
    if integration_match:
        extracted["integration_endpoints"] = int(integration_match.group(1))
    
    # Module detection (ServiceNow)
    modules = []
    if "itsm" in text_lower:
        modules.append("itsm")
    if "itom" in text_lower:
        modules.append("itom")
    if "hrsd" in text_lower or "hr service" in text_lower:
        modules.append("hrsd")
    if "csm" in text_lower or "customer service" in text_lower:
        modules.append("csm")
    
    if modules:
        extracted["modules"] = modules
    
    # Customization complexity (simple heuristics)
    if "custom" in text_lower:
        if "extensive" in text_lower or "heavy" in text_lower:
            extracted["customizations_score"] = 4
        elif "moderate" in text_lower:
            extracted["customizations_score"] = 3
        else:
            extracted["customizations_score"] = 2
    elif "out of the box" in text_lower or "ootb" in text_lower or "standard" in text_lower:
        extracted["customizations_score"] = 1
    
    # Legal entities
    entities_match = re.search(r'(\d+)\s*(?:legal\s*)?entit(?:y|ies)', text_lower)
    if entities_match:
        extracted["legal_entities_count"] = int(entities_match.group(1))
    
    # Geographies (simple extraction)
    geo_patterns = [
        (r'\b(us|usa|united states)\b', 'US'),
        (r'\b(uk|united kingdom)\b', 'UK'),
        (r'\b(ca|canada)\b', 'CA'),
        (r'\b(eu|europe)\b', 'EU'),
    ]
    
    geographies = []
    for pattern, geo_code in geo_patterns:
        if re.search(pattern, text_lower):
            geographies.append(geo_code)
    
    if geographies:
        extracted["geographies"] = ", ".join(geographies)
    
    logger.info(f"[ConversationalParser] Extracted fields: {extracted}")
    return extracted


def generate_confirmation_message(extracted: Dict[str, Any]) -> str:
    """
    Generate a confirmation message for extracted fields.
    
    Args:
        extracted: Dict of extracted fields
    
    Returns:
        Human-readable confirmation message
    """
    parts = []
    
    if "service_portfolio" in extracted:
        service_map = {
            "consulting_snow": "ServiceNow Consulting",
            "consulting_d365": "Dynamics 365 Consulting",
            "consulting_sfdc": "Salesforce Consulting",
            "tax": "Tax Services",
            "aa": "Audit & Assurance",
            "managed_acct": "Managed Accounting"
        }
        parts.append(f"**Service Line:** {service_map.get(extracted['service_portfolio'], extracted['service_portfolio'])}")
    
    if "revenue_model" in extracted:
        model_map = {
            "fixed": "Fixed Fee",
            "tm": "Time & Materials",
            "milestone": "Milestone-Based",
            "retainer": "Retainer / NTE"
        }
        parts.append(f"**Revenue Model:** {model_map.get(extracted['revenue_model'], extracted['revenue_model'])}")
    
    if "user_count" in extracted:
        parts.append(f"**User Count:** {extracted['user_count']}")
    
    if "modules" in extracted:
        parts.append(f"**Modules:** {', '.join(extracted['modules']).upper()}")
    
    if "integration_endpoints" in extracted:
        parts.append(f"**Integrations:** {extracted['integration_endpoints']}")
    
    if "customizations_score" in extracted:
        parts.append(f"**Customization Complexity:** {extracted['customizations_score']}/5")
    
    if "legal_entities_count" in extracted:
        parts.append(f"**Legal Entities:** {extracted['legal_entities_count']}")
    
    if "geographies" in extracted:
        parts.append(f"**Geographies:** {extracted['geographies']}")
    
    if not parts:
        return "I couldn't extract any specific details from your message. Could you provide more information?"
    
    return "I understood the following from your request:\n\n" + "\n".join(parts) + "\n\nIs this correct?"
