from core.base_client import BaseHttpClient
from .config import graph_settings
from core.auth import OnBehalfOfAuth
from core.context import auth_token_ctx
from typing import Optional, List, Any
import logging

logger = logging.getLogger(__name__)

class GraphClient(BaseHttpClient):
    def __init__(self):
        # We start with None auth because we need to dynamically create OBO auth per request/session
        super().__init__(
            base_url=graph_settings.get_api_url,
            auth=None, 
            verify=graph_settings.SSL_VERIFY
        )

    async def _get_headers(self) -> dict:
        """Inject OBO token into headers."""
        headers = {"Content-Type": "application/json"}
        user_token = auth_token_ctx.get()
        
        if user_token:
            # Dynamically create OBO auth for the Graph resource
            obo_auth = OnBehalfOfAuth(
                client_id=graph_settings.ENTRA_CLIENT_ID,
                client_secret=graph_settings.ENTRA_CLIENT_SECRET,
                token_url=graph_settings.get_token_url,
                assertion=user_token,
                scope="https://graph.microsoft.com/.default",
                verify=graph_settings.SSL_VERIFY
            )
            headers = await obo_auth.authenticate_request(headers)
        else:
            error_msg = "[GraphClient] Authentication Failed: A real Entra ID user token is required for M365 actions. Please ensure you are logged in."
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        return headers

    async def get(self, endpoint: str, params: Optional[dict] = None, **kwargs) -> Any:
        headers = await self._get_headers()
        token = headers.get("Authorization", "").replace("Bearer ", "")
        
        return await super().get(endpoint, params, **kwargs)

    async def post(self, endpoint: str, json: Optional[dict] = None, **kwargs) -> Any:
        return await super().post(endpoint, json, **kwargs)

    async def list_messages(self, top: int = 5):
        """List current user's recent emails."""
        return await self.get(f"/me/messages?$top={top}&$select=subject,from,receivedDateTime,webLink,isRead")

    async def list_events(self, top: int = 5):
        """List current user's calendar events."""
        return await self.get(f"/me/events?$top={top}&$select=subject,start,end,location,webLink")

    async def send_mail(self, to_email: str, subject: str, content: str):
        """Send an email on behalf of the user."""
        payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "Text",
                    "content": content
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ]
            }
        }
        return await self.post("/me/sendMail", json=payload)

    async def get_presence(self):
        """Get current user's presence/status."""
        return await self.get("/me/presence")

    async def create_event(self, subject: str, start_time: str, end_time: str, location: str = None):
        """Create a calendar event."""
        payload = {
            "subject": subject,
            "start": {
                "dateTime": start_time,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "UTC"
            }
        }
        if location:
            payload["location"] = {"displayName": location}
            
        return await self.post("/me/events", json=payload)

    async def search_files(self, query: str):
        """Search across OneDrive/SharePoint files."""
        return await self.get(f"/me/drive/root/search(q='{query}')")
