"""
Wizard state management for Pricing Assistant.

Defines the state schema and persistence logic for the multi-phase pricing wizard.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class WizardPhase(str, Enum):
    """Enum for wizard phases."""
    NOT_STARTED = "not_started"
    CRM_CONTEXT = "crm_context"
    CORE_FIELDS = "core_fields"
    BU_BRANCH = "bu_branch"
    RESOURCING = "resourcing"
    COMPUTE = "compute"
    ARTIFACTS = "artifacts"
    COMPLETE = "complete"


class PricingWizardState(BaseModel):
    """
    State container for the pricing wizard.
    
    This is persisted to the database as JSON and loaded/saved
    throughout the wizard flow.
    """
    # Wizard metadata
    wizard_id: str = Field(default="", description="Unique ID for this wizard session")
    current_phase: WizardPhase = Field(default=WizardPhase.NOT_STARTED)
    started_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Collected fields (all user inputs)
    collected_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation state
    validation_errors: Dict[str, List[str]] = Field(default_factory=dict)
    required_fields_missing: List[str] = Field(default_factory=list)
    
    # Backtracking support
    phase_history: List[WizardPhase] = Field(default_factory=list)
    field_change_log: List[Dict[str, Any]] = Field(default_factory=list)
    
    # ML and computation results (cached)
    ml_recommendation: Optional[Dict[str, Any]] = None
    price_bands: Optional[Dict[str, float]] = None
    projected_margin: Optional[float] = None
    
    # Approval tracking
    approval_requests: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Generated artifacts
    generated_artifacts: List[str] = Field(default_factory=list)
    
    def transition_to(self, new_phase: WizardPhase):
        """Transition to a new phase and update history."""
        if self.current_phase != new_phase:
            self.phase_history.append(self.current_phase)
            self.current_phase = new_phase
            self.updated_at = datetime.utcnow()
    
    def set_field(self, key: str, value: Any):
        """Set a field value and log the change."""
        import logging
        logger = logging.getLogger(__name__)
        
        old_value = self.collected_fields.get(key)
        self.collected_fields[key] = value
        
        logger.info(f"[WizardState] set_field: key='{key}', value='{value}', old_value='{old_value}'")
        logger.info(f"[WizardState] collected_fields after set: {self.collected_fields}")
        
        self.field_change_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "field": key,
            "old_value": old_value,
            "new_value": value
        })
        self.updated_at = datetime.utcnow()
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """Get a field value with optional default."""
        return self.collected_fields.get(key, default)
    
    def clear_fields_from_phase(self, phase: WizardPhase):
        """
        Clear fields collected in a specific phase (for backtracking).
        
        This is used when the user changes a core field that invalidates
        downstream data (e.g., changing service line clears BU-specific fields).
        """
        # Define which fields belong to which phase
        phase_field_mapping = {
            WizardPhase.CRM_CONTEXT: ["account_name", "industry", "opportunity_id", "client_segment"],
            WizardPhase.CORE_FIELDS: [
                "service_portfolio", "revenue_model", "target_date",
                "legal_entities_count", "geographies", "deliverables", "exclusions"
            ],
            WizardPhase.BU_BRANCH: [
                # ServiceNow
                "modules", "user_count", "customizations_score", "integration_endpoints",
                "migration_records", "environments", "hypercare_weeks",
                # Tax (future)
                "tax_entity_types", "jurisdictions", "forms_and_counts",
                # A&A (future)
                "aa_service_type", "frameworks", "subsidiaries_count"
            ],
            WizardPhase.RESOURCING: [
                "resourcing_grid", "rate_card_version", "onshore_pct", "offshore_pct",
                "partner_manager_pct", "discount_pct", "discount_rationale"
            ]
        }
        
        fields_to_clear = phase_field_mapping.get(phase, [])
        for field in fields_to_clear:
            if field in self.collected_fields:
                del self.collected_fields[field]
        
        self.updated_at = datetime.utcnow()
    
    def validate_phase(self, phase: WizardPhase) -> bool:
        """
        Validate that all required fields for a phase are present.
        
        Returns True if valid, False otherwise.
        Updates validation_errors and required_fields_missing.
        """
        self.validation_errors.clear()
        self.required_fields_missing.clear()
        
        # Define required fields per phase
        required_by_phase = {
            WizardPhase.CORE_FIELDS: [
                "service_portfolio", "revenue_model", "target_date",
                "legal_entities_count", "geographies"
            ],
            WizardPhase.BU_BRANCH: self._get_bu_required_fields(),
        }
        
        required_fields = required_by_phase.get(phase, [])
        
        for field in required_fields:
            if field not in self.collected_fields or not self.collected_fields[field]:
                self.required_fields_missing.append(field)
                self.validation_errors[field] = [f"{field} is required"]
        
        return len(self.required_fields_missing) == 0
    
    def _get_bu_required_fields(self) -> List[str]:
        """Get required fields based on selected service portfolio."""
        service_portfolio = self.get_field("service_portfolio")
        
        if service_portfolio == "consulting_snow":
            return ["modules", "user_count", "customizations_score", "integration_endpoints", "environments", "hypercare_weeks"]
        elif service_portfolio == "tax":
            return ["tax_entity_types", "jurisdictions", "forms_and_counts"]
        elif service_portfolio == "aa":
            return ["aa_service_type", "frameworks", "subsidiaries_count"]
        
        return []
    
    def get_completion_percentage(self) -> int:
        """Calculate wizard completion percentage."""
        phase_weights = {
            WizardPhase.NOT_STARTED: 0,
            WizardPhase.CRM_CONTEXT: 10,
            WizardPhase.CORE_FIELDS: 30,
            WizardPhase.BU_BRANCH: 60,
            WizardPhase.RESOURCING: 80,
            WizardPhase.COMPUTE: 90,
            WizardPhase.ARTIFACTS: 95,
            WizardPhase.COMPLETE: 100
        }
        return phase_weights.get(self.current_phase, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON storage."""
        return self.model_dump(mode='json')
    
    def __init__(self, **kwargs):
        """Initialize wizard state, handling enum conversion for deserialization."""
        # Convert string phase values to enums if needed before Pydantic's validation
        if "current_phase" in kwargs and isinstance(kwargs["current_phase"], str):
            kwargs["current_phase"] = WizardPhase(kwargs["current_phase"])
        if "phase_history" in kwargs and kwargs["phase_history"]:
            kwargs["phase_history"] = [
                WizardPhase(p) if isinstance(p, str) else p 
                for p in kwargs["phase_history"]
            ]
        
        super().__init__(**kwargs) # Call Pydantic's BaseModel __init__
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PricingWizardState":
        """Deserialize from dict."""
        return cls(**data)
    
    @classmethod
    def create_new(cls, wizard_id: str) -> "PricingWizardState":
        """Create a new wizard state."""
        return cls(
            wizard_id=wizard_id,
            current_phase=WizardPhase.NOT_STARTED,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
