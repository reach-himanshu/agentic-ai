"""
UI Template Tool for Pricing MCP Server.

Provides Zero-LLM UI template generation.
"""
import json
import os
from typing import Dict, Any, Optional
import copy

# Load templates from JSON file
_TEMPLATES: Optional[Dict] = None

def _load_templates() -> Dict:
    """Load UI templates from JSON file."""
    global _TEMPLATES
    if _TEMPLATES is None:
        current_dir = os.path.dirname(__file__)
        template_path = os.path.join(current_dir, "..", "resources", "templates.json")
        with open(template_path, "r", encoding="utf-8") as f:
            _TEMPLATES = json.load(f)
    return _TEMPLATES


async def pricing_get_ui_template(
    template_name: str,
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Get a pre-built UI template (Zero-LLM).
    
    Args:
        template_name: Template name (rate_card_summary, pricing_breakdown, approval_request)
        data: Optional data to inject into template
    
    Returns:
        UI manifest dict ready for frontend rendering
    
    Raises:
        ValueError: If template not found
    """
    templates = _load_templates()
    
    if template_name not in templates:
        raise ValueError(
            f"Template '{template_name}' not found. "
            f"Available: {', '.join(templates.keys())}"
        )
    
    # Deep copy template to avoid modifying cached version
    template = copy.deepcopy(templates[template_name])
    
    # Inject data if provided
    if data:
        template = _inject_data(template, data, template_name)
    
    return template


def _inject_data(template: Dict, data: Dict, template_name: str) -> Dict:
    """Inject data into template based on template type."""
    
    if template_name == "rate_card_summary":
        # Inject rate card rows
        if "rates" in data:
            rows = []
            for role, rate_info in data["rates"].items():
                rows.append([
                    role,
                    f"${rate_info['hourly_rate']}/hr",
                    rate_info["currency"]
                ])
            template["payload"]["rows"] = rows
    
    elif template_name == "pricing_breakdown":
        # Inject pricing sections
        if "labor_cost" in data:
            template["payload"]["sections"][0]["value"] = f"${data['labor_cost']:,.2f}"
        if "expenses" in data:
            template["payload"]["sections"][1]["value"] = f"${data['expenses']:,.2f}"
        if "subtotal" in data:
            template["payload"]["sections"][2]["value"] = f"${data['subtotal']:,.2f}"
        if "margin" in data:
            template["payload"]["sections"][3]["value"] = f"{data['margin']:.1%}"
        if "total_price" in data:
            template["payload"]["sections"][4]["value"] = f"${data['total_price']:,.2f}"
    
    elif template_name == "approval_request":
        # Inject approval request data
        if "engagement_name" in data:
            template["payload"]["sections"][0]["value"] = data["engagement_name"]
        if "total_price" in data:
            template["payload"]["sections"][1]["value"] = f"${data['total_price']:,.2f}"
        if "margin" in data:
            template["payload"]["sections"][2]["value"] = f"{data['margin']:.1%}"
        if "status" in data:
            template["payload"]["sections"][3]["value"] = data["status"]
    
    return template
