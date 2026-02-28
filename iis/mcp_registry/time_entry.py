"""Time Entry MCP Tools for Workday time tracking."""
from mcp.server.fastmcp import FastMCP
from core.database import AsyncSessionLocal, TimeEntry
from sqlalchemy import select
import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

mcp = FastMCP("TimeEntry", instructions="Tools for logging and viewing time entries")


def get_week_start(date: datetime) -> datetime:
    """Get Monday of the week for a given date."""
    days_since_monday = date.weekday()
    return (date - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)


@mcp.tool()
async def wd_add_time_entry(
    project_id: Optional[str] = None,
    project_name: Optional[str] = None,
    time_code: Optional[str] = "CONSULT-BILL",
    hours: Optional[str] = None,
    date: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: str = "demo_user",
    # Alternative field names from LLM forms
    number_of_hours: Optional[str] = None,
    project: Optional[str] = None,
) -> str:
    """
    Add a time entry for the user.
    
    Args:
        project_id: The project code (e.g., "ACME-DT-2026")
        project_name: Human-readable project name
        time_code: Time code classification (e.g., "CONSULT-BILL", "FIRM-MTG")
        hours: Number of hours (e.g., "2.5")
        date: Entry date in YYYY-MM-DD format (defaults to today)
        notes: Optional notes about the work done
        user_id: User identifier
    
    Returns:
        JSON confirmation of the created entry
    """
    try:
        # Handle alternative field names from LLM forms
        actual_hours = hours or number_of_hours or "1"
        actual_project_name = project_name or project or project_id or "General"
        actual_project_id = project_id or "GENERAL"
        
        # Parse date or use today
        if date:
            try:
                entry_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                # Try alternate format MM/DD/YYYY
                entry_date = datetime.strptime(date, "%m/%d/%Y").replace(tzinfo=timezone.utc)
        else:
            entry_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        week_start = get_week_start(entry_date)
        
        entry = TimeEntry(
            id=str(uuid.uuid4()),
            user_id=user_id,
            week_start=week_start,
            entry_date=entry_date,
            project_id=actual_project_id,
            project_name=actual_project_name,
            time_code=time_code,
            hours=actual_hours,
            notes=notes,
            status="draft"
        )
        
        async with AsyncSessionLocal() as session:
            session.add(entry)
            await session.commit()
            
            logger.info(f"[TimeEntry] Created entry: {actual_hours}h for {actual_project_name}")
            
            return json.dumps({
                "success": True,
                "entry": {
                    "id": entry.id,
                    "project_name": actual_project_name,
                    "time_code": time_code,
                    "hours": actual_hours,
                    "date": entry_date.strftime("%Y-%m-%d"),
                    "status": "draft"
                },
                "message": f"Added {actual_hours} hours to {actual_project_name}"
            })
            
    except Exception as e:
        logger.error(f"[TimeEntry] Error adding entry: {e}")
        return json.dumps({"success": False, "error": str(e)})


@mcp.tool()
async def wd_get_my_timesheet(
    week_offset: int = 0,
    user_id: str = "demo_user"
) -> str:
    """
    Get the user's timesheet for a specific week.
    
    Args:
        week_offset: 0 for current week, -1 for last week, etc.
        user_id: User identifier
    
    Returns:
        JSON with weekly time entries grouped by project
    """
    try:
        # Calculate week start
        today = datetime.now(timezone.utc)
        target_week = get_week_start(today) + timedelta(weeks=week_offset)
        week_end = target_week + timedelta(days=7)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(TimeEntry)
                .where(TimeEntry.user_id == user_id)
                .where(TimeEntry.week_start >= target_week)
                .where(TimeEntry.week_start < week_end)
                .order_by(TimeEntry.entry_date)
            )
            entries = result.scalars().all()
            
            # Group by project
            projects = {}
            total_hours = 0.0
            
            for entry in entries:
                key = entry.project_id or "INTERNAL"
                if key not in projects:
                    projects[key] = {
                        "project_id": entry.project_id,
                        "project_name": entry.project_name,
                        "entries": [],
                        "total_hours": 0.0
                    }
                
                hours_float = float(entry.hours)
                projects[key]["entries"].append({
                    "id": entry.id,
                    "date": entry.entry_date.strftime("%Y-%m-%d"),
                    "day": entry.entry_date.strftime("%A"),
                    "hours": entry.hours,
                    "time_code": entry.time_code,
                    "notes": entry.notes,
                    "status": entry.status
                })
                projects[key]["total_hours"] += hours_float
                total_hours += hours_float
            
            return json.dumps({
                "week_start": target_week.strftime("%Y-%m-%d"),
                "week_end": (target_week + timedelta(days=4)).strftime("%Y-%m-%d"),
                "projects": list(projects.values()),
                "total_hours": total_hours,
                "status": "draft" if entries else "empty"
            })
            
    except Exception as e:
        logger.error(f"[TimeEntry] Error getting timesheet: {e}")
        return json.dumps({"success": False, "error": str(e)})
