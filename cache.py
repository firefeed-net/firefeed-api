"""
Cache management for FireFeed API

This module provides cache management utilities for the application.
"""

import json
import pickle
from typing import Optional, Any, Dict, List, Union
from datetime import datetime, timedelta
from loguru import logger

from redis.asyncio import Redis
from redis.exceptions import RedisError

from .config.environment import get_settings


class CacheService:
    """Cache service for FireFeed API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[Redis] = None
        self.cache_ttl = self.settings.cache_ttl
        self.max_cache_size = self.settings.cache_max_size
    
    async def connect(self) -> None:
        """Connect to Redis cache"""
        try:
            self.redis_client = Redis.from_url(
                self.settings.redis_url,
                decode_responses=False  # Use binary mode for pickle serialization
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis cache successfully")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis cache: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis cache"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except RedisError as e:
            logger.error(f"Failed to get cache value for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Serialize value using pickle
            serialized_value = pickle.dumps(value)
            
            # Use provided TTL or default
            cache_ttl = ttl or self.cache_ttl
            
            await self.redis_client.setex(key, cache_ttl, serialized_value)
            return True
        except RedisError as e:
            logger.error(f"Failed to set cache value for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Failed to delete cache value for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            return await self.redis_client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for cache key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.expire(key, ttl)
            return True
        except RedisError as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """
        Get remaining time to live for cache key
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds, -1 if key doesn't exist, -2 if key has no expiration
        """
        if not self.redis_client:
            return -1
        
        try:
            return await self.redis_client.ttl(key)
        except RedisError as e:
            logger.error(f"Failed to get TTL for cache key {key}: {e}")
            return -1
    
    async def keys(self, pattern: str) -> List[str]:
        """
        Get keys matching pattern
        
        Args:
            pattern: Redis pattern
            
        Returns:
            List of matching keys
        """
        if not self.redis_client:
            return []
        
        try:
            keys = await self.redis_client.keys(pattern)
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except RedisError as e:
            logger.error(f"Failed to get keys for pattern {pattern}: {e}")
            return []
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern
        
        Args:
            pattern: Redis pattern
            
        Returns:
            Number of deleted keys
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = await self.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Failed to delete keys for pattern {pattern}: {e}")
            return 0
    
    async def cleanup_expired(self) -> None:
        """Clean up expired cache entries"""
        try:
            # Redis automatically handles expired keys, but we can force cleanup
            await self.redis_client.flushall()
            logger.info("Cache cleanup completed")
        except RedisError as e:
            logger.error(f"Cache cleanup failed: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "memory_usage": info.get("used_memory_human", "unknown"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
        except RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}


# Global cache service instance
cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """Get cache service instance"""
    return cache_service


# Cache key patterns
USER_CACHE_PATTERN = "user:{user_id}"
RSS_ITEM_CACHE_PATTERN = "rss_item:{rss_item_id}"
RSS_FEED_CACHE_PATTERN = "rss_feed:{feed_id}"
CATEGORY_CACHE_PATTERN = "category:{category_id}"
SOURCE_CACHE_PATTERN = "source:{source_id}"
TRANSLATION_CACHE_PATTERN = "translation:{text_hash}"
MEDIA_CACHE_PATTERN = "media:{media_hash}"
EMAIL_CACHE_PATTERN = "email:{email_hash}"