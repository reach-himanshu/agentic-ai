"""
CRM Context Phase Handler (Phase 0).

Fetches opportunity data from D365 and generates a confirmation form.
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


async def handle_crm_context_phase(
    task: str,
    state: "PricingWizardState",
    context: Dict[str, Any],
    d365_mcp: Any = None
) -> Dict[str, Any]:
    """
    Handle Phase 0: CRM Context.
    
    Tries to fetch opportunity data from D365 and generates a confirmation form.
    If no CRM data is available, skips to core fields.
    
    Args:
        task: User message
        state: Current wizard state
        context: Request context (session_id, user_id, etc.)
        d365_mcp: D365 MCP instance (optional)
    
    Returns:
        Response dict with manifest
    """
    # Try to fetch CRM context
    crm_data = await _fetch_crm_context(context, d365_mcp)
    
    if crm_data:
        # Pre-fill state
        state.set_field("account_name", crm_data.get("account_name"))
        state.set_field("industry", crm_data.get("industry"))
        state.set_field("opportunity_id", crm_data.get("opportunity_id"))
        state.set_field("client_segment", crm_data.get("client_segment"))
        
        # Generate confirmation form
        return {
            "type": "assistant_manifest",
            "content": f"I found your opportunity **{crm_data.get('opportunity_id')}** for **{crm_data.get('account_name')}** ({crm_data.get('industry')}). Is this correct?",
            "manifest": {
                "componentType": "form",
                "title": "📋 Confirm CRM Context",
                "fields": [
                    {
                        "key": "account_name",
                        "label": "Account",
                        "value": crm_data.get("account_name"),
                        "editable": False
                    },
                    {
                        "key": "industry",
                        "label": "Industry",
                        "value": crm_data.get("industry"),
                        "editable": True
                    },
                    {
                        "key": "opportunity_id",
                        "label": "Opportunity ID",
                        "value": crm_data.get("opportunity_id"),
                        "editable": False
                    }
                ],
                "submitAction": "confirm_crm_context"
            }
        }
    else:
        # No CRM context, return message to skip to core fields
        return {
            "type": "skip_to_core",
            "content": "No CRM context found. Proceeding to core fields.",
            "manifest": None
        }


async def _fetch_crm_context(
    context: Dict[str, Any],
    d365_mcp: Any = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch CRM context from D365.
    
    For now, returns mock data for testing. In production, calls d365_get_opportunity.
    """
    # TODO: Implement real D365 integration
    # opportunity_id = context.get("opportunity_id")
    # if opportunity_id and d365_mcp:
    #     try:
    #         result = await d365_mcp.call_tool("d365_get_opportunity", {"opportunity_id": opportunity_id})
    #         return result
    #     except Exception as e:
    #         logger.error(f"Failed to fetch CRM context: {e}")
    
    logger.info("[CRMContext] CRM fetch not yet implemented, returning None")
    return None
