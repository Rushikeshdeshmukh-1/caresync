import os
import httpx
import time
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()

class ICD11Service:
    TOKEN_ENDPOINT = "https://icdaccessmanagement.who.int/connect/token"
    SEARCH_ENDPOINT = "https://id.who.int/icd/release/11/2024-01/mms/search"
    
    def __init__(self):
        self.client_id = os.getenv("ICD11_CLIENT_ID")
        self.client_secret = os.getenv("ICD11_CLIENT_SECRET")
        self.token: Optional[str] = None
        self.token_expiry: float = 0

    async def initialize(self):
        """
        Initialize the service.
        """
        print("ICD11Service initialized.")

    async def get_token(self) -> str:
        """
        Retrieves an OAuth2 access token.
        Reuse the token if it's still valid.
        """
        if self.token and time.time() < self.token_expiry:
            return self.token

        if not self.client_id or not self.client_secret:
            raise ValueError("ICD11_CLIENT_ID and ICD11_CLIENT_SECRET must be set in .env")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_ENDPOINT,
                data={"grant_type": "client_credentials", "scope": "icdapi_access"},
                auth=(self.client_id, self.client_secret),
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            # Set expiry a bit earlier than actual to be safe (e.g., -60 seconds)
            self.token_expiry = time.time() + data["expires_in"] - 60
            return self.token

    async def search_entities(self, query: str) -> Dict[str, Any]:
        """
        Search for ICD-11 entities by query string.
        """
        token = await self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "API-Version": "v2",
            "Accept-Language": "en"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.SEARCH_ENDPOINT,
                params={"q": query, "useKl": "true"}, # useKl=true for better results in some contexts, or remove if standard search
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific entity by its URI or ID.
        Note: entity_id should be the full URI or the specific ID part if the API supports it.
        The search result usually provides the URI.
        """
        token = await self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "API-Version": "v2",
            "Accept-Language": "en"
        }
        
        # If entity_id is not a full URL, construct it (assuming it's an ID)
        # However, search results give full URIs like http://id.who.int/icd/entity/12345
        url = entity_id if entity_id.startswith("http") else f"https://id.who.int/icd/entity/{entity_id}"

        # Ensure HTTPS
        if url.startswith("http://"):
            url = url.replace("http://", "https://", 1)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
