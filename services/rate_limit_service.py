"""
Rate limiting service for FireFeed API

This module provides rate limiting functionality using Redis for the API service.
"""

import time
from typing import Optional, Dict, Any, Union
from services.redis_service import RedisService
from config.redis_config import RedisConfig


class RateLimitService:
    """Rate limiting service for FireFeed API using Redis"""
    
    def __init__(self, redis_service: Optional[RedisService] = None):
        """
        Initialize rate limiting service
        
        Args:
            redis_service: Redis service instance
        """
        self.redis_service = redis_service or RedisService()
        self.config = self.redis_service.config
    
    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        ttl: Optional[int] = None
    ) -> Dict[str, Union[bool, int]]:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Rate limit key (e.g., IP address, user ID)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            ttl: TTL for the rate limit key (uses default if None)
            
        Returns:
            Dictionary with 'allowed' status and 'remaining' count
        """
        try:
            rate_key = self.redis_service.get_rate_limit_key(key)
            ttl = ttl or self.config.rate_limit_ttl
            
            current_time = int(time.time())
            window_start = current_time - window
            
            # Remove expired entries
            self.redis_service.get_client().zremrangebyscore(rate_key, 0, window_start)
            
            # Count current requests in window
            current_count = self.redis_service.get_client().zcard(rate_key)
            
            if current_count >= limit:
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_time': current_time + window
                }
            
            # Add current request
            self.redis_service.get_client().zadd(rate_key, {str(current_time): current_time})
            self.redis_service.get_client().expire(rate_key, ttl)
            
            remaining = limit - current_count - 1
            
            return {
                'allowed': True,
                'remaining': remaining,
                'reset_time': current_time + window
            }
            
        except Exception as e:
            print(f"Rate limit check error for key {key}: {e}")
            # Fail open - allow request if Redis is unavailable
            return {
                'allowed': True,
                'remaining': limit - 1,
                'reset_time': int(time.time()) + window
            }
    
    def get_usage(
        self,
        key: str,
        window: int
    ) -> Dict[str, Union[int, int]]:
        """
        Get current rate limit usage
        
        Args:
            key: Rate limit key
            window: Time window in seconds
            
        Returns:
            Dictionary with 'count' and 'reset_time'
        """
        try:
            rate_key = self.redis_service.get_rate_limit_key(key)
            current_time = int(time.time())
            window_start = current_time - window
            
            # Remove expired entries
            self.redis_service.get_client().zremrangebyscore(rate_key, 0, window_start)
            
            # Count current requests in window
            count = self.redis_service.get_client().zcard(rate_key)
            
            return {
                'count': count,
                'reset_time': current_time + window
            }
            
        except Exception as e:
            print(f"Rate limit usage error for key {key}: {e}")
            return {
                'count': 0,
                'reset_time': int(time.time()) + window
            }
    
    def reset_limit(self, key: str) -> bool:
        """
        Reset rate limit for a key
        
        Args:
            key: Rate limit key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            rate_key = self.redis_service.get_rate_limit_key(key)
            result = self.redis_service.get_client().delete(rate_key)
            return bool(result)
            
        except Exception as e:
            print(f"Rate limit reset error for key {key}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiting statistics
        
        Returns:
            Dictionary with rate limiting stats
        """
        try:
            pattern = self.redis_service.get_rate_limit_key("*")
            keys = self.redis_service.get_client().keys(pattern)
            
            return {
                'active_limits': len(keys),
                'memory_usage': self.redis_service.get_client().memory_usage(pattern) if keys else 0
            }
            
        except Exception as e:
            print(f"Rate limit stats error: {e}")
            return {
                'active_limits': 0,
                'memory_usage': 0
            }
    
    def cleanup_expired_limits(self) -> int:
        """
        Clean up expired rate limit entries
        
        Returns:
            Number of entries cleaned up
        """
        try:
            pattern = self.redis_service.get_rate_limit_key("*")
            keys = self.redis_service.get_client().keys(pattern)
            
            cleaned_count = 0
            for key in keys:
                ttl = self.redis_service.get_client().ttl(key)
                if ttl == -1:  # Key exists but has no expiration
                    self.redis_service.get_client().expire(key, self.config.rate_limit_ttl)
                    cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            print(f"Rate limit cleanup error: {e}")
            return 0