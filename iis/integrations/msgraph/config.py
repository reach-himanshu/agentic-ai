from pydantic_settings import BaseSettings
import os
from config import config as iis_config

class GraphSettings(BaseSettings):
    ENTRA_CLIENT_ID: str = iis_config.ENTRA_CLIENT_ID
    ENTRA_CLIENT_SECRET: str = iis_config.ENTRA_CLIENT_SECRET
    ENTRA_TENANT_ID: str = iis_config.ENTRA_TENANT_ID
    GRAPH_RESOURCE_URL: str = os.getenv("GRAPH_RESOURCE_URL", "https://graph.microsoft.com")
    SSL_VERIFY: bool = iis_config.SSL_VERIFY

    @property
    def get_token_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.ENTRA_TENANT_ID}/oauth2/v2.0/token"

    @property
    def get_api_url(self) -> str:
        return f"{self.GRAPH_RESOURCE_URL}/v1.0"

graph_settings = GraphSettings()
