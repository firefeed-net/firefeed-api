"""
Redis configuration for FireFeed API

This module provides Redis configuration specific to the API service,
including connection settings and validation.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from firefeed_core.config.redis_config import RedisConfig as BaseRedisConfig


@dataclass
class RedisConfig(BaseRedisConfig):
    """Redis configuration for FireFeed API service"""
    
    # API-specific settings
    cache_ttl: int = 3600  # 1 hour default cache TTL
    session_ttl: int = 86400  # 24 hours default session TTL
    rate_limit_ttl: int = 3600  # 1 hour rate limit TTL
    
    # Cache prefixes for different data types
    cache_prefix: str = "api:cache"
    session_prefix: str = "api:session"
    rate_limit_prefix: str = "api:rate_limit"
    
    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """Create RedisConfig from environment variables"""
        base_config = super().from_env()

        # Prepare base kwargs excluding API-specific keys to avoid duplicates
        base_kwargs = {
            k: v for k, v in base_config.__dict__.items()
            if k not in {
                'cache_ttl', 'session_ttl', 'rate_limit_ttl',
                'cache_prefix', 'session_prefix', 'rate_limit_prefix'
            }
        }

        return cls(
            **base_kwargs,
            # API-specific settings (override if provided via env, fallback to base values or defaults)
            cache_ttl=int(os.getenv('API_CACHE_TTL', str(getattr(base_config, 'cache_ttl', 3600)))),
            session_ttl=int(os.getenv('API_SESSION_TTL', str(getattr(base_config, 'session_ttl', 86400)))),
            rate_limit_ttl=int(os.getenv('API_RATE_LIMIT_TTL', str(getattr(base_config, 'rate_limit_ttl', 3600)))),
            cache_prefix=os.getenv('API_CACHE_PREFIX', getattr(base_config, 'cache_prefix', 'api:cache')),
            session_prefix=os.getenv('API_SESSION_PREFIX', getattr(base_config, 'session_prefix', 'api:session')),
            rate_limit_prefix=os.getenv('API_RATE_LIMIT_PREFIX', getattr(base_config, 'rate_limit_prefix', 'api:rate_limit')),
        )
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache-specific configuration"""
        return {
            'ttl': self.cache_ttl,
            'prefix': self.cache_prefix
        }
    
    def get_session_config(self) -> Dict[str, Any]:
        """Get session-specific configuration"""
        return {
            'ttl': self.session_ttl,
            'prefix': self.session_prefix
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return {
            'ttl': self.rate_limit_ttl,
            'prefix': self.rate_limit_prefix
        }
    
    def validate(self) -> List[str]:
        """Validate Redis configuration"""
        errors = super().validate()
        
        # Validate TTL values
        if self.cache_ttl <= 0:
            errors.append("Cache TTL must be positive")
        
        if self.session_ttl <= 0:
            errors.append("Session TTL must be positive")
        
        if self.rate_limit_ttl <= 0:
            errors.append("Rate limit TTL must be positive")
        
        # Validate prefixes
        if not self.cache_prefix:
            errors.append("Cache prefix cannot be empty")
        
        if not self.session_prefix:
            errors.append("Session prefix cannot be empty")
        
        if not self.rate_limit_prefix:
            errors.append("Rate limit prefix cannot be empty")
        
        return errors