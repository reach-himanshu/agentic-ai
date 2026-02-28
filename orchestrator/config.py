import os
import json
import httpx
from typing import List, Optional
from pydantic import BaseModel
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


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator."""
    
    # WebSocket server
    ws_host: str = "0.0.0.0"
    ws_port: int = 8001
    
    # Backend API
    backend_url: str = "http://localhost:8000"

    # LLM Models
    models: List[ModelDefinition] = []

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
            # Azure Default
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
            
            # Local Default
            self.models.append(ModelDefinition(
                id="local-phi",
                name="Local LLM (Phi-4)",
                provider="local",
                model_name=os.getenv("LOCAL_LL_MODEL_NAME", "microsoft/phi-4-mini-reasoning"),
                base_url=os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:1234/v1")
            ))

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

    def get_model(self, model_id: str) -> Optional[ModelDefinition]:
        """Get a model definition by ID."""
        for m in self.models:
            if m.id == model_id:
                return m
        return self.models[0] if self.models else None

    # Agent settings
    default_model: str = "gpt-4o"
    max_tool_retries: int = 3
    
    # CORS origins for WebSocket
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "tauri://localhost",
    ]


config = OrchestratorConfig()
