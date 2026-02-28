from typing import Optional
from pydantic_settings import BaseSettings
from config import config as iis_config

class D365Settings(BaseSettings):
    ENTRA_CLIENT_ID: str = iis_config.ENTRA_CLIENT_ID
    ENTRA_CLIENT_SECRET: str = iis_config.ENTRA_CLIENT_SECRET
    ENTRA_TENANT_ID: str = iis_config.ENTRA_TENANT_ID
    D365_RESOURCE_URL: str = iis_config.D365_RESOURCE_URL
    D365_TOKEN_URL: str = iis_config.D365_TOKEN_URL
    D365_TENANT_ID: str = iis_config.D365_TENANT_ID
    D365_SCOPE: str = "" # Computed if empty
    SSL_VERIFY: bool = iis_config.SSL_VERIFY

    class Config:
        extra = "ignore"

d365_settings = D365Settings()
