import os
import json
import httpx
from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ModelDefinition(BaseModel):
    """Definition of an LLM model."""
    id: str
    name: str
    provider: str  # 'azure' or 'local'
    model_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_version: Optional[str] = None

class IISConfig(BaseSettings):
    """Configuration for the Integrated Intelligence Service (IIS)."""
    
    # WebSocket & server
    ws_host: str = "0.0.0.0"
    ws_port: int = 8000  # Combined port
    
    # LLM Models
    models: List[ModelDefinition] = []
    default_model: str = "gpt-4o"
    max_tool_retries: int = 3
    
    # CORS origins
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "tauri://localhost",
    ]

    # Entra ID / Microsoft Identity Settings (Service Identity for OBO)
    ENTRA_TENANT_ID: str = os.getenv("ENTRA_TENANT_ID", "5e8a5341-629d-4421-9dbf-f5a5224ce6e7")
    ENTRA_CLIENT_ID: str = os.getenv("ENTRA_CLIENT_ID", "ee68bfbc-80e4-4914-bef1-eca6337764b6")
    ENTRA_CLIENT_SECRET: str = os.getenv("ENTRA_CLIENT_SECRET", "")
    
    # BOML / External Integration Settings
    D365_RESOURCE_URL: str = os.getenv("D365_RESOURCE_URL", "")
    D365_TOKEN_URL: str = os.getenv("D365_TOKEN_URL", "")
    D365_TENANT_ID: str = os.getenv("D365_TENANT_ID", ENTRA_TENANT_ID)
    
    WORKDAY_BASE_URL: str = os.getenv("WORKDAY_BASE_URL", "")
    WORKDAY_CLIENT_ID: str = os.getenv("WORKDAY_CLIENT_ID", "")
    WORKDAY_CLIENT_SECRET: str = os.getenv("WORKDAY_CLIENT_SECRET", "")
    WORKDAY_TOKEN_URL: str = os.getenv("WORKDAY_TOKEN_URL", "")
    
    SERVICENOW_BASE_URL: str = os.getenv("SERVICENOW_BASE_URL", "")
    
    # Microsoft Graph Settings (OBO)
    GRAPH_RESOURCE_URL: str = os.getenv("GRAPH_RESOURCE_URL", "https://graph.microsoft.com")
    
    # Local LLM Settings (LM Studio / Ollama)
    LOCAL_LLM_ENABLED: bool = os.getenv("LOCAL_LLM_ENABLED", "false").lower() == "true"
    LOCAL_LLM_BASE_URL: str = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
    LOCAL_LLM_MODEL_NAME: str = os.getenv("LOCAL_LLM_MODEL_NAME", "ministral-3-3b")
    LOCAL_LLM_PROVIDER_NAME: str = os.getenv("LOCAL_LLM_PROVIDER_NAME", "LM Studio")
    
    SSL_VERIFY: bool = True

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

    def __init__(self, **data):
        super().__init__(**data)
        self._load_models()

    def _load_models(self):
        """Load models from environment variables."""
        models_json = os.getenv("LLM_MODELS_JSON")
        if models_json:
            try:
                data = json.loads(models_json)
                self.models = [ModelDefinition(**m) for m in data]
            except Exception as e:
                print(f"Error loading LLM_MODELS_JSON: {e}")
        
        # Fallback to single models if JSON is not present or empty
        if not self.models:
            # Azure OpenAI
            if os.getenv("AZURE_OPENAI_ENDPOINT"):
                self.models.append(ModelDefinition(
                    id="azure-openai",
                    name="Azure OpenAI",
                    provider="azure",
                    model_name=os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4o-mini"),
                    base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
                ))
            
            # Regular OpenAI (non-Azure)
            if os.getenv("OPENAI_API_KEY"):
                self.models.append(ModelDefinition(
                    id="openai",
                    name="OpenAI",
                    provider="openai",
                    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                    base_url="https://api.openai.com/v1",
                    api_key=os.getenv("OPENAI_API_KEY")
                ))
                print(f"[Config] OpenAI enabled: {os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')}")
        
        # Local LLM (LM Studio / Ollama) - Add if enabled
        if self.LOCAL_LLM_ENABLED:
            self.models.append(ModelDefinition(
                id="local-llm",
                name=f"Local ({self.LOCAL_LLM_PROVIDER_NAME})",
                provider="local",
                model_name=self.LOCAL_LLM_MODEL_NAME,
                base_url=self.LOCAL_LLM_BASE_URL
            ))
            print(f"[Config] Local LLM enabled: {self.LOCAL_LLM_MODEL_NAME} at {self.LOCAL_LLM_BASE_URL}")

    async def get_available_models(self) -> List[ModelDefinition]:
        """Get models that are currently available (online)."""
        available = []
        for m in self.models:
            if m.provider == "azure":
                available.append(m)
            elif m.provider == "local":
                # Check if local server is up
                try:
                    async with httpx.AsyncClient(timeout=1.0) as client:
                        res = await client.get(f"{m.base_url}/models")
                        if res.status_code == 200:
                            available.append(m)
                except:
                    pass
        return available

    def get_model(self, model_id: str = None) -> Optional[ModelDefinition]:
        """Get a model definition by ID. If no ID, return default based on config."""
        # If specific model requested, find it
        if model_id:
            for m in self.models:
                if m.id == model_id:
                    return m
        
        # If LOCAL_LLM_ENABLED, prefer local model
        if self.LOCAL_LLM_ENABLED:
            for m in self.models:
                if m.provider == "local":
                    return m
        
        # Fallback to first available model
        return self.models[0] if self.models else None

config = IISConfig()
