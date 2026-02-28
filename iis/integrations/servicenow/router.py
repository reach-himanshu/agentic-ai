from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
import httpx
from datetime import datetime, timedelta
from urllib.parse import urlencode
import logging

from .service import ServiceNowClient
from .config import snow_settings
from core.database import get_db, UserCredential
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/auth/login")
async def snow_auth_login(user_email: str):
    """
    Generates the ServiceNow OAuth URL and redirects the user.
    Security: Only redirects to configured ServiceNow instance on service-now.com domain.
    Uses cryptographic state token to prevent user input in redirect URL.
    """
    import re
    import hmac
    import hashlib
    import base64
    import time
    
    # Validate user_email format
    if not user_email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user_email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Security: Validate ServiceNow instance configuration
    instance = snow_settings.SNOW_INSTANCE
    if not instance:
        raise HTTPException(status_code=500, detail="ServiceNow instance not configured")
    
    # Strict validation: only allow alphanumeric and hyphens
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', instance):
        raise HTTPException(status_code=500, detail="Invalid ServiceNow instance configuration")
    
    # Generate cryptographically signed state token
    # Format: base64(email:timestamp:hmac)
    timestamp = str(int(time.time()))
    # Use client_secret as HMAC key (server-side secret)
    secret_key = (snow_settings.SNOW_CLIENT_SECRET or "default-secret-key").encode()
    message = f"{user_email}:{timestamp}".encode()
    signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()[:16]
    state_token = base64.urlsafe_b64encode(f"{user_email}:{timestamp}:{signature}".encode()).decode()
    
    params = {
        "response_type": "code",
        "client_id": snow_settings.SNOW_CLIENT_ID,
        "redirect_uri": snow_settings.SNOW_REDIRECT_URI,
        "state": state_token  # Cryptographically signed, not raw user input
    }
    
    # SECURITY: Hardcoded domain - only redirects to service-now.com
    auth_url = f"https://{instance}.service-now.com/oauth_auth.do?{urlencode(params)}"
    return RedirectResponse(auth_url)

@router.get("/auth/callback")
async def snow_auth_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """
    Handles the ServiceNow OAuth callback, exchanges code for tokens, and persists them.
    Validates cryptographic state token before processing.
    """
    import hmac
    import hashlib
    import base64
    import time
    
    # Validate and decode state token
    try:
        decoded = base64.urlsafe_b64decode(state.encode()).decode()
        parts = decoded.split(":")
        if len(parts) != 3:
            raise HTTPException(status_code=400, detail="Invalid state token format")
        
        user_email, timestamp, signature = parts
        
        # Verify HMAC signature
        secret_key = (snow_settings.SNOW_CLIENT_SECRET or "default-secret-key").encode()
        message = f"{user_email}:{timestamp}".encode()
        expected_sig = hmac.new(secret_key, message, hashlib.sha256).hexdigest()[:16]
        
        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(status_code=400, detail="Invalid state token signature")
        
        # Check token expiry (15 minutes max)
        token_time = int(timestamp)
        if time.time() - token_time > 900:  # 15 minutes
            raise HTTPException(status_code=400, detail="State token expired")
            
    except (ValueError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail="Malformed state token")
    
    # Exchange code for tokens
    token_url = snow_settings.get_token_url
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": snow_settings.SNOW_REDIRECT_URI,
        "client_id": snow_settings.SNOW_CLIENT_ID,
        "client_secret": snow_settings.SNOW_CLIENT_SECRET
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    async with httpx.AsyncClient(verify=snow_settings.SSL_VERIFY) as client:
        res = await client.post(token_url, data=data, headers=headers)
        if res.status_code != 200:
            logger.error(f"[SnowAuth] Token exchange failed: {res.text}")
            raise HTTPException(status_code=400, detail="Token exchange failed.")
        
        tokens = res.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 3600)
        
        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))
        
        # Persist/Update record in DB
        stmt = select(UserCredential).where(
            UserCredential.service_name == "servicenow",
            UserCredential.user_email == user_email
        )
        result = await db.execute(stmt)
        cred = result.scalar_one_or_none()
        
        if cred:
            cred.access_token = access_token
            cred.refresh_token = refresh_token
            cred.expires_at = expires_at
        else:
            cred = UserCredential(
                service_name="servicenow",
                user_email=user_email,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
            db.add(cred)
            
        await db.commit()
        
        # Return a small HTML page that signals success to the opener window and closes itself
        success_html = """
        <html>
            <body>
                <script>
                    if (window.opener) {
                        window.opener.postMessage({ type: "snow_auth_success" }, "*");
                        window.close();
                    } else {
                        document.body.innerHTML = "<h1>Authentication Successful</h1><p>You can now close this window and return to the chat.</p>";
                    }
                </script>
                <h1>Authentication Successful</h1>
                <p>Connecting you back to Ops IQ...</p>
            </body>
        </html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=success_html)

@router.get("/incidents")
async def get_snow_incidents():
    # Keep as is for now, but will eventually need to use the stored tokens
    try:
        client = ServiceNowClient()
        data = await client.get_incidents()
        await client.close()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
