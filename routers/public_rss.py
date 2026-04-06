"""Public RSS endpoints for FireFeed API - maintaining backward compatibility with monolithic version."""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel

from firefeed_core.api_client.client import APIClient
from firefeed_core.auth.token_manager import ServiceTokenManager
from firefeed_core.exceptions import ServiceException
from firefeed_core.models.base_models import RSSItem, CategoryItem, SourceItem, LanguageItem, PaginatedResponse
from config.environment import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["rss_items"],
    responses={
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)

# Pydantic models for public API (backward compatible with monolithic version)

class HTTPError(BaseModel):
    """Error response model for public API."""
    detail: str

# Helper functions (must be defined before usage in Depends)
def get_service_token_manager():
    """Get service token manager for internal API communication."""
    return ServiceTokenManager(
        secret_key=settings.jwt_secret_key,
        issuer="firefeed-api"
    )

def get_api_client():
    """Get API client for internal API communication."""
    return APIClient(
        base_url=settings.internal_api_url,
        token=settings.internal_api_token,
        service_id="firefeed-api-public"
    )

# Authentication dependency for public API
async def get_current_user(request: Request, api_client: APIClient = Depends(get_api_client)):
    """Get current authenticated user from JWT token."""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = auth_header.split(" ")[1]

    try:
        # Verify token
        token_manager = ServiceTokenManager(
            secret_key=settings.jwt_secret_key,
            issuer="firefeed-api"
        )
        payload = token_manager.verify_token(token)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        # Get user from internal API
        user_response = await api_client.get(f"/api/v1/internal/users/{user_id}")
        return user_response

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

async def get_current_user_optional(request: Request, api_client: APIClient = Depends(get_api_client)):
    """Get current authenticated user from JWT token (optional)."""
    try:
        return await get_current_user(request, api_client)
    except HTTPException:
        return None

@router.get(
    "/api/v1/rss-items/",
    response_model=PaginatedResponse[RSSItem],
    summary="Get RSS items with filtering and pagination",
    description="""
    Retrieve a filtered and paginated list of RSS items (news articles).
    
    This endpoint supports comprehensive filtering by language, category, source, publication status,
    date range, and full-text search. Results can be paginated using offset-based or cursor-based pagination.
    
    **Filtering Options:**
    - `original_language`: Filter by original article language
    - `category_id`: Filter by news categories (comma-separated values or multiple params allowed, e.g., 3,5 or category_id=3&category_id=5)
    - `source_id`: Filter by news sources (comma-separated values or multiple params allowed, e.g., 1,2 or source_id=1&source_id=2)
    - `telegram_published`: Filter by Telegram publication status (true/false) - published to channels OR users
    - `telegram_channels_published`: Filter by Telegram channels publication status (true/false)
    - `telegram_users_published`: Filter by Telegram users publication status (true/false)
    - `from_date`: Filter articles published after this timestamp (Unix timestamp)
    - `search_phrase`: Full-text search in titles and content
    
    **Pagination:**
    - **Offset-based:** Use `limit` and `offset` parameters
    - **Cursor-based:** Use `cursor_created_at` and `cursor_rss_item_id` for keyset pagination
    
    **Rate limit:** 1000 requests per minute
    """,
    responses={
        200: {
            "description": "List of RSS items",
            "model": PaginatedResponse[RSSItem]
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_rss_items(
    request: Request,
    original_language: Optional[str] = Query(None),
    category_id: Optional[List[str]] = Query(None),
    source_id: Optional[List[str]] = Query(None),
    telegram_published: Optional[bool] = Query(None),
    telegram_channels_published: Optional[bool] = Query(None),
    telegram_users_published: Optional[bool] = Query(None),
    from_date: Optional[int] = Query(None),
    search_phrase: Optional[str] = Query(None, alias="searchPhrase"),
    cursor_created_at: Optional[int] = Query(None),
    cursor_rss_item_id: Optional[str] = Query(None),
    limit: Optional[int] = Query(50, le=100, gt=0),
    offset: Optional[int] = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Get RSS items with filtering and pagination (backward compatible with monolithic version)."""
    try:
        # Parse category_id and source_id from lists of strings (supporting comma-separated or multiple params)
        category_ids = None
        if category_id:
            try:
                ids = []
                for cid in category_id:
                    if ',' in cid:
                        ids.extend(int(x.strip()) for x in cid.split(',') if x.strip())
                    else:
                        ids.append(int(cid.strip()))
                category_ids = ids if ids else None
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category_id format")

        source_ids = None
        if source_id:
            try:
                ids = []
                for sid in source_id:
                    if ',' in sid:
                        ids.extend(int(x.strip()) for x in sid.split(',') if x.strip())
                    else:
                        ids.append(int(sid.strip()))
                source_ids = ids if ids else None
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid source_id format")

        # Prepare query parameters
        params = {
            "original_language": original_language,
            "category_id": category_ids,
            "source_id": source_ids,
            "telegram_published": telegram_published,
            "telegram_channels_published": telegram_channels_published,
            "telegram_users_published": telegram_users_published,
            "from_date": from_date,
            "search_phrase": search_phrase,
            "cursor_created_at": cursor_created_at,
            "cursor_rss_item_id": cursor_rss_item_id,
            "limit": limit,
            "offset": offset
        }

        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Get RSS items via internal API
        response = await api_client.get("/api/v1/internal/rss/items", params=params)

        # Convert to PaginatedResponse format
        rss_items_list = response.get("data", [])
        count = len(rss_items_list)

        return PaginatedResponse[RSSItem](count=count, results=rss_items_list)

    except ServiceException as e:
        logger.error(f"Service error getting RSS items: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting RSS items: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/api/v1/rss-items/{rss_item_id}",
    response_model=RSSItem,
    summary="Get specific RSS item by ID",
    description="""
    Retrieve detailed information about a specific RSS item (news article) by its unique identifier.
    
    Returns the complete article data including all available translations, metadata, and media URLs.
    
    **Path parameters:**
    - `rss_item_id`: Unique identifier of the RSS item
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "RSS item details",
            "model": RSSItem
        },
        404: {
            "description": "Not Found - RSS item not found",
            "model": HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_rss_item_by_id(
    request: Request,
    rss_item_id: str,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Get specific RSS item by ID (backward compatible with monolithic version)."""
    try:
        response = await api_client.get(f"/api/v1/internal/rss/items/{rss_item_id}")

        if not response:
            raise HTTPException(status_code=404, detail="RSS item not found")

        return RSSItem(**response)

    except ServiceException as e:
        logger.error(f"Service error getting RSS item by ID: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting RSS item by ID: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/api/v1/categories/",
    response_model=PaginatedResponse[CategoryItem],
    summary="Get available news categories",
    description="""
    Retrieve a paginated list of available news categories.
    
    Categories are used to classify news articles and can be used for filtering RSS items.
    Results can be filtered by associated source IDs.
    
    **Query parameters:**
    - `limit`: Number of categories per page (1-1000, default: 100)
    - `offset`: Number of categories to skip (default: 0)
    - `source_ids`: Filter categories by associated news sources (comma-separated values or multiple params allowed, e.g., 1,2 or source_ids=1&source_ids=2)
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of news categories",
            "model": PaginatedResponse[CategoryItem]
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_categories(
    request: Request,
    limit: Optional[int] = Query(100, le=1000, gt=0),
    offset: Optional[int] = Query(0, ge=0),
    source_ids: Optional[List[str]] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Get available news categories (backward compatible with monolithic version)."""
    try:
        # Parse source_ids from lists of strings
        source_ids_list = None
        if source_ids:
            try:
                ids = []
                for sid in source_ids:
                    if ',' in sid:
                        ids.extend(int(x.strip()) for x in sid.split(',') if x.strip())
                    else:
                        ids.append(int(sid.strip()))
                source_ids_list = ids if ids else None
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid source_ids format")

        # Prepare query parameters
        params = {
            "limit": limit,
            "offset": offset,
            "source_ids": source_ids_list
        }

        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Get categories via internal API
        response = await api_client.get("/api/v1/internal/categories", params=params)

        categories = response.get("data", [])
        count = len(categories)

        return PaginatedResponse[CategoryItem](count=count, results=categories)

    except ServiceException as e:
        logger.error(f"Service error getting categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/api/v1/sources/",
    response_model=PaginatedResponse[SourceItem],
    summary="Get available news sources",
    description="""
    Retrieve a paginated list of available news sources.
    
    Sources represent the origin of news articles and can be used for filtering RSS items.
    Results can be filtered by associated category IDs.
    
    **Query parameters:**
    - `limit`: Number of sources per page (1-1000, default: 100)
    - `offset`: Number of sources to skip (default: 0)
    - `category_id`: Filter sources by associated categories (comma-separated values or multiple params allowed, e.g., 1,2 or category_id=1&category_id=2)
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of news sources",
            "model": PaginatedResponse[SourceItem]
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_sources(
    request: Request,
    limit: Optional[int] = Query(100, le=1000, gt=0),
    offset: Optional[int] = Query(0, ge=0),
    category_id: Optional[List[str]] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Get available news sources (backward compatible with monolithic version)."""
    try:
        # Parse category_id from lists of strings
        category_ids = None
        if category_id:
            try:
                ids = []
                for cid in category_id:
                    if ',' in cid:
                        ids.extend(int(x.strip()) for x in cid.split(',') if x.strip())
                    else:
                        ids.append(int(cid.strip()))
                category_ids = ids if ids else None
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category_id format")

        # Prepare query parameters
        params = {
            "limit": limit,
            "offset": offset,
            "category_id": category_ids
        }

        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Get sources via internal API
        response = await api_client.get("/api/v1/internal/sources", params=params)

        sources = response.get("data", [])
        count = len(sources)

        return PaginatedResponse[SourceItem](count=count, results=sources)

    except ServiceException as e:
        logger.error(f"Service error getting sources: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting sources: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/api/v1/languages/",
    response_model=PaginatedResponse[LanguageItem],
    summary="Get supported languages",
    description="""
    Retrieve the list of languages supported by the FireFeed system.
    
    These languages are available for content translation, user interface localization,
    and filtering RSS items by original or translated language.
    
    **Supported languages:**
    - `en`: English
    - `ru`: Russian (Русский)
    - `de`: German (Deutsch)
    - `fr`: French (Français)
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of supported languages",
            "model": PaginatedResponse[LanguageItem]
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_languages(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Get supported languages (backward compatible with monolithic version)."""
    try:
        # Get supported languages via internal API
        response = await api_client.get("/api/v1/internal/languages")

        languages = response.get("results", [])
        count = len(languages)

        return PaginatedResponse[LanguageItem](count=count, results=languages)

    except ServiceException as e:
        logger.error(f"Service error getting languages: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting languages: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/api/v1/health",
    summary="Health check endpoint",
    description="""
    Check the health status of the FireFeed API and its dependencies.
    
    This endpoint provides information about the system's operational status,
    including database connectivity and connection pool statistics.
    
    **Response fields:**
    - `status`: Overall system status ("ok" if healthy)
    - `database`: Database connection status ("ok" or "error")
    - `db_pool`: Database connection pool information
        - `total_connections`: Total number of connections in pool
        - `free_connections`: Number of available connections
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "System health information",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "database": "ok",
                        "db_pool": {
                            "total_connections": 20,
                            "free_connections": 15
                        }
                    }
                }
            }
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {
            "description": "Internal Server Error - System unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "database": "error",
                        "db_pool": {
                            "total_connections": 0,
                            "free_connections": 0
                        }
                    }
                }
            }
        }
    }
)
async def health_check(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Health check endpoint (backward compatible with monolithic version)."""
    try:
        # Get health status via internal API
        response = await api_client.get("/api/v1/internal/health")

        return response

    except ServiceException as e:
        logger.error(f"Service error in health check: {e}")
        return {
            "status": "error",
            "database": "error",
            "db_pool": {"total_connections": 0, "free_connections": 0}
        }
    except Exception as e:
        logger.error(f"Unexpected error in health check: {e}")
        return {
            "status": "error",
            "database": "error",
            "db_pool": {"total_connections": 0, "free_connections": 0}
        }

# RSS Feed endpoints (for managing RSS feeds)
@router.get(
    "/api/v1/rss/feeds/",
    response_model=PaginatedResponse[dict],
    summary="Get RSS feeds",
    description="""
    Retrieve a paginated list of RSS feeds.
    
    **Query parameters:**
    - `page`: Page number (default: 1)
    - `size`: Number of feeds per page (1-1000, default: 100)
    - `is_active`: Filter by active status
    - `category_id`: Filter by category ID
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of RSS feeds",
            "model": PaginatedResponse[dict]
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_rss_feeds(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(100, le=1000, gt=0),
    is_active: Optional[bool] = Query(None),
    category_id: Optional[int] = Query(None),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Get RSS feeds (backward compatible with monolithic version)."""
    try:
        # Prepare query parameters
        params = {
            "page": page,
            "size": size,
            "is_active": is_active,
            "category_id": category_id
        }

        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        # Get RSS feeds via internal API
        response = await api_client.get("/api/v1/internal/rss/feeds", params=params)

        feeds = response.get("data", [])
        count = len(feeds)

        return PaginatedResponse[dict](count=count, results=feeds)

    except ServiceException as e:
        logger.error(f"Service error getting RSS feeds: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting RSS feeds: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/api/v1/rss/feeds/{feed_id}",
    response_model=dict,
    summary="Get RSS feed by ID",
    description="""
    Retrieve detailed information about a specific RSS feed.
    
    **Path parameters:**
    - `feed_id`: Unique identifier of the RSS feed
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "RSS feed details",
            "model": dict
        },
        404: {
            "description": "Not Found - RSS feed not found",
            "model": HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_rss_feed_by_id(
    request: Request,
    feed_id: int,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Get RSS feed by ID (backward compatible with monolithic version)."""
    try:
        response = await api_client.get(f"/api/v1/internal/rss/feeds/{feed_id}")

        if not response:
            raise HTTPException(status_code=404, detail="RSS feed not found")

        return response

    except ServiceException as e:
        logger.error(f"Service error getting RSS feed by ID: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting RSS feed by ID: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# Translation endpoints
@router.post(
    "/api/v1/translation/translate",
    summary="Translate text",
    description="""
    Translate text to a specified language.
    
    **Request body:**
    - `text`: Text to translate
    - `target_language`: Target language code
    - `source_language`: Source language code (optional, auto-detected if not provided)
    - `model`: Translation model to use (optional)
    
    **Rate limit:** 100 requests per minute
    """,
    responses={
        200: {
            "description": "Translation successful",
            "content": {
                "application/json": {
                    "example": {
                        "original_text": "Hello world",
                        "translated_text": "Привет мир",
                        "source_language": "en",
                        "target_language": "ru",
                        "model_used": "facebook/m2m100_418M",
                        "confidence": 0.95,
                        "processing_time": 1.2
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Invalid parameters",
            "model": HTTPError
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def translate_text(
    request: Request,
    translation_data: dict,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    api_client: APIClient = Depends(get_api_client)
):
    """Translate text (backward compatible with monolithic version)."""
    try:
        # Validate translation data
        required_fields = ["text", "target_language"]
        for field in required_fields:
            if field not in translation_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Translate text via internal API
        response = await api_client.post("/api/v1/internal/translation/translate", json_data=translation_data)

        return response

    except ServiceException as e:
        logger.error(f"Service error translating text: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error translating text: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")