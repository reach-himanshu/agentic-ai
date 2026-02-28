"""
BU Branch Phase Handler (Phase 2).

Generates service-line-specific forms (Tax, A&A, ServiceNow, etc.).
"""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def handle_bu_branch_phase(
    task: str,
    state: "PricingWizardState",
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle Phase 2: BU-Specific Branch.
    
    Generates forms based on selected service_portfolio.
    
    Args:
        task: User message
        state: Current wizard state
        context: Request context with optional 'values' dict
    
    Returns:
        Response dict with manifest
    """
    service_portfolio = state.get_field("service_portfolio")
    
    # Check if this is a form submission
    values = context.get("values", {})
    
    if values:
        # Process form submission
        return await _process_bu_form_submission(state, values, service_portfolio)
    
    # Generate form based on service line
    if service_portfolio == "consulting_snow":
        return _generate_servicenow_form(state)
    elif service_portfolio == "consulting_d365":
        return _generate_d365_form(state)
    elif service_portfolio == "tax":
        return _generate_tax_form(state)
    elif service_portfolio == "aa":
        return _generate_aa_form(state)
    elif service_portfolio == "managed_acct":
        return _generate_managed_acct_form(state)
    else:
        return {
            "type": "assistant",
            "content": f"✅ Core fields complete! BU-specific questions for **{service_portfolio}** are coming in future updates.",
            "manifest": None
        }


async def _process_bu_form_submission(
    state: "PricingWizardState",
    values: Dict[str, Any],
    service_portfolio: str
) -> Dict[str, Any]:
    """Process BU-specific form submission."""
    # Extract fields based on service line
    if service_portfolio == "consulting_snow":
        field_keys = ["modules", "user_count", "customizations_score", "integration_endpoints", "hypercare_weeks"]
    elif service_portfolio == "consulting_d365":
        field_keys = ["d365_modules", "d365_user_count", "data_migration_complexity", "customization_level", "go_live_date"]
    elif service_portfolio == "tax":
        field_keys = ["tax_entity_types", "jurisdictions", "tax_forms_count", "compliance_needs", "prior_year_issues"]
    elif service_portfolio == "aa":
        field_keys = ["aa_service_type", "audit_frameworks", "subsidiaries_count", "materiality_threshold", "risk_assessment"]
    elif service_portfolio == "managed_acct":
        field_keys = ["accounting_systems", "transaction_volume", "reporting_frequency", "reconciliation_accounts", "close_timeline"]
    else:
        field_keys = []
    
    for key in field_keys:
        if key in values:
            state.set_field(key, values[key])
    
    # Validate
    if not state.validate_phase(state.current_phase):
        missing = ", ".join(state.required_fields_missing)
        return {
            "type": "assistant",
            "content": f"⚠️ Missing required fields: {missing}. Please provide these to continue.",
            "manifest": None
        }
    
    # Success! Show completion summary
    completion_pct = state.get_completion_percentage()
    service_line_display = service_portfolio.upper() if service_portfolio else "UNKNOWN"
    
    return {
        "type": "assistant",
        "content": f"✅ {service_line_display} scope complete! You're **{completion_pct}%** done. Resourcing and pricing computation coming in Checkpoint 3!",
        "manifest": None
    }


def _generate_servicenow_form(state: "PricingWizardState") -> Dict[str, Any]:
    """Generate ServiceNow scope form."""
    return {
        "type": "assistant_manifest",
        "content": "Now, let's dive into the ServiceNow engagement scope.",
        "manifest": {
            "componentType": "form",
            "payload": {  # ← Critical: wrap in payload
                "title": "🛠️ ServiceNow Engagement Scope - Step 2 of 2",
                "fields": [
                    {
                        "key": "modules",
                        "label": "Modules in Scope",
                        "type": "multiselect",
                        "value": state.get_field("modules", []),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "IT Service Management (ITSM)", "value": "itsm"},
                            {"label": "IT Operations Management (ITOM)", "value": "itom"},
                            {"label": "HR Service Delivery (HRSD)", "value": "hrsd"},
                            {"label": "Customer Service Management (CSM)", "value": "csm"}
                        ]
                    },
                    {
                        "key": "user_count",
                        "label": "Total User Count",
                        "type": "number",
                        "value": state.get_field("user_count", ""),
                        "editable": True,
                        "required": True,
                        "tooltip": "Total named users who will access the platform"
                    },
                    {
                        "key": "customizations_score",
                        "label": "Customization Complexity (1-5)",
                        "type": "select",
                        "value": state.get_field("customizations_score", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "1 - Minimal (OOTB)", "value": 1},
                            {"label": "2 - Light (Minor Config)", "value": 2},
                            {"label": "3 - Moderate (Custom Workflows)", "value": 3},
                            {"label": "4 - Heavy (Custom Apps)", "value": 4},
                            {"label": "5 - Extensive (Platform Extension)", "value": 5}
                        ]
                    },
                    {
                        "key": "integration_endpoints",
                        "label": "Number of Integrations",
                        "type": "number",
                        "value": state.get_field("integration_endpoints", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "hypercare_weeks",
                        "label": "Hypercare Duration (weeks)",
                        "type": "number",
                        "value": state.get_field("hypercare_weeks", 4),
                        "editable": True,
                        "required": True
                    }
                ],
                "submitAction": "submit_consulting_snow_fields"
            }
        }
    }


def _generate_tax_form(state: "PricingWizardState") -> Dict[str, Any]:
    """Generate Tax scope form."""
    return {
        "type": "assistant_manifest",
        "content": "Great! Now let's gather the tax-specific details for your engagement.",
        "manifest": {
            "componentType": "form",
            "payload": {  # ← Critical: wrap in payload
                "title": "📊 Tax Engagement Scope - Step 2 of 2",
                "fields": [
                    {
                        "key": "tax_entity_types",
                        "label": "Entity Types",
                        "type": "multiselect",
                        "value": state.get_field("tax_entity_types", []),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "C-Corporation", "value": "c_corp"},
                            {"label": "S-Corporation", "value": "s_corp"},
                            {"label": "Partnership", "value": "partnership"},
                            {"label": "LLC", "value": "llc"},
                            {"label": "Individual/Trust", "value": "individual"}
                        ]
                    },
                    {
                        "key": "jurisdictions",
                        "label": "Tax Jurisdictions",
                        "type": "text",
                        "value": state.get_field("jurisdictions", ""),
                        "editable": True,
                        "required": True,
                        "tooltip": "e.g., Federal, CA, NY, TX"
                    },
                    {
                        "key": "tax_forms_count",
                        "label": "Number of Tax Forms/Returns",
                        "type": "number",
                        "value": state.get_field("tax_forms_count", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "compliance_needs",
                        "label": "Compliance Requirements",
                        "type": "select",
                        "value": state.get_field("compliance_needs", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Standard Compliance", "value": "standard"},
                            {"label": "Multi-State Compliance", "value": "multi_state"},
                            {"label": "International Tax", "value": "international"},
                            {"label": "Transfer Pricing", "value": "transfer_pricing"}
                        ]
                    },
                    {
                        "key": "prior_year_issues",
                        "label": "Prior Year Issues or Amendments?",
                        "type": "select",
                        "value": state.get_field("prior_year_issues", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "No", "value": "no"},
                            {"label": "Yes - Minor", "value": "minor"},
                            {"label": "Yes - Significant", "value": "significant"}
                        ]
                    }
                ],
                "submitAction": "submit_tax_fields"
            }
        }
    }


def _generate_aa_form(state: "PricingWizardState") -> Dict[str, Any]:
    """Generate Audit & Assurance scope form."""
    return {
        "type": "assistant_manifest",
        "content": "Perfect! Let's define the audit scope and requirements.",
        "manifest": {
            "componentType": "form",
            "payload": {
                "title": "🔍 Audit & Assurance Scope - Step 2 of 2",
                "fields": [
                    {
                        "key": "aa_service_type",
                        "label": "Service Type",
                        "type": "select",
                        "value": state.get_field("aa_service_type", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Financial Statement Audit", "value": "fs_audit"},
                            {"label": "SOC 1/2 Audit", "value": "soc"},
                            {"label": "Internal Audit", "value": "internal"},
                            {"label": "Compliance Audit", "value": "compliance"},
                            {"label": "Review/Compilation", "value": "review"}
                        ]
                    },
                    {
                        "key": "audit_frameworks",
                        "label": "Applicable Frameworks",
                        "type": "multiselect",
                        "value": state.get_field("audit_frameworks", []),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "GAAP", "value": "gaap"},
                            {"label": "IFRS", "value": "ifrs"},
                            {"label": "SOX 404", "value": "sox"},
                            {"label": "AICPA Standards", "value": "aicpa"}
                        ]
                    },
                    {
                        "key": "subsidiaries_count",
                        "label": "Number of Subsidiaries/Locations",
                        "type": "number",
                        "value": state.get_field("subsidiaries_count", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "materiality_threshold",
                        "label": "Estimated Materiality Threshold ($)",
                        "type": "number",
                        "value": state.get_field("materiality_threshold", ""),
                        "editable": True,
                        "required": True,
                        "tooltip": "Approximate dollar amount for planning purposes"
                    },
                    {
                        "key": "risk_assessment",
                        "label": "Risk Assessment Level",
                        "type": "select",
                        "value": state.get_field("risk_assessment", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Low Risk", "value": "low"},
                            {"label": "Moderate Risk", "value": "moderate"},
                            {"label": "High Risk", "value": "high"}
                        ]
                    }
                ],
                "submitAction": "submit_aa_fields"
            }
        }
    }


def _generate_managed_acct_form(state: "PricingWizardState") -> Dict[str, Any]:
    """Generate Managed Accounting scope form."""
    return {
        "type": "assistant_manifest",
        "content": "Excellent! Let's capture the managed accounting engagement details.",
        "manifest": {
            "componentType": "form",
            "payload": {
                "title": "📚 Managed Accounting Scope - Step 2 of 2",
                "fields": [
                    {
                        "key": "accounting_systems",
                        "label": "Accounting Systems",
                        "type": "multiselect",
                        "value": state.get_field("accounting_systems", []),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "QuickBooks", "value": "quickbooks"},
                            {"label": "NetSuite", "value": "netsuite"},
                            {"label": "Sage Intacct", "value": "sage"},
                            {"label": "Xero", "value": "xero"},
                            {"label": "Other/Custom", "value": "other"}
                        ]
                    },
                    {
                        "key": "transaction_volume",
                        "label": "Monthly Transaction Volume",
                        "type": "select",
                        "value": state.get_field("transaction_volume", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "< 100 transactions", "value": "low"},
                            {"label": "100-500 transactions", "value": "medium"},
                            {"label": "500-2000 transactions", "value": "high"},
                            {"label": "> 2000 transactions", "value": "very_high"}
                        ]
                    },
                    {
                        "key": "reporting_frequency",
                        "label": "Financial Reporting Frequency",
                        "type": "select",
                        "value": state.get_field("reporting_frequency", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Monthly", "value": "monthly"},
                            {"label": "Quarterly", "value": "quarterly"},
                            {"label": "Annual", "value": "annual"}
                        ]
                    },
                    {
                        "key": "reconciliation_accounts",
                        "label": "Number of Accounts to Reconcile",
                        "type": "number",
                        "value": state.get_field("reconciliation_accounts", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "close_timeline",
                        "label": "Month-End Close Timeline (days)",
                        "type": "number",
                        "value": state.get_field("close_timeline", ""),
                        "editable": True,
                        "required": True,
                        "tooltip": "Target days to complete month-end close"
                    }
                ],
                "submitAction": "submit_managed_acct_fields"
            }
        }
    }


def _generate_d365_form(state: "PricingWizardState") -> Dict[str, Any]:
    """Generate D365 Consulting scope form."""
    return {
        "type": "assistant_manifest",
        "content": "Great! Let's define the Dynamics 365 implementation scope.",
        "manifest": {
            "componentType": "form",
            "payload": {
                "title": "💼 Dynamics 365 Implementation Scope - Step 2 of 2",
                "fields": [
                    {
                        "key": "d365_modules",
                        "label": "D365 Modules",
                        "type": "multiselect",
                        "value": state.get_field("d365_modules", []),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Sales", "value": "sales"},
                            {"label": "Customer Service", "value": "service"},
                            {"label": "Field Service", "value": "field_service"},
                            {"label": "Marketing", "value": "marketing"},
                            {"label": "Finance & Operations", "value": "finance_ops"}
                        ]
                    },
                    {
                        "key": "d365_user_count",
                        "label": "Total D365 User Count",
                        "type": "number",
                        "value": state.get_field("d365_user_count", ""),
                        "editable": True,
                        "required": True
                    },
                    {
                        "key": "data_migration_complexity",
                        "label": "Data Migration Complexity",
                        "type": "select",
                        "value": state.get_field("data_migration_complexity", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Simple (< 5 entities)", "value": "simple"},
                            {"label": "Moderate (5-15 entities)", "value": "moderate"},
                            {"label": "Complex (15+ entities)", "value": "complex"}
                        ]
                    },
                    {
                        "key": "customization_level",
                        "label": "Customization Level",
                        "type": "select",
                        "value": state.get_field("customization_level", ""),
                        "editable": True,
                        "required": True,
                        "options": [
                            {"label": "Minimal (OOTB)", "value": "minimal"},
                            {"label": "Moderate (Custom Fields/Forms)", "value": "moderate"},
                            {"label": "Extensive (Custom Entities/Workflows)", "value": "extensive"}
                        ]
                    },
                    {
                        "key": "go_live_date",
                        "label": "Target Go-Live Date",
                        "type": "date",
                        "value": state.get_field("go_live_date", ""),
                        "editable": True,
                        "required": True
                    }
                ],
                "submitAction": "submit_consulting_d365_fields"
            }
        }
    }
