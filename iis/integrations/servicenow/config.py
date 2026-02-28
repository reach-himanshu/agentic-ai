from typing import Optional
from pydantic_settings import BaseSettings
from config import config as iis_config

class ServiceNowSettings(BaseSettings):
    SNOW_CLIENT_ID: Optional[str] = None
    SNOW_CLIENT_SECRET: Optional[str] = None
    SNOW_INSTANCE: Optional[str] = None  # e.g., "dev12345"
    SNOW_TOKEN_URL: str = "" # Auto-computed usually
    SNOW_API_URL: str = ""   # Auto-computed usually
    SNOW_REDIRECT_URI: str = "http://localhost:8000/api/v1/servicenow/auth/callback"
    SSL_VERIFY: bool = iis_config.SSL_VERIFY

    @property
    def get_token_url(self):
        return f"https://{self.SNOW_INSTANCE}.service-now.com/oauth_token.do"

    @property
    def get_api_url(self):
        return f"https://{self.SNOW_INSTANCE}.service-now.com/api"

    class Config:
        env_file = ".env"
        env_prefix = ""
        extra = "ignore"

snow_settings = ServiceNowSettings()
