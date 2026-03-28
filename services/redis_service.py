"""
Redis service for FireFeed API

This module provides Redis client management and utility functions
specific to the API service.
"""

import redis
from typing import Optional, Dict, Any, Union
from config.redis_config import RedisConfig
from config.environment import get_environment


class RedisService:
    """Redis service for FireFeed API"""
    
    def __init__(self, config: Optional[RedisConfig] = None):
        """
        Initialize Redis service
        
        Args:
            config: Redis configuration
        """
        self.config = config or RedisConfig.from_env()
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[redis.ConnectionPool] = None
    
    def get_client(self) -> redis.Redis:
        """
        Get Redis client instance
        
        Returns:
            Redis client instance
        """
        if self._client is None:
            self._client = self._create_client()
        return self._client
    
    def get_pool(self) -> redis.ConnectionPool:
        """
        Get Redis connection pool
        
        Returns:
            Redis connection pool
        """
        if self._pool is None:
            self._pool = self._create_pool()
        return self._pool
    
    def _create_client(self) -> redis.Redis:
        """Create Redis client with configuration"""
        from firefeed_core.config.redis_utils import RedisClientFactory
        
        try:
            client = RedisClientFactory.create_client(self.config)
            
            # Set up logging in development
            if get_environment() == 'development':
                print(f"Redis client created: {self.config}")
            
            return client
            
        except Exception as e:
            raise RuntimeError(f"Failed to create Redis client: {e}")
    
    def _create_pool(self) -> redis.ConnectionPool:
        """Create Redis connection pool with configuration"""
        from firefeed_core.config.redis_utils import RedisClientFactory
        
        try:
            pool = RedisClientFactory.create_pool(self.config)
            return pool
            
        except Exception as e:
            raise RuntimeError(f"Failed to create Redis connection pool: {e}")
    
    def health_check(self) -> Dict[str, Union[bool, str]]:
        """
        Perform Redis health check
        
        Returns:
            Health check result
        """
        from firefeed_core.config.redis_utils import RedisHealthChecker
        
        try:
            client = self.get_client()
            return RedisHealthChecker.check_health(client)
            
        except Exception as e:
            return {
                'status': False,
                'message': f'Redis health check failed: {e}'
            }
    
    def get_cache_key(self, key: str) -> str:
        """Build cache key with prefix"""
        return f"{self.config.cache_prefix}:{key}"
    
    def get_session_key(self, key: str) -> str:
        """Build session key with prefix"""
        return f"{self.config.session_prefix}:{key}"
    
    def get_rate_limit_key(self, key: str) -> str:
        """Build rate limit key with prefix"""
        return f"{self.config.rate_limit_prefix}:{key}"
    
    def close(self):
        """Close Redis connections"""
        if self._client:
            self._client.close()
            self._client = None
        
        if self._pool:
            self._pool.disconnect()
            self._pool = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()