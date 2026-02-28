from core.auth import BaseAuth
from .config import snow_settings
from core.context import auth_user_ctx
from core.database import AsyncSessionLocal, UserCredential
from sqlalchemy import select
from datetime import datetime, timedelta
import httpx
import logging

logger = logging.getLogger(__name__)

class ServiceNowAuth(BaseAuth):
    def __init__(self, verify: bool = True):
        # Pass dummy values for base class properties as they aren't used directy here
        # based on DB-driven token retrieval, but required for instantiation.
        super().__init__(
            client_id=snow_settings.SNOW_CLIENT_ID,
            client_secret=snow_settings.SNOW_CLIENT_SECRET,
            token_url=snow_settings.get_token_url
        )
        self.verify = verify

    async def get_token(self) -> str:
        """
        Retrieves the user's ServiceNow token from the database.
        Performs a silent refresh if the access token has expired.
        """
        user_email = auth_user_ctx.get()
        if not user_email:
            logger.warning("[SnowAuth] No user email in context. Cannot perform user-delegated auth.")
            return ""

        logger.info(f"[SnowAuth] Attempting credential lookup for: {user_email}")
        async with AsyncSessionLocal() as db:
            from sqlalchemy import func
            stmt = select(UserCredential).where(
                UserCredential.service_name == "servicenow",
                func.lower(UserCredential.user_email) == user_email.lower()
            )
            result = await db.execute(stmt)
            cred = result.scalar_one_or_none()

            if not cred:
                logger.info(f"[SnowAuth] No credentials found (case-insensitive) for {user_email}. User must authorize.")
                return ""

            # Check if expired or expiring soon (within 1 minute)
            if cred.expires_at < datetime.utcnow() + timedelta(minutes=1):
                logger.info(f"[SnowAuth] Token expired for {user_email}. Refreshing...")
                await self._refresh_token(cred, db)

            return cred.access_token

    async def authenticate_request(self, headers: dict) -> dict:
        """Inject authentication headers into the request."""
        token = await self.get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _refresh_token(self, cred: UserCredential, db):
        """Perform OAuth2 refresh token exchange."""
        token_url = snow_settings.get_token_url
        data = {
            "grant_type": "refresh_token",
            "refresh_token": cred.refresh_token,
            "client_id": snow_settings.SNOW_CLIENT_ID,
            "client_secret": snow_settings.SNOW_CLIENT_SECRET
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        async with httpx.AsyncClient(verify=self.verify) as client:
            res = await client.post(token_url, data=data, headers=headers)
            if res.status_code != 200:
                logger.error(f"[SnowAuth] Refresh failed for {cred.user_email}: {res.text}")
                # Optional: Clear tokens so user is prompted to re-auth
                return

            tokens = res.json()
            cred.access_token = tokens.get("access_token")
            # ServiceNow usually returns a new refresh token too
            new_refresh = tokens.get("refresh_token")
            if new_refresh:
                cred.refresh_token = new_refresh
                
            expires_in = tokens.get("expires_in", 3600)
            cred.expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
            
            await db.commit()
            logger.info(f"[SnowAuth] Successfully refreshed token for {cred.user_email}")
