from typing import List, Dict, Any
from fastapi import Request
from app.services.base_service import BaseService
from app.config import get_settings

settings = get_settings()

class D365Service(BaseService):
    """
    Dynamics 365 CRM Service.
    """
    
    def __init__(self):
        super().__init__(resource_url=settings.d365_api_url)

    async def get_accounts(self, request: Request, user_assertion: str) -> List[Dict[str, Any]]:
        """
        Fetch accounts from D365 CRM.
        """
        # Dataverse OData endpoint for accounts
        response = await self.request(
            request, 
            user_assertion, 
            "GET", 
            "/accounts?$select=name,accountid,address1_city,industrycode"
        )
        return response.get("value", [])

    async def get_account_by_name(self, request: Request, user_assertion: str, name: str) -> Dict[str, Any]:
        """
        Search for an account by name.
        """
        response = await self.request(
            request, 
            user_assertion, 
            "GET", 
            f"/accounts?$filter=contains(name, '{name}')&$select=name,accountid"
        )
        accounts = response.get("value", [])
        return accounts[0] if accounts else None
