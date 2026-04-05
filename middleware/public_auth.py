"""Public authentication middleware for FireFeed API."""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from firefeed_core.auth.token_manager import ServiceTokenManager
from firefeed_core.exceptions import AuthenticationException
from config.environment import settings

logger = logging.getLogger(__name__)

class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[int] = None
    service_id: Optional[str] = None
    scopes: Optional[list] = None

class PublicAuthMiddleware:
    """Middleware for public API authentication."""
    
    def __init__(self, secret_key: str, issuer: str):
        self.token_manager = ServiceTokenManager(secret_key=secret_key, issuer=issuer)
    
    async def authenticate_user_token(self, token: str) -> TokenData:
        """
        Authenticate user JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData with user information
            
        Raises:
            AuthenticationException: If token is invalid or expired
        """
        try:
            payload = self.token_manager.verify_token(token)
            
            # Check if this is a user token (has user_id)
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationException("Invalid user token: missing user_id")
            
            return TokenData(
                user_id=int(user_id),
                service_id=payload.get("service_id"),
                scopes=payload.get("scopes", [])
            )
            
        except Exception as e:
            logger.error(f"User token authentication failed: {e}")
            raise AuthenticationException(f"Invalid user token: {str(e)}")
    
    async def authenticate_service_token(self, token: str) -> TokenData:
        """
        Authenticate service JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData with service information
            
        Raises:
            AuthenticationException: If token is invalid or expired
        """
        try:
            payload = self.token_manager.verify_token(token)
            
            # Check if this is a service token (has service_id)
            service_id = payload.get("service_id")
            if not service_id:
                raise AuthenticationException("Invalid service token: missing service_id")
            
            return TokenData(
                user_id=None,
                service_id=service_id,
                scopes=payload.get("scopes", [])
            )
            
        except Exception as e:
            logger.error(f"Service token authentication failed: {e}")
            raise AuthenticationException(f"Invalid service token: {str(e)}")

class PublicAuthDependency:
    """Dependency for public API authentication."""
    
    def __init__(self, secret_key: str, issuer: str, required: bool = True):
        self.middleware = PublicAuthMiddleware(secret_key, issuer)
        self.required = required
    
    async def __call__(self, request: Request) -> Optional[TokenData]:
        """
        Authenticate request and return token data.

        Args:
            request: FastAPI request object

        Returns:
            TokenData if authentication successful, None if not required and failed

        Raises:
            HTTPException: If authentication is required but failed
        """
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return None

        token = auth_header.split(" ")[1]

        # Determine token type from header or payload and authenticate accordingly
        # Do NOT silently fall back between user and service token authentication
        try:
            # Try user token authentication first
            payload = self.middleware.token_manager.verify_token(token)
            user_id = payload.get("sub")
            service_id = payload.get("service_id")

            if user_id and not service_id:
                # This is a user token
                return TokenData(
                    user_id=int(user_id),
                    service_id=service_id,
                    scopes=payload.get("scopes", [])
                )
            elif service_id and not user_id:
                # This is a service token
                return TokenData(
                    user_id=None,
                    service_id=service_id,
                    scopes=payload.get("scopes", [])
                )
            elif user_id and service_id:
                # Token has both - treat as user token (more restrictive)
                return TokenData(
                    user_id=int(user_id),
                    service_id=service_id,
                    scopes=payload.get("scopes", [])
                )
            else:
                # Token has neither - invalid
                if self.required:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication token: missing user_id and service_id",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                return None

        except HTTPException:
            raise
        except Exception as e:
            if self.required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid authentication token: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            return None

# HTTP Bearer authentication for optional endpoints
class OptionalHTTPBearer(HTTPBearer):
    """Optional HTTP Bearer authentication."""
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Extract credentials without raising exception if missing."""
        try:
            return await super().__call__(request)
        except HTTPException as e:
            if e.status_code == 403:  # No credentials provided
                return None
            raise

# Create authentication dependencies
def create_public_auth_dependency(secret_key: str, issuer: str, required: bool = True):
    """Create public authentication dependency."""
    return PublicAuthDependency(secret_key, issuer, required)

# Default authentication dependencies
public_auth_required = create_public_auth_dependency(
    secret_key=settings.secret_key,
    issuer="firefeed-api",
    required=True
)

public_auth_optional = create_public_auth_dependency(
    secret_key=settings.secret_key,
    issuer="firefeed-api",
    required=False
)

# Bearer authentication for optional endpoints
optional_bearer = OptionalHTTPBearer(auto_error=False)