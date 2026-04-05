"""
Internal API for FireFeed

This module provides the internal API endpoints for microservice communication.
These endpoints are not intended for external use and require service authentication.
"""

from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
import logging

from .middleware import (
    ServiceAuthMiddleware,
    InternalLoggingMiddleware,
    InternalErrorHandlingMiddleware,
    InternalRateLimitingMiddleware
)
from .routers import (
    health_router,
    auth_router,
    users_router,
    rss_router,
    categories_router,
    sources_router,
    translation_router,
    media_router,
    email_router,
    maintenance_router,
    database_router,
    metrics_router,
    cache_router
)
from .config import get_settings
from .models import HealthResponse, ServiceInfo

logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager using modern pattern."""
    # Startup
    logger.info("Starting FireFeed Internal API")
    logger.info(f"Service: {settings.project_name} v{settings.project_version}")
    logger.info(f"Environment: {settings.api_environment}")
    yield
    # Shutdown
    try:
        logger.info("Shutting down FireFeed Internal API")
    except Exception:
        pass


# Create FastAPI app for internal API - use lifespan instead of deprecated events
internal_app = FastAPI(
    title="FireFeed Internal API",
    description="Internal API for microservice communication within FireFeed system",
    version="1.0.0",
    docs_url=None,  # Disable docs for internal API
    redoc_url=None,  # Disable redoc for internal API
    openapi_url=None,  # Disable OpenAPI for internal API
    lifespan=lifespan
)

# Parse allowed origins from settings
allowed_origins_list = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()] if settings.allowed_origins else []

# Add CORS middleware - require explicit origin configuration for internal API
if not allowed_origins_list:
    logger.warning("No allowed origins configured for internal API - using restrictive defaults")
    # Use localhost only as fallback, never use wildcard for internal API
    allowed_origins_list = ["http://localhost:3000", "http://localhost:8080"]

internal_app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add TrustedHostMiddleware with configured hosts (fallback to all if not set)
allowed_hosts = getattr(settings, 'allowed_hosts', None)
if allowed_hosts:
    internal_app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

if settings.secure_cookies:
    internal_app.add_middleware(HTTPSRedirectMiddleware)

# Add custom middleware (order matters: last added = first executed).
# Auth must run before rate limiting to prevent unauthenticated quota consumption.
internal_app.add_middleware(InternalRateLimitingMiddleware)   # added 1st → runs 4th
internal_app.add_middleware(InternalErrorHandlingMiddleware)  # added 2nd → runs 3rd
internal_app.add_middleware(InternalLoggingMiddleware)        # added 3rd → runs 2nd
internal_app.add_middleware(ServiceAuthMiddleware)            # added 4th → runs 1st (auth first)

# GZip should be added last to avoid I/O errors during shutdown
internal_app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
internal_app.include_router(health_router, prefix="/api/v1/internal", tags=["Health"])
internal_app.include_router(auth_router, prefix="/api/v1/internal", tags=["Authentication"])
internal_app.include_router(users_router, prefix="/api/v1/internal", tags=["Users"])
internal_app.include_router(rss_router, prefix="/api/v1/internal", tags=["RSS"])
internal_app.include_router(categories_router, prefix="/api/v1/internal", tags=["Categories"])
internal_app.include_router(sources_router, prefix="/api/v1/internal", tags=["Sources"])
internal_app.include_router(translation_router, prefix="/api/v1/internal", tags=["Translation"])
internal_app.include_router(media_router, prefix="/api/v1/internal", tags=["Media"])
internal_app.include_router(email_router, prefix="/api/v1/internal", tags=["Email"])
internal_app.include_router(maintenance_router, prefix="/api/v1/internal", tags=["Maintenance"])
internal_app.include_router(database_router, prefix="/api/v1/internal", tags=["Database"])
internal_app.include_router(metrics_router, prefix="/api/v1/internal", tags=["Metrics"])
internal_app.include_router(cache_router, prefix="/api/v1/internal", tags=["Cache"])

# Health check endpoint (no auth required - defined BEFORE routers to avoid conflicts)
@internal_app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for internal services"""
    return HealthResponse(
        status="healthy",
        version=settings.project_version,
        timestamp=datetime.utcnow().isoformat()
    )

# Root endpoint
@internal_app.get("/", response_model=ServiceInfo, tags=["Info"])
async def root():
    """Root endpoint with service information"""
    return ServiceInfo(
        name=settings.project_name,
        version=settings.project_version,
        description=settings.project_description,
        status="running"
    )

# Custom OpenAPI schema for internal API
def custom_openapi():
    if internal_app.openapi_schema:
        return internal_app.openapi_schema
    
    openapi_schema = get_openapi(
        title="FireFeed Internal API",
        version="1.0.0",
        description="Internal API for microservice communication",
        routes=internal_app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ServiceAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Service authentication token"
        }
    }
    
    # Add security to all endpoints
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"ServiceAuth": []}]
    
    internal_app.openapi_schema = openapi_schema
    return internal_app.openapi_schema

internal_app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "internal.main:internal_app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower()
    )