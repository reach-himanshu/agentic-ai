"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App settings
    app_name: str = "AI Agent Backend"
    app_version: str = "0.1.0"
    debug: bool = True
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS settings
    cors_origins: list[str] = [
        "http://localhost:5172",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5172",
        "http://127.0.0.1:5173",
        "tauri://localhost",
    ]
    
    # Auth settings
    jwt_secret: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    
    # Azure AD Settings
    azure_tenant_id: str = "common"
    azure_backend_client_id: str = ""
    azure_backend_client_secret: str = ""
    azure_backend_scope: str = ""
    azure_use_mock_auth: bool = True
    default_azure_auth_flow: str = "CLIENT_CREDENTIALS" # Options: OBO, CLIENT_CREDENTIALS
    # Dynamics 365 Settings
    d365_resource_url: str = "https://org.crm.dynamics.com"
    d365_api_url: str = "https://org.api.crm.dynamics.com/api/data/v9.2"
    d365_mcp_url: str = "http://127.0.0.1:8006/mcp/d365/sse"
    workday_mcp_url: str = "http://127.0.0.1:8006/mcp/workday/sse"
    
    # Mock data settings
    use_mock_data: bool = True
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
