"""
Middleware for FireFeed Internal API

This module provides middleware for the internal API endpoints.
"""

from typing import Callable, Awaitable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
import time
import json

from .auth import verify_service_auth, cleanup_expired_tokens
from .models import ErrorResponse
from .config import get_settings

# Get application settings
settings = get_settings()


class ServiceAuthMiddleware:
    """Middleware for service authentication"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with service authentication
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint function
            
        Returns:
            Response object
        """
        # Skip authentication for health check endpoints
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        # Verify service authentication
        try:
            auth_result = await verify_service_auth(request)
            request.state.service_auth = auth_result
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    error="Authentication failed",
                    status_code=e.status_code,
                    error_code="SERVICE_AUTH_ERROR",
                    details={"message": e.detail}
                ).dict()
            )
        
        return await call_next(request)


class InternalLoggingMiddleware:
    """Middleware for logging internal API requests"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with logging
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint function
            
        Returns:
            Response object
        """
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Internal API Request: {request.method} {request.url.path} "
            f"from service: {getattr(request.state, 'service_auth', {}).get('service_name', 'unknown')}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Internal API Response: {response.status_code} "
            f"({process_time:.4f}s) for {request.method} {request.url.path}"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class InternalErrorHandlingMiddleware:
    """Middleware for handling errors in internal API"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with error handling
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint function
            
        Returns:
            Response object
        """
        try:
            return await call_next(request)
        except HTTPException as e:
            logger.error(f"HTTP Exception in internal API: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    error="HTTP Error",
                    status_code=e.status_code,
                    error_code="HTTP_ERROR",
                    details={"message": e.detail}
                ).dict()
            )
        except Exception as e:
            logger.error(f"Unexpected error in internal API: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    error="Internal Server Error",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error_code="INTERNAL_ERROR",
                    details={"message": "An unexpected error occurred"}
                ).dict()
            )


import os
from firefeed_api.services.redis_service import RedisService
from firefeed_api.services.rate_limit_service import RateLimitService

class InternalRateLimitingMiddleware:
    """Middleware for rate limiting internal API requests"""
    
    def __init__(self):
        """
        Initialize rate limiting middleware with env-configurable limits
        """
        self.redis_service = RedisService()
        self.rate_limiter = RateLimitService(self.redis_service)
        self.max_requests = int(os.getenv('INTERNAL_RATE_LIMIT_MAX', '10000'))
        self.window_seconds = int(os.getenv('INTERNAL_RATE_WINDOW_SECONDS', '60'))
        self.rss_multiplier = int(os.getenv('RSS_RATE_MULTIPLIER', '10'))
        self.requests: dict = {}  # Fallback


        # Per-path adjustments
        self.path_limits = {
'/api/v1/internal/rss/items': self.max_requests * 10,  # 100k/min for RSS high-volume
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint function
            
        Returns:
            Response object
        """
        path = request.url.path
        
        # Bypass rate limiting for RSS duplicate checks
        if '/rss/items' in path:  # More robust match for POST /rss/items
            logger.debug(f"Bypassing rate limit for RSS duplicate check: {path}")
            return await call_next(request)
        
        # Get client identifier (service name)
        service_name = getattr(request.state, 'service_auth', {}).get('service_name', 'unknown')
        
        # Path-specific limit
        path = request.url.path
        effective_limit = self.path_limits.get(path, self.max_requests)
        
        # Get current time
        current_time = time.time()
        
        # Path-specific limit
        effective_limit = self.path_limits.get(path, self.max_requests)
        
        # Primary: Redis rate limiting
        rate_key = f"internal_rate:{service_name}"
        redis_result = self.rate_limiter.is_allowed(
            key=rate_key,
            limit=effective_limit * self.rss_multiplier if '/rss/items' in path else effective_limit,
            window=self.window_seconds
        )
        
        if not redis_result['allowed']:
            logger.warning(f"Redis rate limit exceeded for {service_name}: {path}, remaining: {redis_result['remaining']}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=ErrorResponse(
                    error="Rate limit exceeded",
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    error_code="RATE_LIMIT_EXCEEDED",
                    details={
                        "message": f"Too many requests from service {service_name}",
                        "limit": effective_limit,
                        "window": self.window_seconds,
                        "remaining": redis_result['remaining'],
                        "retry_after": redis_result['reset_time'] - int(time.time())
                    }
                ).dict()
            )

        
        return await call_next(request)


class InternalSecurityMiddleware:
    """Middleware for security checks in internal API"""
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with security checks
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint function
            
        Returns:
            Response object
        """
        # Check content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=ErrorResponse(
                        error="Invalid content type",
                        status_code=status.HTTP_400_BAD_REQUEST,
                        error_code="INVALID_CONTENT_TYPE",
                        details={"message": "Content-Type must be application/json"}
                    ).dict()
                )
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                max_content_length = 10 * 1024 * 1024  # 10MB
                if content_length > max_content_length:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content=ErrorResponse(
                            error="Request too large",
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            error_code="REQUEST_TOO_LARGE",
                            details={
                                "message": f"Request size {content_length} exceeds limit {max_content_length}"
                            }
                        ).dict()
                    )
            except ValueError:
                pass
        
        return await call_next(request)


class InternalMetricsMiddleware:
    """Middleware for collecting metrics in internal API"""
    
    def __init__(self):
        """Initialize metrics middleware"""
        self.metrics = {
            "requests_total": 0,
            "requests_by_method": {},
            "requests_by_path": {},
            "errors_total": 0,
            "errors_by_type": {},
            "processing_time_total": 0.0,
            "processing_time_avg": 0.0
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with metrics collection
        
        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint function
            
        Returns:
            Response object
        """
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Update metrics
            self.metrics["requests_total"] += 1
            self.metrics["requests_by_method"][request.method] = \
                self.metrics["requests_by_method"].get(request.method, 0) + 1
            self.metrics["requests_by_path"][request.url.path] = \
                self.metrics["requests_by_path"].get(request.url.path, 0) + 1
            
            # Calculate processing time
            process_time = time.time() - start_time
            self.metrics["processing_time_total"] += process_time
            
            # Update average processing time
            self.metrics["processing_time_avg"] = \
                self.metrics["processing_time_total"] / self.metrics["requests_total"]
            
            # Add metrics to response headers
            response.headers["X-Requests-Total"] = str(self.metrics["requests_total"])
            response.headers["X-Processing-Time-Avg"] = f"{self.metrics['processing_time_avg']:.4f}"
            
            return response
            
        except Exception as e:
            # Update error metrics
            self.metrics["errors_total"] += 1
            error_type = type(e).__name__
            self.metrics["errors_by_type"][error_type] = \
                self.metrics["errors_by_type"].get(error_type, 0) + 1
            
            # Re-raise the exception
            raise e
    
    def get_metrics(self) -> dict:
        """Get current metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = {
            "requests_total": 0,
            "requests_by_method": {},
            "requests_by_path": {},
            "errors_total": 0,
            "errors_by_type": {},
            "processing_time_total": 0.0,
            "processing_time_avg": 0.0
        }


# Global metrics middleware instance
metrics_middleware = InternalMetricsMiddleware()


def cleanup_expired_tokens_background() -> None:
    """Background task to clean up expired tokens"""
    cleanup_expired_tokens()