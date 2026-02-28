from abc import ABC, abstractmethod
from typing import Optional, Dict

class BaseAuth(ABC):
    def __init__(self, client_id: str, client_secret: str, token_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self._token: Optional[str] = None

    @abstractmethod
    async def get_token(self) -> str:
        """Retrieve or refresh the access token."""
        pass

    @abstractmethod
    async def authenticate_request(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject authentication headers into the request."""
        pass
