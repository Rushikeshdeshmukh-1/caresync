"""
Authentication Service for ABHA OAuth 2.0 token validation
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AuthService:
    """Service for ABHA OAuth 2.0 authentication"""
    
    def __init__(self):
        self.abha_token_url = os.getenv(
            "ABHA_TOKEN_URL",
            "https://dev.abdm.gov.in/gateway/v0.5/sessions"
        )
        self.client_id = os.getenv("ABHA_CLIENT_ID", "")
        self.client_secret = os.getenv("ABHA_CLIENT_SECRET", "")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.algorithm = "RS256"
        self.valid_tokens: Dict[str, datetime] = {}  # Cache for demo
    
    def verify_token(self, token: str) -> bool:
        """
        Verify ABHA OAuth 2.0 token
        In production, this would validate against ABHA gateway
        """
        try:
            # For demo purposes, accept tokens that start with "Bearer " or are valid JWT
            if token.startswith("Bearer "):
                token = token[7:]
            
            # For demo mode, accept any non-empty token
            if not token or len(token) < 1:
                return False
            
            # Try JWT validation if it looks like a JWT (has dots)
            if '.' in token and len(token.split('.')) == 3:
                try:
                    # Basic JWT validation (without signature verification for demo)
                    decoded = jwt.decode(
                        token,
                        key="",  # Empty key since we're not verifying signature
                        options={"verify_signature": False}  # In production, verify signature
                    )
                    
                    # Check expiration
                    exp = decoded.get("exp")
                    if exp and datetime.utcnow().timestamp() > exp:
                        return False
                    
                    # Cache valid token
                    self.valid_tokens[token] = datetime.utcnow() + timedelta(hours=1)
                    return True
                except (JWTError, Exception) as e:
                    # Not a valid JWT, but for demo accept it anyway
                    logger.debug(f"Token is not a valid JWT: {str(e)}")
                    pass
            
            # For demo, accept any non-empty token
            # In production, implement proper ABHA token validation
            if token and len(token) > 1:
                self.valid_tokens[token] = datetime.utcnow() + timedelta(hours=1)
                return True
            return False
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return False
    
    async def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token information"""
        try:
            if token.startswith("Bearer "):
                token = token[7:]
            
            # Only try to decode if it looks like a JWT
            if '.' in token and len(token.split('.')) == 3:
                try:
                    decoded = jwt.decode(
                        token,
                        key="",  # Empty key since we're not verifying signature
                        options={"verify_signature": False}
                    )
                    
                    return {
                        "sub": decoded.get("sub"),
                        "iss": decoded.get("iss"),
                        "aud": decoded.get("aud"),
                        "exp": decoded.get("exp"),
                        "iat": decoded.get("iat")
                    }
                except (JWTError, Exception):
                    pass
            
            # Return basic info for non-JWT tokens
            return {
                "token_type": "demo",
                "token_length": len(token)
            }
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return None
    
    async def validate_with_abha(self, token: str) -> bool:
        """
        Validate token with ABHA gateway
        This is the production implementation
        """
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # In production, make actual API call to ABHA gateway
            # response = await self.client.post(
            #     f"{self.abha_token_url}/validate",
            #     headers=headers,
            #     json={"token": token}
            # )
            # return response.status_code == 200
            
            # For demo, use local validation
            return self.verify_token(token)
        except Exception as e:
            logger.error(f"ABHA validation error: {str(e)}")
            return False
