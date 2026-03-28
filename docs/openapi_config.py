"""
OpenAPI configuration for FireFeed API

This module provides OpenAPI configuration and documentation
for the API endpoints.
"""

from typing import Dict, Any, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def get_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate OpenAPI schema for the application
    
    Args:
        app: FastAPI application instance
        
    Returns:
        OpenAPI schema dictionary
    """
    return get_openapi(
        title="FireFeed API",
        version="1.0.0",
        description="Microservices-based RSS feed management API with backward compatibility",
        routes=app.routes,
    )


def configure_openapi(app: FastAPI) -> None:
    """
    Configure OpenAPI schema for the application
    
    Args:
        app: FastAPI application instance
    """
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi_schema(app)
        
        # Add custom OpenAPI configuration
        openapi_schema["info"]["contact"] = {
            "name": "FireFeed Support",
            "email": "mail@firefeed.net",
            "url": "https://firefeed.net"
        }
        
        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for authentication"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for authentication"
            }
        }
        
        # Add custom responses
        openapi_schema["components"]["responses"] = {
            "ValidationError": {
                "description": "Validation error",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                                "status_code": {"type": "integer"},
                                "error_code": {"type": "string"},
                                "details": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "NotFoundError": {
                "description": "Resource not found",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                                "status_code": {"type": "integer"},
                                "error_code": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "AuthenticationError": {
                "description": "Authentication required",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "error": {"type": "string"},
                                "status_code": {"type": "integer"},
                                "error_code": {"type": "string"},
                                "www_authenticate": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
        
        # Add custom parameters
        openapi_schema["components"]["parameters"] = {
            "UserId": {
                "name": "user_id",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string",
                    "description": "User ID"
                }
            },
            "RssItemId": {
                "name": "rss_item_id",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string",
                    "description": "RSS item ID"
                }
            },
            "FeedId": {
                "name": "feed_id",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string",
                    "description": "RSS feed ID"
                }
            },
            "CategoryId": {
                "name": "category_id",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string",
                    "description": "Category ID"
                }
            },
            "SourceId": {
                "name": "source_id",
                "in": "path",
                "required": True,
                "schema": {
                    "type": "string",
                    "description": "Source ID"
                }
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi


def get_api_tags() -> List[Dict[str, Any]]:
    """
    Get API tags configuration
    
    Returns:
        List of API tags
    """
    return [
        {
            "name": "Authentication",
            "description": "Authentication and authorization endpoints"
        },
        {
            "name": "Users",
            "description": "User management endpoints"
        },
        {
            "name": "RSS Items",
            "description": "RSS items management endpoints"
        },
        {
            "name": "RSS Feeds",
            "description": "RSS feeds management endpoints"
        },
        {
            "name": "Categories",
            "description": "Categories management endpoints"
        },
        {
            "name": "Sources",
            "description": "Sources management endpoints"
        },
        {
            "name": "Translation",
            "description": "Translation service endpoints"
        },
        {
            "name": "Media",
            "description": "Media processing endpoints"
        },
        {
            "name": "Email",
            "description": "Email service endpoints"
        },
        {
            "name": "Health",
            "description": "Health check and monitoring endpoints"
        },
        {
            "name": "Internal",
            "description": "Internal service endpoints (for microservices communication)"
        }
    ]


def get_api_servers() -> List[Dict[str, Any]]:
    """
    Get API servers configuration
    
    Returns:
        List of API servers
    """
    return [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.firefeed.net",
            "description": "Production server"
        }
    ]


def get_api_external_docs() -> Dict[str, Any]:
    """
    Get API external documentation configuration
    
    Returns:
        External documentation configuration
    """
    return {
        "url": "https://docs.firefeed.net",
        "description": "FireFeed API Documentation"
    }