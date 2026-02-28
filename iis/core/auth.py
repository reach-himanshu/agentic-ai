import httpx
import time
import logging
from typing import Dict, Optional
from .base_auth import BaseAuth

logger = logging.getLogger(__name__)

class ClientCredentialsAuth(BaseAuth):
    def __init__(self, client_id: str, client_secret: str, token_url: str, scope: Optional[str] = None, verify: bool = True):
        super().__init__(client_id, client_secret, token_url)
        self.scope = scope
        self.verify = verify
        self._token_expires_at = 0

    async def get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token

        async with httpx.AsyncClient(verify=self.verify) as client:
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            if self.scope:
                payload["scope"] = self.scope

            response = await client.post(self.token_url, data=payload)
            response.raise_for_status()
            data = response.json()
            
            self._token = data["access_token"]
            # Set expiration slightly before actual expiry to be safe
            self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
            
            return self._token

    async def authenticate_request(self, headers: Dict[str, str]) -> Dict[str, str]:
        token = await self.get_token()
        headers["Authorization"] = f"Bearer {token}"
        return headers

class AuthorizationCodeAuth(BaseAuth):
    def __init__(self, client_id: str, client_secret: str, token_url: str, refresh_token: str, verify: bool = True):
        super().__init__(client_id, client_secret, token_url)
        self.refresh_token = refresh_token
        self.verify = verify
        self._token_expires_at = 0

    async def get_token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token
            
        # If we have a refresh token, use it to get a new access token
        async with httpx.AsyncClient(verify=self.verify) as client:
            payload = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token
            }
            
            response = await client.post(self.token_url, data=payload)
            response.raise_for_status()
            data = response.json()
            
            self._token = data["access_token"]
            # Update refresh token if provided in response
            if "refresh_token" in data:
                self.refresh_token = data["refresh_token"]
                
            self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
            
            return self._token

    async def authenticate_request(self, headers: Dict[str, str]) -> Dict[str, str]:
        token = await self.get_token()
        headers["Authorization"] = f"Bearer {token}"
        return headers

class OnBehalfOfAuth(BaseAuth):
    """
    Implements the OAuth 2.0 On-Behalf-Of (OBO) flow.
    Exchanges a user's incoming access token for a token for a downstream resource.
    """
    def __init__(self, client_id: str, client_secret: str, token_url: str, assertion: str, scope: str, verify: bool = True, tenant_id: Optional[str] = None):
        # If a specific tenant_id is provided, ensure the token_url targets that tenant
        # Security: Use proper URL parsing instead of substring matching
        if tenant_id:
            from urllib.parse import urlparse
            parsed = urlparse(token_url)
            if parsed.netloc == "login.microsoftonline.com":
                token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            
        super().__init__(client_id, client_secret, token_url)
        self.assertion = assertion
        self.scope = scope
        self.verify = verify
        self.tenant_id = tenant_id  # Store for later if needed
        self._token_expires_at = 0

    async def get_token(self) -> str:
        # Check cache (Note: in OBO, tokens are specific to the assertion/user)
        if self._token and time.time() < self._token_expires_at:
            return self._token

        # Robust mock token detection (handle case, whitespace, and substrings)
        assertion_val = self.assertion.strip() if self.assertion else ""
        assertion_upper = assertion_val.upper()
        
        if "MOCK" in assertion_upper:
            logger.info(f"[OBO] Mock token detected (starts with '{assertion_val[:10]}...', length {len(assertion_val)}). Returning mock-obo-token for local testing.")
            return "mock-obo-token"

        # Diagnostic: Try to extract audience from JWT without external libs for quick debugging
        try:
            import base64
            import json
            parts = assertion_val.split('.')
            if len(parts) >= 2:
                payload_b64 = parts[1]
                # Fix padding
                payload_b64 += '=' * (-len(payload_b64) % 4)
                payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
                aud = payload.get('aud')
                appid = payload.get('appid') or payload.get('azp')
                scp = payload.get('scp') or payload.get('roles')
                ver = payload.get('ver')
                logger.info(f"[OBO] Exchange started for client '{self.client_id}'. Incoming Token - Aud: {aud}, AppID: {appid}, Scopes: {scp}, Ver: {ver}")
        except Exception as e:
            logger.warning(f"[OBO] Could not parse assertion for diagnostics: {e}")

        logger.info(f"[OBO] Exchange payload details: Assertion starts with '{assertion_val[:10]}...', length {len(assertion_val)}")

        async with httpx.AsyncClient(verify=self.verify) as client:
            payload = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "assertion": self.assertion,
                "scope": self.scope,
                "requested_token_use": "on_behalf_of",
            }

            try:
                response = await client.post(self.token_url, data=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    logger.error(f"[OBO] 400 Bad Request from token endpoint. This usually means the assertion (user token) is invalid, expired, or a mock token. Response: {e.response.text}")
                    raise Exception(f"OAuth OBO flow failed (400 Bad Request). A real Entra ID user token is required for this operation. Is this a mock login? Response: {e.response.text}") from e
                raise
            
            data = response.json()
            
            self._token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
            
            return self._token

    async def authenticate_request(self, headers: Dict[str, str]) -> Dict[str, str]:
        token = await self.get_token()
        headers["Authorization"] = f"Bearer {token}"
        return headers
