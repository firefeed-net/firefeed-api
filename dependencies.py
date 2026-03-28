"""
Dependency injection module for FireFeed API

This module provides dependency injection functions for database
and Redis services used throughout the application.
"""

from typing import AsyncGenerator, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config.environment import get_environment
from .config.database_config import DatabaseConfig
from .config.redis_config import RedisConfig
from .services.database_service import DatabaseService
from .services.redis_service import RedisService
from .models.user import User
from .services.user_service import UserService


# Security scheme
security = HTTPBearer()


async def get_db_service() -> AsyncGenerator[DatabaseService, None]:
    """
    Get database service dependency
    
    Yields:
        DatabaseService instance
    """
    # This will be injected by the lifespan manager
    # For now, we'll create a new instance
    config = DatabaseConfig.from_env()
    service = DatabaseService(config)
    await service.initialize()
    try:
        yield service
    finally:
        await service.close()


def get_redis_service() -> Generator[RedisService, None, None]:
    """
    Get Redis service dependency
    
    Yields:
        RedisService instance
    """
    # This will be injected by the lifespan manager
    # For now, we'll create a new instance
    config = RedisConfig.from_env()
    service = RedisService(config)
    try:
        yield service
    finally:
        service.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_service: DatabaseService = Depends(get_db_service)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        db_service: Database service dependency
        
    Returns:
        User instance
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Validate token and get user
        user_service = UserService(db_service)
        user = await user_service.get_user_by_token(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_cache_service(
    redis_service: RedisService = Depends(get_redis_service)
) -> Generator[RedisService, None, None]:
    """
    Get cache service dependency
    
    Args:
        redis_service: Redis service dependency
        
    Yields:
        RedisService instance configured for caching
    """
    yield redis_service


async def get_session_service(
    redis_service: RedisService = Depends(get_redis_service)
) -> Generator[RedisService, None, None]:
    """
    Get session service dependency
    
    Args:
        redis_service: Redis service dependency
        
    Yields:
        RedisService instance configured for sessions
    """
    yield redis_service


async def get_rate_limit_service(
    redis_service: RedisService = Depends(get_redis_service)
) -> Generator[RedisService, None, None]:
    """
    Get rate limiting service dependency
    
    Args:
        redis_service: Redis service dependency
        
    Yields:
        RedisService instance configured for rate limiting
    """
    yield redis_service


# Development mode dependencies (for testing and debugging)
if get_environment() == "development":
    
    async def get_debug_db_service() -> AsyncGenerator[DatabaseService, None]:
        """
        Get debug database service dependency
        
        This provides additional logging and debugging features
        in development mode.
        """
        config = DatabaseConfig.from_env()
        service = DatabaseService(config)
        await service.initialize()
        
        # Add debug logging
        service.logger.setLevel(logging.DEBUG)
        
        try:
            yield service
        finally:
            await service.close()
    
    def get_debug_redis_service() -> Generator[RedisService, None, None]:
        """
        Get debug Redis service dependency
        
        This provides additional logging and debugging features
        in development mode.
        """
        config = RedisConfig.from_env()
        service = RedisService(config)
        
        # Add debug logging
        service.logger.setLevel(logging.DEBUG)
        
        try:
            yield service
        finally:
            service.close()