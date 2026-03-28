"""
Internal API package for FireFeed

This package contains the internal API endpoints and utilities
for microservice communication within the FireFeed system.
"""

# Import main internal API app
from .main import internal_app

# Import authentication utilities
from .auth import (
    create_service_token,
    verify_service_token,
    get_service_from_token,
    is_valid_service_token,
    verify_service_auth
)

# Import middleware
from .middleware import (
    ServiceAuthMiddleware,
    InternalLoggingMiddleware,
    InternalErrorHandlingMiddleware,
    InternalRateLimitingMiddleware,
    InternalSecurityMiddleware,
    InternalMetricsMiddleware,
    metrics_middleware,
    cleanup_expired_tokens_background
)

# Import models
from .models import (
    HealthResponse,
    ServiceInfo,
    ServiceTokenResponse,
    ServiceAuthResponse,
    ErrorResponse,
    UserResponse,
    RSSItemResponse,
    CategoryResponse,
    SourceResponse,
    RSSFeedResponse,
    TranslationRequest,
    TranslationResponse,
    MediaRequest,
    MediaResponse,
    EmailRequest,
    EmailResponse,
    TaskStatusResponse,
    MetricsResponse,
    CacheStatsResponse,
    DatabaseHealthResponse,
    SystemHealthResponse,
    ServiceStatusResponse
)

# Export commonly used items
__all__ = [
    # Main app
    'internal_app',
    
    # Authentication
    'create_service_token',
    'verify_service_token',
    'get_service_from_token',
    'is_valid_service_token',
    'verify_service_auth',
    
    # Middleware
    'ServiceAuthMiddleware',
    'InternalLoggingMiddleware',
    'InternalErrorHandlingMiddleware',
    'InternalRateLimitingMiddleware',
    'InternalSecurityMiddleware',
    'InternalMetricsMiddleware',
    'metrics_middleware',
    'cleanup_expired_tokens_background',
    
    # Models
    'HealthResponse',
    'ServiceInfo',
    'ServiceTokenResponse',
    'ServiceAuthResponse',
    'ErrorResponse',
    'UserResponse',
    'RSSItemResponse',
    'CategoryResponse',
    'SourceResponse',
    'RSSFeedResponse',
    'TranslationRequest',
    'TranslationResponse',
    'MediaRequest',
    'MediaResponse',
    'EmailRequest',
    'EmailResponse',
    'TaskStatusResponse',
    'MetricsResponse',
    'CacheStatsResponse',
    'DatabaseHealthResponse',
    'SystemHealthResponse',
    'ServiceStatusResponse'
]