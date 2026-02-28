"""
Test script for Pricing MCP Server tools.

Run this to verify all pricing tools work correctly.
"""
import asyncio
import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, '../../..'))

from tools import (
    pricing_get_rate_card,
    pricing_get_all_rates,
    pricing_validate_engagement,
    pricing_get_ui_template,
)


async def test_rate_card():
    """Test rate card lookup."""
    print("\n=== Testing Rate Card Lookup ===")
    
    # Test single rate
    result = await pricing_get_rate_card("tax", "Senior Manager")
    print(f"Tax Senior Manager: ${result['hourly_rate']}/hr")
    assert result['hourly_rate'] == 250
    
    # Test all rates
    result = await pricing_get_all_rates("consulting_snow")
    print(f"ServiceNow rates: {len(result['rates'])} roles")
    assert "Partner" in result['rates']
    
    print("✅ Rate card tests passed")


async def test_validation():
    """Test pricing validation."""
    print("\n=== Testing Pricing Validation ===")
    
    # Test low margin warning
    result = await pricing_validate_engagement(
        service_line="tax",
        revenue_model="tm",
        target_margin=0.30,
        estimated_hours=500
    )
    print(f"Validation result: valid={result['valid']}, warnings={len(result['warnings'])}")
    assert len(result['warnings']) > 0  # Should warn about low margin
    
    # Test error for very low margin
    result = await pricing_validate_engagement(
        service_line="aa",
        revenue_model="fixed",
        total_cost=100000,
        total_price=110000  # Only 10% margin
    )
    print(f"Low margin test: valid={result['valid']}, errors={len(result['errors'])}")
    assert not result['valid']  # Should fail validation
    
    print("✅ Validation tests passed")


async def test_ui_templates():
    """Test UI template generation."""
    print("\n=== Testing UI Templates ===")
    
    # Test rate card summary template
    rates_data = await pricing_get_all_rates("tax")
    template = await pricing_get_ui_template("rate_card_summary", rates_data)
    print(f"Rate card template: {template['componentType']}, rows={len(template['payload']['rows'])}")
    assert template['componentType'] == "table"
    assert len(template['payload']['rows']) == 5  # 5 roles
    
    # Test pricing breakdown template
    template = await pricing_get_ui_template("pricing_breakdown", {
        "labor_cost": 150000,
        "expenses": 10000,
        "subtotal": 160000,
        "margin": 0.35,
        "total_price": 246153.85
    })
    print(f"Pricing breakdown: {template['payload']['title']}")
    assert "$150,000.00" in template['payload']['sections'][0]['value']
    
    print("✅ UI template tests passed")


async def main():
    """Run all tests."""
    print("🧪 Testing Pricing MCP Server Tools")
    
    try:
        await test_rate_card()
        await test_validation()
        await test_ui_templates()
        
        print("\n✅ All tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
