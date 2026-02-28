"""
Validation Tool for Pricing MCP Server.

Provides business rule validation for pricing engagements.
"""
from typing import Dict, Any, List


# Business rules configuration
MARGIN_THRESHOLDS = {
    "tax": 0.40,  # 40% recommended margin for tax
    "aa": 0.45,  # 45% for audit & assurance
    "managed_acct": 0.35,  # 35% for managed accounting
    "consulting_snow": 0.50,  # 50% for ServiceNow consulting
    "consulting_d365": 0.50,  # 50% for D365 consulting
}

MAX_HOURS_PER_ENGAGEMENT = {
    "tax": 2000,
    "aa": 3000,
    "managed_acct": 1500,
    "consulting_snow": 5000,
    "consulting_d365": 5000,
}


async def pricing_validate_engagement(
    service_line: str,
    revenue_model: str,
    estimated_hours: int = None,
    target_margin: float = None,
    total_cost: float = None,
    total_price: float = None
) -> Dict[str, Any]:
    """
    Validate pricing parameters against business rules.
    
    Args:
        service_line: Service line (tax, aa, managed_acct, consulting_snow, consulting_d365)
        revenue_model: Revenue model (tm, fixed, milestone, retainer)
        estimated_hours: Estimated hours for engagement
        target_margin: Target margin (0.0-1.0)
        total_cost: Total cost
        total_price: Total price
    
    Returns:
        Dict with valid (bool), warnings (list), errors (list)
    """
    warnings: List[str] = []
    errors: List[str] = []
    
    # Validate service line
    if service_line not in MARGIN_THRESHOLDS:
        errors.append(f"Invalid service line: {service_line}")
        return {"valid": False, "warnings": warnings, "errors": errors}
    
    # Validate margin
    if target_margin is not None:
        recommended_margin = MARGIN_THRESHOLDS[service_line]
        if target_margin < recommended_margin:
            warnings.append(
                f"Margin {target_margin:.0%} is below recommended {recommended_margin:.0%} "
                f"for {service_line} engagements"
            )
        if target_margin < 0.20:
            errors.append("Margin below 20% requires executive approval")
    
    # Validate hours
    if estimated_hours is not None:
        max_hours = MAX_HOURS_PER_ENGAGEMENT.get(service_line, 10000)
        if estimated_hours > max_hours:
            warnings.append(
                f"Estimated hours ({estimated_hours}) exceed typical maximum ({max_hours}) "
                f"for {service_line} engagements"
            )
        if estimated_hours < 10:
            warnings.append("Very low hour estimate - consider minimum engagement size")
    
    # Validate revenue model compatibility
    if revenue_model == "fixed" and estimated_hours is None:
        errors.append("Fixed fee engagements require estimated hours for pricing")
    
    # Calculate margin if cost and price provided
    if total_cost is not None and total_price is not None:
        if total_price <= total_cost:
            errors.append("Total price must be greater than total cost")
        else:
            calculated_margin = (total_price - total_cost) / total_price
            if calculated_margin < 0.20:
                errors.append(f"Calculated margin {calculated_margin:.0%} is below minimum 20%")
    
    return {
        "valid": len(errors) == 0,
        "warnings": warnings,
        "errors": errors
    }
