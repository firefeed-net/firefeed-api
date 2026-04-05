"""
Middleware for FireFeed Internal API

This module provides middleware for the internal API endpoints.
"""

import os
import time
import json
import asyncio
import logging
from collections import deque
from typing import Callable, Awaitable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse

from .auth import verify_service_token, cleanup_expired_tokens
from .models import ErrorResponse
from .config import get_settings

logger = logging.getLogger(__name__)

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

        # Verify service authentication by extracting token from header
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authorization header",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            token = auth_header.split(" ", 1)[1]
            auth_result = verify_service_token(token)
            request.state.service_auth = auth_result
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    error="Authentication failed",
                    status_code=e.status_code,
                    error_code="SERVICE_AUTH_ERROR",
                    details={"message": e.detail}
                ).model_dump()
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

        # Log request - service_auth is a ServiceAuthResponse object, use getattr
        auth_obj = getattr(request.state, 'service_auth', None)
        service_name = getattr(auth_obj, 'service_name', 'unknown') if auth_obj else 'unknown'
        logger.info(
            f"Internal API Request: {request.method} {request.url.path} "
            f"from service: {service_name}"
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
                ).model_dump()
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
                ).model_dump()
            )


class InternalRateLimitingMiddleware:
    """Middleware for rate limiting internal API requests"""

    # Maximum number of entries in the in-memory store to prevent unbounded growth
    MAX_MEMORY_ENTRIES = 10000
    # Cleanup interval in seconds (avoid sorting on every request)
    CLEANUP_INTERVAL = 60

    def __init__(self):
        """
        Initialize rate limiting middleware with env-configurable limits
        """
        # Try to import Redis-based rate limiter, fallback to in-memory
        try:
            from firefeed_api.services.redis_service import RedisService
            from firefeed_api.services.rate_limit_service import RateLimitService
            self.redis_service = RedisService()
            self.rate_limiter = RateLimitService(self.redis_service)
            self.use_redis = True
        except (ImportError, Exception) as e:
            self.use_redis = False
            logger.warning(f"Redis rate limiting unavailable, falling back to in-memory: {e}")

        self.max_requests = int(os.getenv('INTERNAL_RATE_LIMIT_MAX', '10000'))
        self.window_seconds = int(os.getenv('INTERNAL_RATE_WINDOW_SECONDS', '60'))
        self.rss_multiplier = int(os.getenv('RSS_RATE_MULTIPLIER', '10'))
        # Use deque with maxlen to prevent unbounded memory growth
        self.requests: dict = {}
        self._last_cleanup = time.time()

        # Per-path adjustments
        self.path_limits = {
            '/api/v1/internal/rss/items': self.max_requests * 10,
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

        # Only bypass rate limiting for the specific RSS duplicate check endpoint
        if path == '/api/v1/internal/rss/items/duplicate-check':
            logger.debug(f"Bypassing rate limit for RSS duplicate check: {path}")
            return await call_next(request)

        # Get client identifier (service name)
        service_name = getattr(request.state, 'service_auth', None)
        if service_name:
            service_name = getattr(service_name, 'service_name', 'unknown')
        else:
            service_name = 'unknown'

        # Path-specific limit (calculated once)
        effective_limit = self.path_limits.get(path, self.max_requests)

        # Primary: Redis rate limiting (if available)
        if self.use_redis:
            rate_key = f"internal_rate:{service_name}"
            is_rss_path = '/rss/items' in path
            redis_result = self.rate_limiter.is_allowed(
                key=rate_key,
                limit=effective_limit * self.rss_multiplier if is_rss_path else effective_limit,
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
                    ).model_dump()
                )
        else:
            # Fallback: simple in-memory rate limiting with bounded memory
            current_time = time.time()
            rate_key = f"internal_rate:{service_name}"
            if rate_key not in self.requests:
                # Use deque with maxlen to prevent unbounded growth
                max_len = max(self.path_limits.get(path, self.max_requests) * 2, 1000)
                self.requests[rate_key] = deque(maxlen=max_len)

            # Clean old entries (entries outside the current window)
            self.requests[rate_key] = deque(
                [t for t in self.requests[rate_key] if current_time - t < self.window_seconds],
                maxlen=self.requests[rate_key].maxlen
            )

            is_rss_path = '/rss/items' in path
            limit = effective_limit * self.rss_multiplier if is_rss_path else effective_limit

            if len(self.requests[rate_key]) >= limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=ErrorResponse(
                        error="Rate limit exceeded",
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        error_code="RATE_LIMIT_EXCEEDED",
                        details={
                            "message": f"Too many requests from service {service_name}",
                            "limit": limit,
                            "window": self.window_seconds,
                        }
                    ).model_dump()
                )

            self.requests[rate_key].append(current_time)

            # Periodic TTL-based cleanup (avoids O(n log n) on every request)
            if current_time - self._last_cleanup > self.CLEANUP_INTERVAL:
                self._last_cleanup = current_time
                expired_keys = [
                    k for k, v in self.requests.items()
                    if not v or (current_time - v[-1]) > self.window_seconds
                ]
                for k in expired_keys:
                    del self.requests[k]
                # If still over limit, remove oldest entries
                if len(self.requests) > self.MAX_MEMORY_ENTRIES:
                    excess = len(self.requests) - self.MAX_MEMORY_ENTRIES
                    for k in list(self.requests.keys())[:excess]:
                        del self.requests[k]

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
                    ).model_dump()
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
                        ).model_dump()
                    )
            except ValueError:
                pass
        
        return await call_next(request)


class InternalMetricsMiddleware:
    """Middleware for collecting metrics in internal API"""

    # Maximum number of paths to track (prevent unbounded growth)
    MAX_PATHS = 10000
    MAX_ERROR_TYPES = 100

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

            method = request.method
            if len(self.metrics["requests_by_method"]) < self.MAX_PATHS:
                self.metrics["requests_by_method"][method] = \
                    self.metrics["requests_by_method"].get(method, 0) + 1

            path = request.url.path
            if len(self.metrics["requests_by_path"]) < self.MAX_PATHS:
                self.metrics["requests_by_path"][path] = \
                    self.metrics["requests_by_path"].get(path, 0) + 1

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
            if len(self.metrics["errors_by_type"]) < self.MAX_ERROR_TYPES:
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