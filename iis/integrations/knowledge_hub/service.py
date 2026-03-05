import httpx
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

import os

class KnowledgeHubClient:
    """
    Service client for the Armanino Knowledge Hub (Librarian Gateway).
    Encapsulates RAG search and document management.
    """
    
    def __init__(self, base_url: Optional[str] = None, verify: bool = True):
        url = base_url or os.environ.get("LIBRARIAN_URL", "http://127.0.0.1:8001")
        self.base_url = url.rstrip("/")
        self.verify = verify

    async def search(self, query: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search the knowledge base for a query."""
        async with httpx.AsyncClient(verify=self.verify) as client:
            try:
                url = f"{self.base_url}/api/v1/search?query={quote(query)}"
                if domain:
                    url += f"&domain={domain}"
                
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
            except Exception as e:
                logger.error(f"[KnowledgeHubClient] Search error: {e}")
                raise

    async def list_domains(self) -> List[str]:
        """List available knowledge domains."""
        async with httpx.AsyncClient(verify=self.verify) as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/meta/domains")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"[KnowledgeHubClient] List domains error: {e}")
                raise

    async def list_partitions(self) -> List[str]:
        """List available knowledge partitions/folders."""
        async with httpx.AsyncClient(verify=self.verify) as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/meta/partitions")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"[KnowledgeHubClient] List partitions error: {e}")
                raise

    async def get_source_content(self, source_name: str) -> Dict[str, Any]:
        """Retrieve the full consolidated text of a document."""
        async with httpx.AsyncClient(verify=self.verify) as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/documents/{quote(source_name)}/content")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"[KnowledgeHubClient] Get content error for {source_name}: {e}")
                raise

    async def update_metadata(self, source_name: str, domain: Optional[str] = None, partition: Optional[str] = None) -> str:
        """Update document metadata."""
        async with httpx.AsyncClient(verify=self.verify) as client:
            try:
                payload = {}
                if domain: payload["domain"] = domain
                if partition: payload["partition"] = partition
                
                if not payload:
                    return "No changes provided."

                response = await client.patch(
                    f"{self.base_url}/api/v1/documents/{quote(source_name)}/metadata",
                    json=payload
                )
                response.raise_for_status()
                return response.json().get("message", "Document updated.")
            except Exception as e:
                logger.error(f"[KnowledgeHubClient] Update metadata error: {e}")
                raise
