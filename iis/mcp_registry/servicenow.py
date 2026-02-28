from mcp.server.fastmcp import FastMCP
from integrations.servicenow.service import ServiceNowClient
from core.context import auth_user_ctx
import logging
import json

mcp = FastMCP("ServiceNow")
logger = logging.getLogger(__name__)

# Helper to check if user has ServiceNow credentials
async def _check_snow_credentials() -> str | None:
    """Check if user has ServiceNow OAuth credentials. Returns error message if not, None if OK."""
    from core.database import AsyncSessionLocal, UserCredential
    from sqlalchemy import select, func
    
    user_email = auth_user_ctx.get()
    if not user_email:
        return "❌ No user session found. Please sign in again."
    
    async with AsyncSessionLocal() as db:
        stmt = select(UserCredential).where(
            UserCredential.service_name == "servicenow",
            func.lower(UserCredential.user_email) == func.lower(user_email)
        )
        result = await db.execute(stmt)
        cred = result.scalar_one_or_none()
    
    if not cred:
        login_url = f"http://localhost:8000/api/v1/servicenow/auth/login?user_email={user_email}"
        return f"🔐 You haven't connected your ServiceNow account yet. Please [Connect to ServiceNow]({login_url}) first to use IT Support features."
    
    return None

@mcp.tool()
async def snow_create_incident(description: str, short_description: str = None, impact: str = "3", urgency: str = "3") -> str:
    """
    Create a high-impact incident in ServiceNow.
    :param description: Detailed description of the issue.
    :param short_description: A brief summary (optional, defaults to first line of description).
    :param impact: 1 (High), 2 (Medium), 3 (Low).
    :param urgency: 1 (High), 2 (Medium), 3 (Low).
    """
    # Check credentials first
    auth_error = await _check_snow_credentials()
    if auth_error:
        return auth_error
    
    # Fallback for short_description if not provided
    if not short_description:
        short_description = description.split('\n')[0][:80]
    
    user_email = auth_user_ctx.get()

    async with ServiceNowClient() as client:
        res = await client.create_incident(short_description, description, impact, urgency, caller_email=user_email)
        data = res.get("result", {})
        number = data.get('number')
        sys_id = data.get('sys_id')
        from integrations.servicenow.config import snow_settings
        if not number:
            return f"ServiceNow returned success but no incident number was found. Response: {json.dumps(res)}"
        return f"Incident **{number}** has been successfully created. [Link](https://{snow_settings.SNOW_INSTANCE}.service-now.com/nav_to.do?uri=incident.do?sys_id={sys_id})"

@mcp.tool()
async def snow_search_incidents(query: str = "", limit: int = 5) -> str:
    """
    Search for incidents. Returns a JSON list of incidents.
    """
    # Check credentials first
    auth_error = await _check_snow_credentials()
    if auth_error:
        return auth_error
    
    async with ServiceNowClient() as client:
        res = await client.search_incidents(query, limit)
        results = res.get("result", [])
        if not results: return "No incidents found."
        
        # Return cleaned data for LLM/UI processing
        cleaned = []
        for r in results:
            cleaned.append({
                "number": r.get("number"),
                "short_description": r.get("short_description"),
                "state": r.get("state"),
                "priority": r.get("priority"),
                "sys_id": r.get("sys_id")
            })
        return json.dumps(cleaned)

@mcp.tool()
async def snow_update_incident(sys_id: str, work_notes: str = None, state: str = None) -> str:
    """Update an existing incident with work notes or a new state."""
    auth_error = await _check_snow_credentials()
    if auth_error:
        return auth_error
    
    data = {}
    if work_notes: data["work_notes"] = work_notes
    if state: data["state"] = state
    async with ServiceNowClient() as client:
        await client.update_incident(sys_id, data)
        return "Incident Updated successfully."

@mcp.tool()
async def snow_search_knowledge(keywords: str, limit: int = 3) -> str:
    """Search knowledge base. Returns JSON list."""
    auth_error = await _check_snow_credentials()
    if auth_error:
        return auth_error
    
    async with ServiceNowClient() as client:
        res = await client.search_knowledge(keywords, limit)
        articles = res.get("result", [])
        if not articles: return "No articles found."
        
        cleaned = []
        for a in articles:
            cleaned.append({
                "title": a.get("short_description"),
                "number": a.get("number"),
                "sys_id": a.get("sys_id")
            })
        return json.dumps(cleaned)

@mcp.tool()
async def snow_list_approvals() -> str:
    """List pending approvals. Returns JSON list."""
    auth_error = await _check_snow_credentials()
    if auth_error:
        return auth_error
    
    async with ServiceNowClient() as client:
        res = await client.get_my_approvals()
        results = res.get("result", [])
        if not results: return "You have no pending approvals."
        
        cleaned = []
        for r in results:
            cleaned.append({
                "target": r.get("sysapproval", {}).get("display_value", "Request"),
                "state": r.get("state"),
                "sys_id": r.get("sys_id"),
                "created": r.get("sys_created_on")
            })
        return json.dumps(cleaned)

@mcp.tool()
async def snow_approve_request(sys_id: str, state: str = "approved", comments: str = None) -> str:
    """Approve or Reject a request. state must be 'approved' or 'rejected'."""
    auth_error = await _check_snow_credentials()
    if auth_error:
        return auth_error
    
    async with ServiceNowClient() as client:
        await client.take_approval_action(sys_id, state, comments)
        return f"Approval {state} successfully."
