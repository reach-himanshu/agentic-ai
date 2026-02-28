from mcp.server.fastmcp import FastMCP
from integrations.msgraph.service import GraphClient
import logging
import json

mcp = FastMCP("Microsoft Graph")
logger = logging.getLogger(__name__)

@mcp.tool()
async def graph_list_emails(limit: int = 5) -> str:
    """Retrieve the signed-in user's recent emails. Returns a JSON list."""
    async with GraphClient() as client:
        res = await client.list_messages(top=limit)
        messages = res.get("value", [])
        if not messages: return "No recent emails found."
        
        cleaned = []
        for m in messages:
            cleaned.append({
                "subject": m.get("subject"),
                "from": m.get("from", {}).get("emailAddress", {}).get("name"),
                "received": m.get("receivedDateTime"),
                "is_read": m.get("isRead")
            })
        return json.dumps(cleaned)

@mcp.tool()
async def graph_list_events(limit: int = 5) -> str:
    """Retrieve the signed-in user's recent calendar events. Returns a JSON list."""
    async with GraphClient() as client:
        res = await client.list_events(top=limit)
        events = res.get("value", [])
        if not events: return "No recent meetings found."
        
        cleaned = []
        for e in events:
            cleaned.append({
                "subject": e.get("subject"),
                "start": e.get("start", {}).get("dateTime"),
                "end": e.get("end", {}).get("dateTime"),
                "location": e.get("location", {}).get("displayName")
            })
        return json.dumps(cleaned)

@mcp.tool()
async def graph_get_presence() -> str:
    """Get the current availability and activity status of the signed-in user."""
    async with GraphClient() as client:
        res = await client.get_presence()
        availability = res.get("availability")
        activity = res.get("activity")
        return f"Current Presence: {availability} ({activity})"

@mcp.tool()
async def graph_create_meeting(subject: str, start_time: str, end_time: str, location: str = None) -> str:
    """
    Create a new calendar meeting/event.
    :param subject: Title of the meeting.
    :param start_time: ISO 8601 format (e.g. '2026-01-09T10:00:00').
    :param end_time: ISO 8601 format (e.g. '2026-01-09T10:30:00').
    :param location: Optional physical or virtual location.
    """
    async with GraphClient() as client:
        res = await client.create_event(subject, start_time, end_time, location)
        event_id = res.get("id")
        web_link = res.get("webLink")
        return f"Meeting created successfully: **{subject}**. [View in Outlook]({web_link})"

@mcp.tool()
async def graph_search_files(query: str) -> str:
    """Search for files in the user's OneDrive. Returns a JSON list."""
    async with GraphClient() as client:
        res = await client.search_files(query)
        items = res.get("value", [])
        if not items: return f"No files found matching '{query}'."
        
        cleaned = []
        for i in items:
            cleaned.append({
                "name": i.get("name"),
                "link": i.get("webUrl"),
                "last_modified": i.get("lastModifiedDateTime")
            })
        return json.dumps(cleaned)
