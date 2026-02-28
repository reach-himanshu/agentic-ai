from fastapi import APIRouter, HTTPException
from .service import WorkdayClient

router = APIRouter()

from .config import workday_settings

@router.get("/customer-accounts")
async def get_customer_accounts():
    try:
        client = WorkdayClient()
        data = await client.get_customer_accounts()
        await client.close()
        return data
    except Exception as e:
        url = str(e.request.url) if hasattr(e, "request") else "unknown"
        config_url = workday_settings.WORKDAY_API_URL
        raise HTTPException(status_code=500, detail=f"Error: {e}, URL: {url}, Config: {config_url}")

@router.get("/workers")
async def get_workers(search: str = None):
    try:
        client = WorkdayClient()
        data = await client.get_workers(search=search)
        await client.close()
        return data
    except Exception as e:
        url = str(e.request.url) if hasattr(e, "request") else "unknown"
        raise HTTPException(status_code=500, detail=f"Error: {e}, URL: {url}")
