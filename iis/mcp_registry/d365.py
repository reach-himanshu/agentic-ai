from mcp.server.fastmcp import FastMCP
from integrations.d365.service import D365Client
from integrations.d365.schemas import AccountInput, ContactInput, OpportunityInput, DeepInsertInput
import logging

logger = logging.getLogger(__name__)

# Initialize FastMCP for D365
mcp = FastMCP("Dynamics 365", instructions="Tools for interacting with Microsoft Dynamics 365 CRM")

@mcp.tool()
async def d365_get_accounts() -> str:
    """
    Fetch top 5 accounts from Dynamics 365.
    Returns basic details like name, account number, phone, and city.
    """
    client = D365Client()
    import json
    try:
        accounts = await client.get_accounts()
        return json.dumps(accounts)
    except Exception as e:
        logger.error(f"Error in d365_get_accounts: {str(e)}")
        return f"Error: {str(e)}"
    
@mcp.tool()
async def d365_search_accounts(query: str) -> str:
    """
    Search for accounts in Dynamics 365 by name.
    """
    client = D365Client()
    import json
    try:
        accounts = await client.search_accounts(query)
        if not accounts:
            return f"No accounts found matching '{query}'."
        return json.dumps(accounts)
    except Exception as e:
        return f"Search failed: {str(e)}"

@mcp.tool()
async def search_clients(query: str) -> str:
    """
    Alias for searching D365 accounts/clients by name.
    """
    return await d365_search_accounts(query)

@mcp.tool()
async def d365_get_opportunities() -> str:
    """
    Fetch the most recent sales opportunities from Dynamics 365.
    """
    client = D365Client()
    import json
    try:
        opps = await client.get_opportunities()
        if not opps:
            return "No recent opportunities found."
        return json.dumps(opps)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def list_opportunities() -> str:
    """
    Alias for listing recent sales opportunities.
    """
    return await d365_get_opportunities()

# Add a Resource to the original FastMCP server
@mcp.resource("d365://config/option-sets")
def get_option_sets_resource() -> str:
    """Provides a list of available option sets in the D365 environment."""
    return "Industry, Relationship_Type, Category, Sales_Team, Sales_Stage, Forecast_Stage"

# Add a Prompt to the original FastMCP server
@mcp.prompt("generate-account-summary")
def account_summary_prompt(account_name: str) -> str:
    """Generates a summary of a specific account for a sales meeting."""
    return f"Please summarize the D365 account details for '{account_name}' and highlight any recent opportunities."

@mcp.tool()
async def d365_resolve_lookup(entity: str, search_field: str, value: str) -> str:
    """
    Find the ID of a record in D365 using fuzzy search.
    
    Args:
        entity: The D365 entity name (e.g., 'accounts', 'contacts', 'systemusers')
        search_field: The field to search in (e.g., 'name', 'emailaddress1', 'domainname')
        value: The string value to search for.
    """
    client = D365Client()
    try:
        entity_id = await client.resolve_lookup(entity, search_field, value)
        return f"Resolved {entity}.{search_field} '{value}' to ID: {entity_id}"
    except Exception as e:
        return f"Failed to resolve lookup: {str(e)}"

@mcp.tool()
async def d365_create_account(
    name: str,
    Industry: str,
    Relationship_Type: str,
    Category: str,
    zip_code: str,
    owner_email: str = ""
) -> str:
    """
    Create a new Account record in Dynamics 365.
    
    Args:
        name: Account Name
        Industry: Industry (e.g., 'Consulting', 'Financial')
        Relationship_Type: Type (e.g., 'Customer', 'Prospect')
        Category: Category (e.g., 'Standard', 'Preferred')
        zip_code: Postal Code
        owner_email: Email of the owner user (optional)
    """
    client = D365Client()
    try:
        data = AccountInput(
            name=name,
            industry=Industry,
            relationship_type=Relationship_Type,
            category=Category,
            zip=zip_code,
            owner=owner_email
        )
        response = await client.create_account(data)
        return f"Successfully created account: {response}"
    except Exception as e:
        return f"Error creating account: {str(e)}"

@mcp.tool()
async def d365_create_opportunity(
    name: str,
    potential_customer_name: str,
    sales_team: str,
    sales_stage: str,
    forecast_stage: str,
    estimated_close_date: str,
    lead_source: str,
    owner_email: str = "",
    primary_contact_email: str = ""
) -> str:
    """
    Create a new Opportunity in Dynamics 365.
    
    Args:
        name: Opportunity Name
        potential_customer_name: Name of the existing Account to link.
        sales_team: Sales Team (choice)
        sales_stage: Sales Stage (choice)
        forecast_stage: Forecast Stage (choice)
        estimated_close_date: Date (YYYY-MM-DD)
        lead_source: How the lead was found.
    """
    client = D365Client()
    try:
        data = OpportunityInput(
            name=name,
            oppty_potential_customer_name=potential_customer_name,
            oppty_primary_contact_email=primary_contact_email,
            oppty_owner_email=owner_email,
            oppty_partner_email="", # Default
            sales_team=sales_team,
            sales_stage=sales_stage,
            forecast_stage=forecast_stage,
            estimated_close_date=estimated_close_date,
            lead_source=lead_source,
            lead_source_details="Created via MCP"
        )
        response = await client.create_opportunity(data)
        return f"Successfully created opportunity: {response}"
    except Exception as e:
        return f"Error creating opportunity: {str(e)}"

@mcp.tool()
async def d365_deep_insert(payload: dict) -> str:
    """
    Advanced: Create Account, Contact, and Opportunity in a single atomic transaction.
    This is useful for complete "onboarding" flows.
    The payload should follow the structure expected by D365Client.create_deep_insert.
    """
    client = D365Client()
    try:
        # We parse the dict into the DeepInsertInput model
        data = DeepInsertInput(**payload)
        response = await client.create_deep_insert(data)
        return f"Deep insert successful: {response}"
    except Exception as e:
        return f"Deep insert failed: {str(e)}"
