"""
Middleware package for FireFeed API

This package contains all the middleware for the application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Import middleware components
from .public_auth import PublicAuthMiddleware, public_auth_required, public_auth_optional, optional_bearer


def setup_middleware(app: FastAPI) -> None:
    """Register application middlewares."""
    # Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # CORS (permissive by default; adjust as needed)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted hosts (optional; comment out or configure list)
    # app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


# Export commonly used middleware and setup function
__all__ = [
    'PublicAuthMiddleware',
    'public_auth_required',
    'public_auth_optional',
    'optional_bearer',
    'setup_middleware',
]