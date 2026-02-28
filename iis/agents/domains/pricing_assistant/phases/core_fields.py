"""
Core Fields Phase Handler (Phase 1).

Collects essential engagement details: service line, revenue model, dates, etc.
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def handle_core_fields_phase(
    task: str,
    state: "PricingWizardState",
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle Phase 1: Core Fields.
    
    Generates a form for core engagement details or processes form submission.
    
    Args:
        task: User message
        state: Current wizard state
        context: Request context with optional 'values' dict from form submission
    
    Returns:
        Response dict with manifest
    """
    # Check if this is a form submission
    values = context.get("values", {})
    
    if values:
        # Process form submission
        logger.info(f"[CoreFields] Processing form submission with values: {values}")
        logger.info(f"[CoreFields] State before processing: phase={state.current_phase}, fields={state.collected_fields}")
        
        for key in ["service_portfolio", "revenue_model", "target_date", "legal_entities_count", "geographies"]:
            if key in values:
                logger.info(f"[CoreFields] Setting field: {key}={values[key]}")
                state.set_field(key, values[key])
        
        logger.info(f"[CoreFields] State after processing: phase={state.current_phase}, fields={state.collected_fields}")
        
        # Validate
        if not state.validate_phase(state.current_phase):
            missing = ", ".join(state.required_fields_missing)
            return {
                "type": "assistant",
                "content": f"⚠️ Missing required fields: {missing}. Please provide these to continue.",
                "manifest": None
            }
        
        # Success - signal to transition to BU branch
        return {
            "type": "transition_to_bu_branch",
            "content": "Core fields validated successfully.",
            "manifest": None
        }
    
    # Generate form
    return _generate_core_fields_form(state)


def _generate_core_fields_form(state: "PricingWizardState") -> Dict[str, Any]:
    """Generate the core fields form manifest."""
    return {
        "type": "assistant_manifest",
        "content": "Great! Let's start with the core engagement details.",
        "manifest": {
            "componentType": "form",
            "payload": {
                "title": "📋 Core Engagement Details - Step 1 of 2",
                "fields": [
                    {
                        "key": "service_portfolio",
                        "label": "Service Line",
                        "type": "select",
                        "value": state.get_field("service_portfolio", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Tax", "value": "tax"},
                            {"label": "Audit & Assurance", "value": "aa"},
                            {"label": "Managed Accounting", "value": "managed_acct"},
                            {"label": "Consulting (ServiceNow)", "value": "consulting_snow"},
                            {"label": "Consulting (D365)", "value": "consulting_d365"}
                        ]
                    },
                    {
                        "key": "revenue_model",
                        "label": "Revenue Model",
                        "type": "select",
                        "value": state.get_field("revenue_model", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Time & Materials", "value": "tm"},
                            {"label": "Fixed Fee", "value": "fixed"},
                            {"label": "Milestone-Based", "value": "milestone"},
                            {"label": "Retainer / NTE", "value": "retainer"}
                        ]
                    },
                    {
                        "key": "target_date",
                        "label": "Target Delivery Date",
                        "type": "date",
                        "value": state.get_field("target_date", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "legal_entities_count",
                        "label": "Number of Legal Entities",
                        "type": "number",
                        "value": state.get_field("legal_entities_count", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "geographies",
                        "label": "Geographies (comma-separated)",
                        "type": "text",
                        "value": state.get_field("geographies", ""),
                        "editable": True,
                        "required": True,
                        "tooltip": "e.g., US-CA, US-TX, UK"
                    }
                ],
                "submitAction": "submit_core_fields"
            }
        }
    }
