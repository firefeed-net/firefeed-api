"""
Main entry point for FireFeed API

This module sets up the FastAPI application with all necessary
middleware, routes, and startup/shutdown handlers.
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from config.environment import get_environment, get_settings
from config.logging_config import setup_logging
from config.database_config import DatabaseConfig
from config.redis_config import RedisConfig
from services.database_service import DatabaseService
from services.redis_service import RedisService
from middleware import setup_middleware
from routers import setup_routers
from versioning import setup_versioning

# Setup logging
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager
    
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting FireFeed API...")
    
    try:
        # Initialize database
        db_config = DatabaseConfig.from_env()
        db_service = DatabaseService(db_config)
        await db_service.initialize()
        app.state.db_service = db_service
        
        # Initialize Redis
        redis_config = RedisConfig.from_env()
        redis_service = RedisService(redis_config)
        app.state.redis_service = redis_service
        
        # Health check
        health_result = redis_service.health_check()
        if not health_result['status']:
            logger.warning(f"Redis health check failed: {health_result['message']}")
        else:
            logger.info("Redis connection established successfully")
        
        logger.info("FireFeed API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start FireFeed API: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FireFeed API...")

    try:
        # Cleanup database
        if hasattr(app.state, 'db_service'):
            await app.state.db_service.close()

        # Cleanup Redis
        if hasattr(app.state, 'redis_service'):
            app.state.redis_service.close()

        logger.info("FireFeed API shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        # Don't re-raise during shutdown to prevent I/O errors


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    
    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="FireFeed API",
        description="API for FireFeed RSS reader service",
        version="1.0.0",
        docs_url=None,  # Disable default docs
        redoc_url=None,  # Disable default redoc
        openapi_url=None,  # Disable default OpenAPI
        lifespan=lifespan
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup routers
    setup_routers(app)
    
    # Setup versioning
    setup_versioning(app)
    
    return app


# Create application instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to FireFeed API",
        "version": "1.0.0",
        "environment": get_environment(),
        "docs": "/docs" if get_environment() == "development" else "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - returns basic status without sensitive details."""
    try:
        # Check if services are initialized
        db_status = "unknown"
        redis_status = "unknown"

        if hasattr(app.state, 'db_service'):
            db_health = await app.state.db_service.health_check()
            db_status = "ok" if isinstance(db_health, dict) and db_health.get("status") == "ok" else "error"
        else:
            db_status = "not_initialized"

        if hasattr(app.state, 'redis_service'):
            redis_health = app.state.redis_service.health_check()
            redis_status = "ok" if isinstance(redis_health, dict) and redis_health.get("status") in ("ok", True) else "error"
        else:
            redis_status = "not_initialized"

        overall_status = "healthy"
        if db_status == "error" or redis_status == "error":
            overall_status = "degraded"

        # Return simplified status (no detailed connection info)
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn

    # Get settings
    settings = get_settings()

    # Run application
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
        log_level=settings.log_level.lower(),
        access_log=settings.api_access_log
    )