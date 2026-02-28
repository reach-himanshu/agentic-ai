from typing import Optional
from core.auth import ClientCredentialsAuth, OnBehalfOfAuth
from core.context import auth_token_ctx
from .config import d365_settings
import logging

logger = logging.getLogger(__name__)

# Construct token URL for Azure AD
TOKEN_URL = f"https://login.microsoftonline.com/{d365_settings.ENTRA_TENANT_ID}/oauth2/v2.0/token"

class D365Auth(ClientCredentialsAuth):
    def __init__(self, verify: bool = None, resource_url: Optional[str] = None, tenant_id: Optional[str] = None):
        # Determine verify setting: use arg if provided, else falls back to config
        if verify is None:
            verify = d365_settings.SSL_VERIFY
        
        self.verify_val = verify # Store for internal use
        self.resource_url = resource_url or d365_settings.D365_RESOURCE_URL
        self.tenant_id = tenant_id or d365_settings.D365_TENANT_ID
        
        # Construct tenant-specific token URL
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        # Default scope for CC
        scope = d365_settings.D365_SCOPE
        if not scope:
            scope = f"{self.resource_url}/.default"
        
        super().__init__(
            client_id=d365_settings.ENTRA_CLIENT_ID,
            client_secret=d365_settings.ENTRA_CLIENT_SECRET,
            token_url=token_url,
            scope=scope,
            verify=verify
        )

    async def authenticate_request(self, headers: dict) -> dict:
        """
        Enforces On-Behalf-Of (OBO) authentication for Dynamics 365.
        Automatically uses OBO if a user token is present in the context.
        """
        user_token = auth_token_ctx.get()

        if user_token:
            logger.info("[D365Auth] Using On-Behalf-Of (OBO) flow")
            # Create a temporary OBO auth object
            obo = OnBehalfOfAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                token_url=self.token_url,
                assertion=user_token,
                scope=self.scope,
                verify=self.verify_val,
                tenant_id=self.tenant_id
            )
            return await obo.authenticate_request(headers)
        
        # OBO is mandatory for D365 actions when logged in
        error_msg = "[D365Auth] Authentication Failed: A real Entra ID user token is required for Dynamics 365 actions. Please ensure you are logged in with a real account."
        logger.error(error_msg)
        raise ValueError(error_msg)
