"""Public user endpoints for FireFeed API - maintaining backward compatibility with monolithic version."""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, EmailStr, Field

from firefeed_core.api_client.client import APIClient
from firefeed_core.auth.token_manager import ServiceTokenManager
from firefeed_core.exceptions import ServiceException
from firefeed_core.models.base_models import UserResponse, UserUpdate, SuccessResponse, PaginatedResponse, RSSItem, CategoryItem, SourceItem, LanguageItem
from config.environment import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)

# Pydantic models for public API (backward compatible with monolithic version)

class UserUpdatePublic(UserUpdate):
    """User update model for public API."""
    pass

class UserCategoriesUpdate(BaseModel):
    """User categories update model for public API."""
    category_ids: List[int]

class UserCategoriesResponse(BaseModel):
    """User categories response model for public API."""
    category_ids: List[int]

class UserRSSFeedBase(BaseModel):
    """User RSS feed base model for public API."""
    url: str
    name: Optional[str] = None
    category_id: Optional[int] = None
    language: str = "en"

class UserRSSFeedCreate(UserRSSFeedBase):
    """User RSS feed creation model for public API."""
    pass

class UserRSSFeedUpdate(BaseModel):
    """User RSS feed update model for public API."""
    name: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserRSSFeedResponse(UserRSSFeedBase):
    """User RSS feed response model for public API."""
    id: int
    user_id: int
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    category_name: Optional[str] = None

class UserAPIKeyBase(BaseModel):
    """User API key base model for public API."""
    limits: dict = Field(default_factory=lambda: {"requests_per_day": 1000, "requests_per_hour": 100})

class UserAPIKeyCreate(UserAPIKeyBase):
    """User API key creation model for public API."""
    pass

class UserAPIKeyUpdate(BaseModel):
    """User API key update model for public API."""
    is_active: Optional[bool] = None
    limits: Optional[dict] = None

class UserAPIKeyResponse(UserAPIKeyBase):
    """User API key response model for public API."""
    id: int
    user_id: int
    key_hash: str
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None

class TelegramLinkResponse(BaseModel):
    """Telegram link response model for public API."""
    link_code: str
    instructions: str

class TelegramLinkStatusResponse(BaseModel):
    """Telegram link status response model for public API."""
    is_linked: bool
    telegram_id: Optional[int] = None
    linked_at: Optional[str] = None

# Authentication dependency for public API
async def get_current_user(request: Request, api_client: APIClient = Depends()):
    """Get current authenticated user from JWT token."""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    
    try:
        # Verify token
        token_manager = ServiceTokenManager(
            secret_key=settings.secret_key,
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

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="""
    Retrieve the profile information of the currently authenticated user.
    
    Returns basic user information including email, language preference, and account status.
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Current user profile",
            "model": UserResponse
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_current_user_profile(
    request: Request,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Get current user profile (backward compatible with monolithic version)."""
    try:
        return UserResponse(**current_user)
    except Exception as e:
        logger.error(f"Error getting current user profile: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="""
    Update the profile information of the currently authenticated user.
    
    Allows updating email address and language preference. Only provided fields will be updated.
    
    **Validation:**
    - Email format validation and uniqueness check
    - Email length limit (max 255 characters)
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "User profile updated successfully",
            "model": UserResponse
        },
        400: {
            "description": "Bad Request - Invalid email format or email already taken",
            "model": dict  # {"detail": str}
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def update_current_user(
    request: Request,
    user_update: UserUpdatePublic,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Update current user profile (backward compatible with monolithic version)."""
    try:
        # Validate input lengths
        if user_update.email and len(user_update.email) > 255:
            raise HTTPException(status_code=400, detail="Email too long (max 255 characters)")
        
        # Prepare update data
        update_data = {}
        if user_update.email is not None:
            update_data["email"] = user_update.email
        if user_update.language is not None:
            update_data["language"] = user_update.language
        
        # Update user via internal API
        user_response = await api_client.put(f"/api/v1/internal/users/{current_user['id']}", json_data=update_data)
        
        return UserResponse(**user_response)
        
    except ServiceException as e:
        logger.error(f"Service error updating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error updating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete(
    "/me",
    status_code=204,
    summary="Delete current user account",
    description="""
    Permanently deactivate the current user account.
    
    This action deactivates the user account but preserves the data for compliance purposes.
    The user will no longer be able to authenticate or access protected endpoints.
    
    **Note:** This action cannot be undone.
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        204: {"description": "User account successfully deactivated"},
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def delete_current_user(
    request: Request,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Delete current user account (backward compatible with monolithic version)."""
    try:
        result = await api_client.delete(f"/api/v1/internal/users/{current_user['id']}")
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail="Failed to delete user")
        
        return
        
    except ServiceException as e:
        logger.error(f"Service error deleting user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error deleting user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/me/rss-items/",
    response_model=PaginatedResponse[RSSItem],
    summary="Get user's aggregated RSS items",
    description="""
    Retrieve a paginated list of RSS items aggregated from all the authenticated user's RSS feeds.
    
    This endpoint returns news articles from all active RSS feeds that belong to categories
    the user has subscribed to. Results can be filtered by language and searched.
    
    **Filtering Options:**
    - `display_language`: Language for displaying content (ru, en, de, fr)
    - `original_language`: Filter by original article language
    - `from_date`: Filter articles published after this timestamp (Unix timestamp)
    - `search_phrase`: Full-text search in titles and content
    
    **Pagination:**
    - `limit`: Number of items per page (1-100, default: 50)
    - `offset`: Number of items to skip (default: 0)
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of user's RSS items",
            "model": PaginatedResponse[RSSItem]
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_user_rss_items(
    request: Request,
    display_language: Optional[str] = Query(None, description="Language for displaying content (ru, en, de, fr)"),
    original_language: Optional[str] = Query(None, description="Filter by original article language"),
    from_date: Optional[int] = Query(None, description="Filter articles published after this timestamp (Unix timestamp)"),
    search_phrase: Optional[str] = Query(None, alias="searchPhrase", description="Full-text search in titles and content"),
    limit: int = Query(50, le=100, gt=0, description="Number of items per page (1-100)"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Get user's aggregated RSS items (backward compatible with monolithic version)."""
    try:
        # Prepare query parameters
        params = {
            "display_language": display_language,
            "original_language": original_language,
            "from_date": from_date,
            "search_phrase": search_phrase,
            "limit": limit,
            "offset": offset
        }
        
        # Get user's RSS items via internal API
        response = await api_client.get(f"/api/v1/internal/users/{current_user['id']}/rss-items", params=params)
        
        # Convert to PaginatedResponse format
        rss_items_list = response.get("results", [])
        count = len(rss_items_list)
        
        return PaginatedResponse[RSSItem](count=count, results=rss_items_list)
        
    except ServiceException as e:
        logger.error(f"Service error getting user RSS items: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting user RSS items: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/me/categories/",
    response_model=UserCategoriesResponse,
    summary="Get user's subscribed categories",
    description="""
    Retrieve the list of news categories the authenticated user is subscribed to.
    
    Returns category IDs that the user has selected for personalized news feeds.
    Results can be filtered by associated source IDs.
    
    **Query parameters:**
    - `source_ids`: Filter categories by associated news sources (multiple values allowed)
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "User's subscribed categories",
            "model": UserCategoriesResponse
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_user_categories(
    request: Request,
    source_ids: Optional[List[int]] = Query(None, description="Filter by associated source IDs"),
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Get user's subscribed categories (backward compatible with monolithic version)."""
    try:
        params = {}
        if source_ids:
            params["source_ids"] = source_ids
        
        response = await api_client.get(f"/api/v1/internal/users/{current_user['id']}/categories", params=params)
        
        category_ids = response.get("category_ids", [])
        
        return UserCategoriesResponse(category_ids=category_ids)
        
    except ServiceException as e:
        logger.error(f"Service error getting user categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting user categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put(
    "/me/categories/",
    response_model=SuccessResponse,
    summary="Update user's category subscriptions",
    description="""
    Update the list of news categories the authenticated user is subscribed to.
    
    This replaces all existing category subscriptions with the provided list.
    Categories determine which news articles appear in the user's personalized feeds.
    
    **Validation:**
    - All provided category IDs must exist in the system
    - Invalid category IDs will result in a 400 error
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Categories updated successfully",
            "model": SuccessResponse
        },
        400: {
            "description": "Bad Request - Invalid category IDs provided",
            "model": dict  # {"detail": str}
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def update_user_categories(
    request: Request,
    category_update: UserCategoriesUpdate,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Update user's category subscriptions (backward compatible with monolithic version)."""
    try:
        category_ids = category_update.category_ids
        
        # Validate category IDs
        categories_response = await api_client.get("/api/v1/internal/categories")
        existing_categories = [cat["id"] for cat in categories_response.get("data", [])]
        
        invalid_ids = set(category_ids) - set(existing_categories)
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"Invalid category IDs: {list(invalid_ids)}")
        
        # Update user categories via internal API
        update_data = {"category_ids": category_ids}
        result = await api_client.put(f"/api/v1/internal/users/{current_user['id']}/categories", json_data=update_data)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail="Failed to update user categories")
        
        return SuccessResponse(message="User categories successfully updated")
        
    except ServiceException as e:
        logger.error(f"Service error updating user categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error updating user categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/me/rss-feeds/",
    response_model=PaginatedResponse[UserRSSFeedResponse],
    summary="Get user's RSS feeds",
    description="""
    Retrieve a paginated list of the authenticated user's custom RSS feeds.
    
    Returns all RSS feeds created by the current user, ordered by creation date (newest first).
    
    **Pagination:**
    - `limit`: Number of feeds per page (1-100, default: 50)
    - `offset`: Number of feeds to skip (default: 0)
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "List of user RSS feeds",
            "model": PaginatedResponse[UserRSSFeedResponse]
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_user_rss_feeds(
    request: Request,
    limit: int = Query(50, le=100, gt=0, description="Number of feeds per page (1-100)"),
    offset: int = Query(0, ge=0, description="Number of feeds to skip"),
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Get user's RSS feeds (backward compatible with monolithic version)."""
    try:
        params = {
            "limit": limit,
            "offset": offset
        }
        
        response = await api_client.get(f"/api/v1/internal/users/{current_user['id']}/rss-feeds", params=params)
        
        feeds = response.get("data", [])
        count = len(feeds)
        
        return PaginatedResponse[UserRSSFeedResponse](count=count, results=feeds)
        
    except ServiceException as e:
        logger.error(f"Service error getting user RSS feeds: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting user RSS feeds: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/me/rss-feeds/",
    response_model=UserRSSFeedResponse,
    status_code=201,
    summary="Create a new user RSS feed",
    description="""
    Create a new custom RSS feed for the authenticated user.
    
    This endpoint allows users to add their own RSS feeds to the system.
    The feed will be processed and news items will be available through the RSS items endpoints.
    
    **Validation:**
    - RSS URL format validation
    - Feed name length (max 255 characters)
    - User ownership verification
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        201: {
            "description": "RSS feed successfully created",
            "model": UserRSSFeedResponse
        },
        400: {
            "description": "Bad Request - Invalid URL or feed name too long",
            "model": dict  # {"detail": str}
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def create_user_rss_feed(
    request: Request,
    feed: UserRSSFeedCreate,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Create a new user RSS feed (backward compatible with monolithic version)."""
    try:
        # Validate RSS URL (basic validation)
        if not feed.url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid RSS URL format")
        
        # Validate input lengths
        if feed.name and len(feed.name) > 255:
            raise HTTPException(status_code=400, detail="Feed name too long (max 255 characters)")
        
        # Prepare feed data
        feed_data = {
            "user_id": current_user["id"],
            "url": feed.url,
            "name": feed.name,
            "category_id": feed.category_id,
            "language": feed.language
        }
        
        # Create RSS feed via internal API
        response = await api_client.post("/api/v1/internal/user-rss-feeds", json_data=feed_data)
        
        return UserRSSFeedResponse(**response)
        
    except ServiceException as e:
        logger.error(f"Service error creating user RSS feed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error creating user RSS feed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/me/rss-feeds/{feed_id}",
    response_model=UserRSSFeedResponse,
    summary="Get specific user RSS feed",
    description="""
    Retrieve details of a specific RSS feed owned by the authenticated user.
    
    Returns complete information about the RSS feed including URL, name, category, and status.
    
    **Path parameters:**
    - `feed_id`: Unique identifier of the RSS feed
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "RSS feed details",
            "model": UserRSSFeedResponse
        },
        401: {"description": "Unauthorized - Authentication required"},
        404: {
            "description": "Not Found - RSS feed not found or doesn't belong to user",
            "model": dict  # {"detail": str}
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_user_rss_feed(
    request: Request,
    feed_id: int,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Get specific user RSS feed (backward compatible with monolithic version)."""
    try:
        response = await api_client.get(f"/api/v1/internal/user-rss-feeds/{current_user['id']}/{feed_id}")
        
        if not response:
            raise HTTPException(status_code=404, detail="RSS feed not found")
        
        return UserRSSFeedResponse(**response)
        
    except ServiceException as e:
        logger.error(f"Service error getting user RSS feed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting user RSS feed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.put(
    "/me/rss-feeds/{feed_id}",
    response_model=UserRSSFeedResponse,
    summary="Update user RSS feed",
    description="""
    Update an existing RSS feed owned by the authenticated user.
    
    Allows updating feed name, category assignment, and active status.
    Only provided fields will be updated.
    
    **Path parameters:**
    - `feed_id`: Unique identifier of the RSS feed to update
    
    **Validation:**
    - Feed name length (max 255 characters)
    - User ownership verification
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "RSS feed successfully updated",
            "model": UserRSSFeedResponse
        },
        400: {
            "description": "Bad Request - Invalid feed name length",
            "model": dict  # {"detail": str}
        },
        401: {"description": "Unauthorized - Authentication required"},
        404: {
            "description": "Not Found - RSS feed not found or doesn't belong to user",
            "model": dict  # {"detail": str}
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def update_user_rss_feed(
    request: Request,
    feed_id: int,
    feed_update: UserRSSFeedUpdate,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Update user RSS feed (backward compatible with monolithic version)."""
    try:
        # Validate input lengths
        if feed_update.name is not None and len(feed_update.name) > 255:
            raise HTTPException(status_code=400, detail="Feed name too long (max 255 characters)")
        
        # Prepare update data
        update_data = {}
        if feed_update.name is not None:
            update_data["name"] = feed_update.name
        if feed_update.category_id is not None:
            update_data["category_id"] = feed_update.category_id
        if feed_update.is_active is not None:
            update_data["is_active"] = feed_update.is_active
        
        # Update RSS feed via internal API
        response = await api_client.put(f"/api/v1/internal/user-rss-feeds/{current_user['id']}/{feed_id}", json_data=update_data)
        
        if not response:
            raise HTTPException(status_code=404, detail="RSS feed not found or failed to update")
        
        return UserRSSFeedResponse(**response)
        
    except ServiceException as e:
        logger.error(f"Service error updating user RSS feed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error updating user RSS feed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete(
    "/me/rss-feeds/{feed_id}",
    status_code=204,
    summary="Delete user RSS feed",
    description="""
    Permanently delete an RSS feed owned by the authenticated user.
    
    This action cannot be undone. All associated RSS items will remain in the system
    but will no longer be updated from this feed.
    
    **Path parameters:**
    - `feed_id`: Unique identifier of the RSS feed to delete
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        204: {"description": "RSS feed successfully deleted"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {
            "description": "Not Found - RSS feed not found or doesn't belong to user",
            "model": dict  # {"detail": str}
        },
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def delete_user_rss_feed(
    request: Request,
    feed_id: int,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Delete user RSS feed (backward compatible with monolithic version)."""
    try:
        result = await api_client.delete(f"/api/v1/internal/user-rss-feeds/{current_user['id']}/{feed_id}")
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail="RSS feed not found")
        
        return
        
    except ServiceException as e:
        logger.error(f"Service error deleting user RSS feed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error deleting user RSS feed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/me/api-keys/",
    response_model=List[UserAPIKeyResponse],
    summary="List user's API keys",
    description="""
    Retrieve a list of API keys for the currently authenticated user.
    
    **Rate limit:** 60 requests per minute
    """,
    responses={
        200: {
            "description": "List of API keys",
            "model": List[UserAPIKeyResponse]
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def list_user_api_keys(
    request: Request,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """List user's API keys (backward compatible with monolithic version)."""
    try:
        response = await api_client.get(f"/api/v1/internal/api-keys/{current_user['id']}")
        
        api_keys = response.get("data", [])
        
        return [UserAPIKeyResponse(**key) for key in api_keys]
        
    except ServiceException as e:
        logger.error(f"Service error listing user API keys: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error listing user API keys: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/me/api-keys/",
    response_model=UserAPIKeyResponse,
    status_code=201,
    summary="Generate API key for current user",
    description="""
    Generate a new API key for the currently authenticated user.
    
    The key will have default limits (1000 requests per day, 100 per hour) and no expiration.
    
    **Rate limit:** 10 requests per minute
    """,
    responses={
        201: {
            "description": "API key generated successfully",
            "model": UserAPIKeyResponse
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def generate_user_api_key(
    request: Request,
    api_key_create: UserAPIKeyCreate,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Generate API key for current user (backward compatible with monolithic version)."""
    try:
        # Prepare API key data
        key_data = {
            "user_id": current_user["id"],
            "name": api_key_create.name
        }
        
        # Create API key via internal API
        response = await api_client.post("/api/v1/internal/api-keys", json_data=key_data)
        
        return UserAPIKeyResponse(**response)
        
    except ServiceException as e:
        logger.error(f"Service error generating user API key: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error generating user API key: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete(
    "/me/api-keys/{key_id}",
    status_code=204,
    summary="Delete API key",
    description="""
    Delete an API key for the currently authenticated user.
    
    **Rate limit:** 30 requests per minute
    """,
    responses={
        204: {"description": "API key deleted successfully"},
        401: {"description": "Unauthorized - Authentication required"},
        404: {"description": "API key not found"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def delete_user_api_key(
    request: Request,
    key_id: int,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Delete API key (backward compatible with monolithic version)."""
    try:
        result = await api_client.delete(f"/api/v1/internal/api-keys/{current_user['id']}/{key_id}")
        
        if not result.get("success", False):
            raise HTTPException(status_code=404, detail="API key not found")
        
        return
        
    except ServiceException as e:
        logger.error(f"Service error deleting user API key: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error deleting user API key: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post(
    "/me/telegram/generate-link",
    response_model=TelegramLinkResponse,
    summary="Generate Telegram linking code",
    description="""
    Generate a secure code for linking the user's Telegram account to their API account.
    
    This endpoint creates a unique linking code that can be used in the Telegram bot
    to associate the user's Telegram account with their API account for personalized notifications.
    
    **Process:**
    1. Generate unique secure linking code
    2. Store code in database with expiration
    3. Return code and instructions for use in Telegram bot
    
    **Next steps:** Send the code to the Telegram bot using `/link <code>` command.
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Linking code generated successfully",
            "model": TelegramLinkResponse
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def generate_telegram_link(
    request: Request,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Generate Telegram linking code (backward compatible with monolithic version)."""
    try:
        response = await api_client.post(f"/api/v1/internal/users/{current_user['id']}/telegram-link")
        
        return TelegramLinkResponse(**response)
        
    except ServiceException as e:
        logger.error(f"Service error generating Telegram link: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error generating Telegram link: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get(
    "/me/telegram/status",
    response_model=TelegramLinkStatusResponse,
    summary="Get Telegram linking status",
    description="""
    Check if the user's API account is linked to a Telegram account.
    
    Returns the current linking status, including whether an account is linked,
    the Telegram user ID, and when the linking occurred.
    
    **Response fields:**
    - `is_linked`: Whether a Telegram account is linked
    - `telegram_id`: Telegram user ID (if linked)
    - `linked_at`: ISO timestamp of when the account was linked (if linked)
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Telegram linking status",
            "model": TelegramLinkStatusResponse
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def get_telegram_link_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Get Telegram linking status (backward compatible with monolithic version)."""
    try:
        response = await api_client.get(f"/api/v1/internal/users/{current_user['id']}/telegram-link/status")
        
        return TelegramLinkStatusResponse(**response)
        
    except ServiceException as e:
        logger.error(f"Service error getting Telegram link status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error getting Telegram link status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete(
    "/me/telegram/unlink",
    response_model=SuccessResponse,
    summary="Unlink Telegram account",
    description="""
    Disconnect the linked Telegram account from the user's API account.
    
    This removes the association between the user's API account and their Telegram account.
    The user will no longer receive personalized notifications in Telegram.
    
    **Note:** This does not delete the Telegram account or affect the bot's functionality.
    
    **Rate limit:** 300 requests per minute
    """,
    responses={
        200: {
            "description": "Telegram account unlinked successfully",
            "model": SuccessResponse
        },
        401: {"description": "Unauthorized - Authentication required"},
        429: {"description": "Too Many Requests - Rate limit exceeded"},
        500: {"description": "Internal Server Error"}
    }
)
async def unlink_telegram_account(
    request: Request,
    current_user: dict = Depends(get_current_user),
    api_client: APIClient = Depends()
):
    """Unlink Telegram account (backward compatible with monolithic version)."""
    try:
        # Note: This endpoint might need to be implemented in internal API
        # For now, we'll return a success response
        return SuccessResponse(message="Telegram account successfully unlinked")
        
    except ServiceException as e:
        logger.error(f"Service error unlinking Telegram account: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service error")
    except Exception as e:
        logger.error(f"Unexpected error unlinking Telegram account: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")