"""
Routers package for FireFeed API

This package contains all the API routers for the application.
"""

from fastapi import FastAPI

# Import routers
from .public_auth import router as public_auth_router
from .public_users import router as public_users_router
from .public_rss import router as public_rss_router
from .internal import router as internal_router


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