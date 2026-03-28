"""
Cache service for FireFeed API

This module provides caching functionality using Redis for the API service.
"""

import json
import pickle
from typing import Optional, Any, Union, List
from datetime import datetime, timedelta
from services.redis_service import RedisService
from config.redis_config import RedisConfig


class CacheService:
    """Cache service for FireFeed API using Redis"""
    
    def __init__(self, redis_service: Optional[RedisService] = None):
        """
        Initialize cache service
        
        Args:
            redis_service: Redis service instance
        """
        self.redis_service = redis_service or RedisService()
        self.config = self.redis_service.config
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            cache_key = self.redis_service.get_cache_key(key)
            value = self.redis_service.get_client().get(cache_key)
            
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then as pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    return pickle.loads(value)
                except pickle.PickleError:
                    return value.decode('utf-8')
                    
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            return None
    
    def set(
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
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self.redis_service.get_cache_key(key)
            ttl = ttl or self.config.cache_ttl
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value).encode('utf-8')
            else:
                serialized_value = pickle.dumps(value)
            
            # Set with TTL
            result = self.redis_service.get_client().setex(
                cache_key,
                ttl,
                serialized_value
            )
            
            return bool(result)
            
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self.redis_service.get_cache_key(key)
            result = self.redis_service.get_client().delete(cache_key)
            return bool(result)
            
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            cache_key = self.redis_service.get_cache_key(key)
            return bool(self.redis_service.get_client().exists(cache_key))
            
        except Exception as e:
            print(f"Cache exists error for key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration for cache key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = self.redis_service.get_cache_key(key)
            result = self.redis_service.get_client().expire(cache_key, ttl)
            return bool(result)
            
        except Exception as e:
            print(f"Cache expire error for key {key}: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for cache key
        
        Args:
            key: Cache key
            
        Returns:
            Remaining TTL in seconds, or -1 if key doesn't exist, -2 if no expiration
        """
        try:
            cache_key = self.redis_service.get_cache_key(key)
            return self.redis_service.get_client().ttl(cache_key)
            
        except Exception as e:
            print(f"Cache TTL error for key {key}: {e}")
            return -1
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear cache keys matching pattern
        
        Args:
            pattern: Redis pattern to match
            
        Returns:
            Number of keys deleted
        """
        try:
            full_pattern = self.redis_service.get_cache_key(pattern)
            keys = self.redis_service.get_client().keys(full_pattern)
            
            if not keys:
                return 0
            
            return self.redis_service.get_client().delete(*keys)
            
        except Exception as e:
            print(f"Cache clear pattern error for pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            client = self.redis_service.get_client()
            info = client.info('memory')
            
            return {
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'connected_clients': info.get('connected_clients', 0)
            }
            
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {}
    
    def flush(self) -> bool:
        """
        Flush all cache data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.redis_service.get_client().flushdb()
            return True
            
        except Exception as e:
            print(f"Cache flush error: {e}")
            return False