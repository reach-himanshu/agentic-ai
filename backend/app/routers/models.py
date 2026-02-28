from fastapi import APIRouter
import os
import json
import httpx
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(tags=["models"])

class ModelInfoResponse(BaseModel):
    id: str
    name: str
    provider: str
    available: bool

@router.get("/", response_model=List[ModelInfoResponse])
async def list_models():
    """List available LLM models with availability check."""
    models_json = os.getenv("LLM_MODELS_JSON")
    models = []
    
    if models_json:
        try:
            models = json.loads(models_json)
        except:
            pass
            
    if not models:
        # Defaults
        models = [
            {
                "id": "azure-openai",
                "name": "Azure OpenAI (gpt-4o-mini)",
                "provider": "azure",
                "base_url": os.getenv("AZURE_OPENAI_ENDPOINT")
            },
            {
                "id": "local-phi",
                "name": "LM Studio (Phi-4)",
                "provider": "local",
                "base_url": os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:1234/v1")
            }
        ]
        
    results = []
    async with httpx.AsyncClient(timeout=1.0) as client:
        for m in models:
            available = True
            if m.get("provider") == "local":
                try:
                    res = await client.get(f"{m['base_url']}/models")
                    available = res.status_code == 200
                except:
                    available = False
            
            results.append(ModelInfoResponse(
                id=m["id"],
                name=m["name"],
                provider=m["provider"],
                available=available
            ))
            
    return results
