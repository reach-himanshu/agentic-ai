"""
Basic tests for Pricing Assistant wizard state management.

Run with: python -m pytest iis/agents/domains/pricing_assistant/tests/test_wizard_state.py -v
"""
import pytest
from datetime import datetime
from ..wizard_state import PricingWizardState, WizardPhase


def test_create_new_wizard_state():
    """Test creating a new wizard state."""
    state = PricingWizardState.create_new("test_wizard_123")
    
    assert state.wizard_id == "test_wizard_123"
    assert state.current_phase == WizardPhase.NOT_STARTED
    assert state.started_at is not None
    assert len(state.collected_fields) == 0


def test_phase_transition():
    """Test phase transitions and history tracking."""
    state = PricingWizardState.create_new("test_wizard")
    
    state.transition_to(WizardPhase.CRM_CONTEXT)
    assert state.current_phase == WizardPhase.CRM_CONTEXT
    assert WizardPhase.NOT_STARTED in state.phase_history
    
    state.transition_to(WizardPhase.CORE_FIELDS)
    assert state.current_phase == WizardPhase.CORE_FIELDS
    assert len(state.phase_history) == 2


def test_set_and_get_field():
    """Test field setting and retrieval."""
    state = PricingWizardState.create_new("test_wizard")
    
    state.set_field("service_portfolio", "consulting_snow")
    assert state.get_field("service_portfolio") == "consulting_snow"
    
    # Test default value
    assert state.get_field("nonexistent", "default") == "default"
    
    # Test change log
    assert len(state.field_change_log) == 1
    assert state.field_change_log[0]["field"] == "service_portfolio"


def test_validation():
    """Test phase validation."""
    state = PricingWizardState.create_new("test_wizard")
    state.transition_to(WizardPhase.CORE_FIELDS)
    
    # Should fail - missing required fields
    assert not state.validate_phase(WizardPhase.CORE_FIELDS)
    assert len(state.required_fields_missing) > 0
    
    # Add required fields
    state.set_field("service_portfolio", "consulting_snow")
    state.set_field("revenue_model", "fixed")
    state.set_field("target_date", "2026-06-01")
    state.set_field("legal_entities_count", 2)
    state.set_field("geographies", "US-CA, US-TX")
    
    # Should pass
    assert state.validate_phase(WizardPhase.CORE_FIELDS)
    assert len(state.required_fields_missing) == 0


def test_clear_fields_from_phase():
    """Test backtracking by clearing phase fields."""
    state = PricingWizardState.create_new("test_wizard")
    
    # Set core fields
    state.set_field("service_portfolio", "consulting_snow")
    state.set_field("revenue_model", "fixed")
    
    # Set BU branch fields
    state.set_field("modules", ["itsm", "itom"])
    state.set_field("user_count", 500)
    
    # Clear BU branch fields
    state.clear_fields_from_phase(WizardPhase.BU_BRANCH)
    
    # Core fields should remain
    assert state.get_field("service_portfolio") == "consulting_snow"
    
    # BU fields should be cleared
    assert state.get_field("modules") is None
    assert state.get_field("user_count") is None


def test_completion_percentage():
    """Test completion percentage calculation."""
    state = PricingWizardState.create_new("test_wizard")
    
    assert state.get_completion_percentage() == 0
    
    state.transition_to(WizardPhase.CORE_FIELDS)
    assert state.get_completion_percentage() == 30
    
    state.transition_to(WizardPhase.BU_BRANCH)
    assert state.get_completion_percentage() == 60
    
    state.transition_to(WizardPhase.COMPLETE)
    assert state.get_completion_percentage() == 100


def test_serialization():
    """Test state serialization and deserialization."""
    state = PricingWizardState.create_new("test_wizard")
    state.set_field("service_portfolio", "consulting_snow")
    state.transition_to(WizardPhase.CORE_FIELDS)
    
    # Serialize
    data = state.to_dict()
    assert isinstance(data, dict)
    assert data["wizard_id"] == "test_wizard"
    
    # Deserialize
    restored = PricingWizardState.from_dict(data)
    assert restored.wizard_id == state.wizard_id
    assert restored.current_phase == state.current_phase
    assert restored.get_field("service_portfolio") == "consulting_snow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
