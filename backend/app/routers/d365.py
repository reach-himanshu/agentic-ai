from fastapi import APIRouter, Depends, Security, Request
from typing import List, Dict, Any
from app.core.security_azure import get_current_user, security
from app.services.d365_service import D365Service

router = APIRouter(prefix="/v1/d365", tags=["Dynamics 365"])
d365_service = D365Service()

@router.get("/accounts")
async def get_d365_accounts(
    request: Request,
    user: dict = Depends(get_current_user),
    credentials: Any = Security(security)
):
    """
    Fetch accounts from Dynamics 365.
    Uses the X-OpsIQ-Auth-Flow header to determine whether to use OBO or Client Credentials.
    """
    user_assertion = credentials.credentials
    accounts = await d365_service.get_accounts(request, user_assertion)
    return {"accounts": accounts}

@router.get("/accounts/search")
async def search_d365_accounts(
    request: Request,
    name: str,
    user: dict = Depends(get_current_user),
    credentials: Any = Security(security)
):
    """
    Search for an account in Dynamics 365.
    """
    user_assertion = credentials.credentials
    account = await d365_service.get_account_by_name(request, user_assertion, name)
    return {"account": account}
