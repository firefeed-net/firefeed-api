"""
Authentication utilities for FireFeed Internal API

This module provides authentication utilities for internal API endpoints
and service-to-service communication.
"""

import hmac
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from collections import OrderedDict
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import logging

from .models import ServiceTokenResponse, ServiceAuthResponse
from .config import get_settings

logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()

# HTTP Bearer authentication scheme
security = HTTPBearer()

# Service tokens cache with max size (LRU cache)
# Use threading.RLock for thread-safe synchronous access
_MAX_CACHE_SIZE = 1000
_service_tokens: OrderedDict[str, Dict[str, Any]] = OrderedDict()
_cache_lock = threading.RLock()


def _add_to_cache(token: str, data: Dict[str, Any]) -> None:
    """Add token to LRU cache with eviction (thread-safe, synchronous)."""
    with _cache_lock:
        if token in _service_tokens:
            _service_tokens.move_to_end(token)
        _service_tokens[token] = data
        if len(_service_tokens) > _MAX_CACHE_SIZE:
            _service_tokens.popitem(last=False)


def _cleanup_expired_from_cache() -> None:
    """Remove expired tokens from cache (thread-safe, synchronous)."""
    with _cache_lock:
        current_time = datetime.now(timezone.utc)
        expired = [t for t, info in _service_tokens.items()
                   if info.get("expires_at") and current_time > info["expires_at"]]
        for t in expired:
            del _service_tokens[t]


def create_service_token(
    service_name: str,
    expires_delta: Optional[timedelta] = None
) -> ServiceTokenResponse:
    """
    Create a service authentication token

    Args:
        service_name: Name of the service
        expires_delta: Token expiration time delta

    Returns:
        ServiceTokenResponse with token and metadata
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    # Use numeric timestamps for JWT claims (PyJWT expects int/float)
    payload = {
        "sub": service_name,
        "service_name": service_name,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": "firefeed-api",
        "type": "service"
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    # Cache the token synchronously (no fire-and-forget)
    _add_to_cache(token, {
        "service_name": service_name,
        "expires_at": expire,
        "created_at": now
    })

    logger.info(f"Created service token for {service_name}")

    return ServiceTokenResponse(
        token=token,
        service_name=service_name,
        expires_at=expire.isoformat(),
        created_at=now.isoformat()
    )


def verify_service_token(token: str) -> ServiceAuthResponse:
    """
    Verify a service authentication token

    Args:
        token: JWT token to verify

    Returns:
        ServiceAuthResponse with service information

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Check cache with thread-safe lock
        with _cache_lock:
            if token in _service_tokens:
                cached = _service_tokens[token]
                _service_tokens.move_to_end(token)  # LRU update
                expires_at = cached.get("expires_at")
                now = datetime.now(timezone.utc)
                if expires_at and now > expires_at:
                    del _service_tokens[token]
                else:
                    logger.info(f"Verified service token from cache: {cached.get('service_name')}")
                    return ServiceAuthResponse(
                        service_name=cached.get("service_name"),
                        token_valid=True,
                        expires_at=expires_at.isoformat() if expires_at else None,
                        issued_at=cached.get("created_at").isoformat() if cached.get("created_at") else None
                    )

        # Decode JWT token - PyJWT automatically validates 'exp' and raises ExpiredSignatureError
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp"]}
        )

        # Extract service name from 'sub' claim (or fallback to 'service_name')
        service_name = payload.get("sub") or payload.get("service_name")
        if not service_name:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"}
            )

        expires_at = payload.get("exp")
        issued_at = payload.get("iat")

        logger.info(f"Verified service token for {service_name}")

        return ServiceAuthResponse(
            service_name=service_name,
            token_valid=True,
            expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat() if expires_at else None,
            issued_at=datetime.fromtimestamp(issued_at, tz=timezone.utc).isoformat() if issued_at else None
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_service_from_token(token: str) -> str:
    """
    Get service name from token

    Args:
        token: JWT token

    Returns:
        Service name

    Raises:
        HTTPException: If token is invalid
    """
    auth_response = verify_service_token(token)
    return auth_response.service_name


def is_valid_service_token(token: str) -> bool:
    """
    Check if service token is valid

    Args:
        token: JWT token to check

    Returns:
        True if token is valid, False otherwise
    """
    try:
        verify_service_token(token)
        return True
    except HTTPException:
        return False


async def verify_service_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> ServiceAuthResponse:
    """
    Verify service authentication for internal endpoints

    Args:
        credentials: HTTP authorization credentials

    Returns:
        ServiceAuthResponse with service information

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    # Check if token is the internal API token using constant-time comparison
    if settings.internal_api_token and hmac.compare_digest(token, settings.internal_api_token):
        return ServiceAuthResponse(
            service_name="internal-api",
            token_valid=True,
            expires_at=None,
            issued_at=datetime.now(timezone.utc).isoformat()
        )

    # Verify as JWT token
    return verify_service_token(token)


def cleanup_expired_tokens() -> None:
    """
    Clean up expired tokens from cache (synchronous, thread-safe).
    """
    _cleanup_expired_from_cache()
    with _cache_lock:
        remaining = len(_service_tokens)
    if remaining:
        logger.info(f"Cleaned up expired tokens, {remaining} remaining")


def get_active_service_tokens() -> Dict[str, Dict[str, Any]]:
    """
    Get all active service tokens

    Returns:
        Dictionary of active tokens
    """
    with _cache_lock:
        return _service_tokens.copy()


def revoke_service_token(token: str) -> bool:
    """
    Revoke a service token

    Args:
        token: Token to revoke

    Returns:
        True if token was revoked, False if not found
    """
    with _cache_lock:
        if token in _service_tokens:
            del _service_tokens[token]
            logger.info(f"Revoked service token")
            return True
    return False


def revoke_all_service_tokens() -> int:
    """
    Revoke all service tokens

    Returns:
        Number of tokens revoked
    """
    with _cache_lock:
        count = len(_service_tokens)
        _service_tokens.clear()
    logger.info(f"Revoked {count} service tokens")
    return count


# Service authentication dependency
ServiceAuthDep = Depends(verify_service_auth)
