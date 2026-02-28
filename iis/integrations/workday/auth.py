from core.auth import AuthorizationCodeAuth
from .config import workday_settings

class WorkdayAuth(AuthorizationCodeAuth):
    def __init__(self, verify: bool = True):
        super().__init__(
            client_id=workday_settings.WORKDAY_CLIENT_ID,
            client_secret=workday_settings.WORKDAY_CLIENT_SECRET,
            token_url=workday_settings.WORKDAY_TOKEN_URL,
            refresh_token=workday_settings.WORKDAY_REFRESH_TOKEN,
            verify=verify
        )
