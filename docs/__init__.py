"""
Documentation package for FireFeed API

This package configures OpenAPI and documentation endpoints for the application.
"""

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from .openapi_config import configure_openapi


def setup_docs(app: FastAPI) -> None:
    """Configure OpenAPI and register documentation endpoints."""
    # Configure OpenAPI generation
    configure_openapi(app)

    # Expose OpenAPI JSON explicitly since default openapi_url is disabled in main
    def openapi_json():
        return app.openapi()

    app.add_api_route("/openapi.json", openapi_json, include_in_schema=False)

    # Swagger UI
    def swagger_ui():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="FireFeed API - Swagger UI",
        )

    app.add_api_route("/docs", swagger_ui, include_in_schema=False)

    # ReDoc
    def redoc_ui():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="FireFeed API - ReDoc",
        )

    app.add_api_route("/redoc", redoc_ui, include_in_schema=False)


__all__ = [
    'setup_docs',
]