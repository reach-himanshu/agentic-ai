import os
import msal
import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from typing import Optional, Dict
import time

from app.config import get_settings
from fastapi import Request

# Configuration from global settings
settings = get_settings()
TENANT_ID = settings.azure_tenant_id
CLIENT_ID = settings.azure_backend_client_id
CLIENT_SECRET = settings.azure_backend_client_secret
BACKEND_SCOPE = settings.azure_backend_scope

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
DISCOVERY_URL = f"{AUTHORITY}/v2.0/.well-known/openid-configuration"

# Global cache for JWKS and Service Tokens
_jwks_cache: Dict = {"keys": [], "expires_at": 0}
_service_token_cache: Dict[str, Dict] = {} # scope -> {token, expires_at}

# Security dependency
security = HTTPBearer()

async def get_jwks():
    """Fetches and caches Microsoft's public keys for signature validation."""
    global _jwks_cache
    if time.time() < _jwks_cache["expires_at"]:
        return _jwks_cache["keys"]

    async with httpx.AsyncClient() as client:
        config_res = await client.get(DISCOVERY_URL)
        jwks_uri = config_res.json().get("jwks_uri")
        jwks_res = await client.get(jwks_uri)
        _jwks_cache["keys"] = jwks_res.json().get("keys", [])
        _jwks_cache["expires_at"] = time.time() + 3600 # Cache for 1 hour
        return _jwks_cache["keys"]

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Validates the bearer token (JWT) from Azure AD.
    Supports a mock bypass mode for local development.
    """
    token = credentials.credentials
    
    # Bypass logic for development
    if settings.azure_use_mock_auth and token == "MOCK_TOKEN":
        print("[Auth] Bypassing Azure AD for MOCK_TOKEN")
        return {
            "name": "Dev User",
            "email": "dev@opsiq.local",
            "roles": ["APP_ROLE_ADMIN", "APP_ROLE_SALES"],
            "mock": True
        }

    print(f"[Auth] Attempting real JWT validation. Mock enabled: {settings.azure_use_mock_auth}, Token: {token[:10]}...")
    try:
        keys = await get_jwks()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        rsa_key = {}
        for key in keys:
            if key["kid"] == kid:
                rsa_key = key
                break
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Public key not found")

        issuer = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
        
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=issuer
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTClaimsError as e:
        raise HTTPException(status_code=401, detail=f"Invalid claims: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

def get_client_credentials_token(scope: str) -> Optional[str]:
    """Acquires a token using the application's own identity (Client Credentials)."""
    global _service_token_cache
    
    # Check cache
    if scope in _service_token_cache:
        if time.time() < _service_token_cache[scope]["expires_at"]:
            return _service_token_cache[scope]["token"]

    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )

    result = app.acquire_token_for_client(scopes=[scope])

    if "access_token" in result:
        # Cache for just under the expiry time
        expires_in = result.get("expires_in", 3600)
        _service_token_cache[scope] = {
            "token": result["access_token"],
            "expires_at": time.time() + expires_in - 60
        }
        return result["access_token"]
    else:
        print(f"Client Cred Error: {result.get('error')}, {result.get('error_description')}")
        return None

def get_service_token(request: Request, user_assertion: str, scope: str) -> Optional[str]:
    """
    Dynamically picks between OBO and Client Credentials based on request header.
    """
    flow = request.headers.get("X-OpsIQ-Auth-Flow", settings.default_azure_auth_flow)
    
    if flow == "OBO":
        print(f"[Auth] Attempting OBO flow for scope: {scope}")
        token = get_obo_token(user_assertion, scope)
        if token:
            return token
        print("[Auth] OBO failed, falling back to Client Credentials")

    # Default to Client Credentials if OBO fails or is not explicitly requested
    return get_client_credentials_token(scope)

def get_obo_token(user_assertion: str, scope: str) -> Optional[str]:
    """
    Exchanges a user's access token for a service-specific token using OBO flow.
    """
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )

    result = app.acquire_token_on_behalf_of(
        user_assertion=user_assertion,
        scopes=[scope]
    )

    if "access_token" in result:
        return result["access_token"]
    else:
        print(f"OBO Error: {result.get('error')}, {result.get('error_description')}")
        return None
