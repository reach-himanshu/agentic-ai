from typing import Optional
from core.base_client import BaseHttpClient
from .config import workday_settings
from .auth import WorkdayAuth

class WorkdayClient(BaseHttpClient):
    def __init__(self):
        super().__init__(
            base_url=workday_settings.WORKDAY_API_URL,
            auth=WorkdayAuth(verify=workday_settings.SSL_VERIFY),
            verify=workday_settings.SSL_VERIFY
        )

    async def get_customer_accounts(self):
        """
        Fetch customer accounts from Workday.
        Endpoint: /customers
        """
        # Note: The base_url is set to .../customerAccounts/v1, so we append /customers
        return await self.get("customers?$limit=10")

    async def get_workers(self, search: Optional[str] = None):
        """
        Fetch workers from Workday Staffing API.
        Endpoint: /workers
        """
        url = f"{workday_settings.WORKDAY_STAFFING_URL}workers"
        if search:
            url += f"?search={search}"
        return await self.get(url)
