"""
Routers package for FireFeed API

This package contains all the API routers for the application.
"""

import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Import routers - handle missing files gracefully
try:
    from .public_auth import router as public_auth_router
except ImportError as e:
    logger.warning(f"Could not import public_auth router: {e}")
    from fastapi import APIRouter
    public_auth_router = APIRouter()

try:
    from .public_users import router as public_users_router
except ImportError as e:
    logger.warning(f"Could not import public_users router: {e}")
    from fastapi import APIRouter
    public_users_router = APIRouter()

try:
    from .public_rss import router as public_rss_router
except ImportError as e:
    logger.warning(f"Could not import public_rss router: {e}")
    from fastapi import APIRouter
    public_rss_router = APIRouter()

try:
    from .internal import router as internal_router
except ImportError as e:
    logger.warning(f"Could not import internal router: {e}")
    from fastapi import APIRouter
    internal_router = APIRouter()


def setup_routers(app: FastAPI) -> None:
    """Include all routers into the FastAPI app."""
    app.include_router(public_auth_router)
    app.include_router(public_users_router)
    app.include_router(public_rss_router)
    app.include_router(internal_router)


# Export commonly used routers and setup function
__all__ = [
    'public_auth_router',
    'public_users_router',
    'public_rss_router',
    'internal_router',
    'setup_routers',
]