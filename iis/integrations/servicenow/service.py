from core.base_client import BaseHttpClient
from .config import snow_settings
from .auth import ServiceNowAuth

class ServiceNowClient(BaseHttpClient):
    def __init__(self):
        super().__init__(
            base_url=snow_settings.get_api_url,
            auth=ServiceNowAuth(verify=snow_settings.SSL_VERIFY),
            verify=snow_settings.SSL_VERIFY
        )
        self._user_sys_id_cache = {}

    async def get_user_sys_id(self, email: str) -> str | None:
        """Resolve a user's SysID based on their email address."""
        if email in self._user_sys_id_cache:
            return self._user_sys_id_cache[email]
        
        try:
            res = await self.get(f"/now/table/sys_user?sysparm_query=email={email}&sysparm_fields=sys_id&sysparm_limit=1")
            results = res.get("result", [])
            if results:
                sys_id = results[0].get("sys_id")
                self._user_sys_id_cache[email] = sys_id
                return sys_id
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not resolve ServiceNow SysID for {email}: {e}")
        
        return None

    async def get_incidents(self, limit: int = 10):
        # Example endpoint for ServiceNow Table API
        return await self.get(f"/now/table/incident?sysparm_limit={limit}")

    async def create_incident(self, short_description: str, description: str = "", impact: str = "3", urgency: str = "3", caller_email: str = None):
        data = {
            "short_description": short_description,
            "description": description,
            "impact": impact,
            "urgency": urgency
        }
        
        if caller_email:
            caller_sys_id = await self.get_user_sys_id(caller_email)
            if caller_sys_id:
                data["caller_id"] = caller_sys_id

        return await self.post("/now/table/incident", json=data)

    async def update_incident(self, sys_id: str, data: dict):
        return await self.patch(f"/now/table/incident/{sys_id}", json=data)

    async def search_incidents(self, query: str = "", limit: int = 10):
        url = f"/now/table/incident?sysparm_limit={limit}"
        if query:
            url += f"&sysparm_query={query}"
        return await self.get(url)

    async def search_knowledge(self, keywords: str, limit: int = 5):
        # ServiceNow KM API (Note: filter parameter uses keywords)
        return await self.get(f"/sn_km_api/knowledge/articles?filter={keywords}&sysparm_limit={limit}")

    async def get_my_approvals(self):
        # Approvals assigned to current user
        return await self.get("/now/table/sysapproval_approver?sysparm_query=state=requested^approver=javascript:gs.getUserID()")

    async def take_approval_action(self, sys_id: str, state: str, comments: str = None):
        # state should be 'approved' or 'rejected'
        data = {"state": state}
        if comments:
            data["comments"] = comments
        return await self.patch(f"/now/table/sysapproval_approver/{sys_id}", json=data)
