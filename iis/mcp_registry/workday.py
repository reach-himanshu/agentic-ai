from mcp.server.fastmcp import FastMCP
from integrations.workday.service import WorkdayClient
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Initialize FastMCP for Workday
mcp = FastMCP("Workday", instructions="Tools for interacting with Workday ERP (Customer Accounts and Staffing)")

@mcp.tool()
async def workday_get_customer_accounts() -> str:
    """
    Fetch top 10 customer accounts from Workday.
    """
    client = WorkdayClient()
    try:
        import json
        data = await client.get_customer_accounts()
        await client.close()
        return json.dumps(data)
    except Exception as e:
        logger.error(f"Error in workday_get_customer_accounts: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
async def workday_get_workers(search: Optional[str] = None) -> str:
    """
    Fetch workers from Workday Staffing API.
    
    Args:
        search: Optional search term for worker name or ID.
    """
    client = WorkdayClient()
    try:
        import json
        data = await client.get_workers(search=search)
        await client.close()
        return json.dumps(data)
    except Exception as e:
        logger.error(f"Error in workday_get_workers: {str(e)}")
        return f"Error: {str(e)}"

@mcp.resource("workday://config/api-urls")
def get_workday_config_resource() -> str:
    """Provides the Workday API base URLs used by this integration."""
    from integrations.workday.config import workday_settings
    return f"Customer Accounts API: {workday_settings.WORKDAY_API_URL}\nStaffing API: {workday_settings.WORKDAY_STAFFING_URL}"
