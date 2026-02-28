import httpx
import logging
from typing import List, Dict, Any
from .auth import D365Auth
from core.context import auth_token_ctx

logger = logging.getLogger(__name__)

class D365DiscoveryService:
    """
    Client for the Power Platform Global Discovery Service.
    Allows listing all D365 instances available to the current user.
    """
    DISCOVERY_URL = "https://globaldisco.crm.dynamics.com/api/discovery/v2.0/Instances"
    
    def __init__(self, verify: bool = True):
        self.verify = verify

    async def get_instances(self) -> List[Dict[str, Any]]:
        """
        Fetch all D365 instances for the logged-in user using OBO.
        """
        user_token = auth_token_ctx.get()

        if not user_token:
            logger.warning("[D365Discovery] Discovery requires a user token. Skipping.")
            return []

        # We need an OBO token specifically for the Discovery Service
        discovery_auth = D365Auth(
            verify=self.verify,
            resource_url="https://globaldisco.crm.dynamics.com", # Discovery resource
            # Tenant ID is not strictly needed for global discovery usually, 
            # but we pass the default just in case
        )

        headers = await discovery_auth.authenticate_request({})
        
        async with httpx.AsyncClient(verify=self.verify) as client:
            try:
                logger.info(f"[D365Discovery] Fetching instances from {self.DISCOVERY_URL}")
                response = await client.get(self.DISCOVERY_URL, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Discovery V2 returns a list of instances in 'value'
                instances = data.get("value", [])
                logger.info(f"[D365Discovery] Found {len(instances)} instances.")
                return instances
            except Exception as e:
                logger.error(f"[D365Discovery] Failed to fetch instances: {e}")
                return []
