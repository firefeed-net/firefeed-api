"""Public API client for FireFeed API - handles communication with internal API."""

import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timezone
import httpx

from firefeed_core.auth.token_manager import ServiceTokenManager
from firefeed_core.exceptions import ServiceException, AuthenticationException, ServiceUnavailableException
from firefeed_core.models.base_models import UserResponse, RSSItem, CategoryItem, SourceItem, LanguageItem

logger = logging.getLogger(__name__)

class PublicAPIClient:
    """
    HTTP client for FireFeed public API communication with internal services.
    
    This client handles:
    - Authentication token management
    - Request/response transformation
    - Error handling and retry logic
    - Format conversion between public and internal APIs
    """
    
    def __init__(
        self,
        internal_api_base_url: str,
        service_token: str,
        service_id: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Public API Client.
        
        Args:
            internal_api_base_url: Base URL for internal API (e.g., http://localhost:8001)
            service_token: JWT token for internal API authentication
            service_id: Unique identifier for this service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.internal_api_base_url = internal_api_base_url.rstrip('/')
        self.service_token = service_token
        self.service_id = service_id
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": f"firefeed-public-api/{service_id}/1.0.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {service_token}",
                "X-Service-ID": service_id,
            }
        )
        
        logger.info(f"Initialized PublicAPIClient for {service_id} -> {internal_api_base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            logger.info("PublicAPIClient closed")
    
    def __del__(self):
        """Destructor to ensure client is closed."""
        if self.client and not self.client.is_closed:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.client.aclose())
                else:
                    loop.run_until_complete(self.client.aclose())
            except Exception:
                pass
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authentication."""
        return {
            "Authorization": f"Bearer {self.service_token}",
            "X-Service-ID": self.service_id,
            "X-Request-ID": f"{self.service_id}-{int(datetime.now(timezone.utc).timestamp() * 1000000)}",
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Make HTTP request to internal API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (will be joined with base_url)
            params: Query parameters
            data: Form data
            json_data: JSON data
            **kwargs: Additional arguments for httpx request
            
        Returns:
            Parsed response data
            
        Raises:
            ServiceException: For various HTTP and network errors
        """
        url = f"{self.internal_api_base_url}{endpoint}"
        headers = self._get_headers()
        
        # Prepare request arguments
        request_kwargs = {
            "headers": headers,
            "params": params or {},
            **kwargs
        }
        
        if json_data is not None:
            request_kwargs["json"] = json_data
        elif data is not None:
            request_kwargs["data"] = data
        
        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Making request: {method} {url} (attempt {attempt + 1})")
                
                response = await self.client.request(method, url, **request_kwargs)
                
                return self._handle_response(response)
                
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    import asyncio
                    delay = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}): {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    break
            
            except ServiceException as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.status_code < 500:
                    raise
                else:
                    # Retry on server errors (5xx)
                    last_exception = e
                    
                    if attempt < self.max_retries:
                        import asyncio
                        delay = 2 ** attempt  # Exponential backoff
                        logger.warning(
                            f"Request failed (attempt {attempt + 1}): {str(e)}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break
        
        # All retries failed
        if last_exception:
            raise ServiceUnavailableException(
                f"Request failed after {self.max_retries + 1} attempts: {str(last_exception)}"
            )
    
    def _handle_response(self, response: httpx.Response) -> Any:
        """
        Handle HTTP response and convert to appropriate exceptions.
        
        Args:
            response: httpx.Response object
            
        Returns:
            Parsed JSON response data
            
        Raises:
            ServiceException: For various HTTP error codes
        """
        # Log response
        logger.debug(
            f"Response: {response.status_code} {response.request.url} "
            f"({len(response.content)} bytes)"
        )
        
        try:
            response_data = response.json() if response.content else {}
        except Exception:
            response_data = {"message": response.text}
        
        # Handle HTTP status codes
        if response.status_code == 200:
            return response_data
        
        elif response.status_code == 201:
            return response_data
        
        elif response.status_code == 400:
            error_details = response_data.get("details", [])
            raise ServiceException(
                message=response_data.get("error", {}).get("message", "Bad request"),
                status_code=response.status_code,
                validation_errors=error_details
            )
        
        elif response.status_code == 401:
            raise AuthenticationException(
                message=response_data.get("error", {}).get("message", "Authentication failed")
            )
        
        elif response.status_code == 403:
            raise ServiceException(
                message=response_data.get("error", {}).get("message", "Forbidden"),
                status_code=response.status_code
            )
        
        elif response.status_code == 404:
            raise ServiceException(
                message=response_data.get("error", {}).get("message", "Not found"),
                status_code=response.status_code
            )
        
        elif response.status_code == 409:
            raise ServiceException(
                message=response_data.get("error", {}).get("message", "Conflict"),
                status_code=response.status_code
            )
        
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise ServiceException(
                message=response_data.get("error", {}).get("message", "Rate limit exceeded"),
                status_code=response.status_code,
                retry_after=int(retry_after) if retry_after else None
            )
        
        elif response.status_code >= 500:
            raise ServiceUnavailableException(
                message=response_data.get("error", {}).get("message", "Service unavailable")
            )
        
        else:
            raise ServiceException(
                message=f"Unexpected response: {response.status_code}",
                status_code=response.status_code,
                response_data=response_data
            )
    
    # User management methods
    
    async def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID from internal API."""
        return await self._make_request("GET", f"/api/v1/internal/users/{user_id}")
    
    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Get user by email from internal API."""
        return await self._make_request("GET", f"/api/v1/internal/users/by-email/{email}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user via internal API."""
        return await self._make_request("POST", "/api/v1/internal/users", json_data=user_data)
    
    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user via internal API."""
        return await self._make_request("PUT", f"/api/v1/internal/users/{user_id}", json_data=update_data)
    
    async def delete_user(self, user_id: int) -> Dict[str, Any]:
        """Delete user via internal API."""
        return await self._make_request("DELETE", f"/api/v1/internal/users/{user_id}")
    
    async def activate_user(self, user_id: int, verification_code: str) -> Dict[str, Any]:
        """Activate user via internal API."""
        activation_data = {
            "user_id": user_id,
            "verification_code": verification_code
        }
        return await self._make_request("POST", "/api/v1/internal/users/activate", json_data=activation_data)
    
    async def save_verification_code(self, user_id: int, verification_code: str, expires_at: datetime) -> Dict[str, Any]:
        """Save verification code via internal API."""
        verification_data = {
            "user_id": user_id,
            "verification_code": verification_code,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        return await self._make_request("POST", "/api/v1/internal/user-verification-codes", json_data=verification_data)
    
    async def save_password_reset_token(self, user_id: int, token: str, expires_at: datetime) -> Dict[str, Any]:
        """Save password reset token via internal API."""
        reset_data = {
            "user_id": user_id,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        return await self._make_request("POST", "/api/v1/internal/password-reset-tokens", json_data=reset_data)
    
    async def confirm_password_reset(self, token: str, new_password_hash: str) -> Dict[str, Any]:
        """Confirm password reset via internal API."""
        reset_data = {
            "token": token,
            "new_password_hash": new_password_hash
        }
        return await self._make_request("POST", "/api/v1/internal/password-reset-tokens/confirm", json_data=reset_data)
    
    # RSS items methods
    
    async def get_rss_items(
        self,
        original_language: Optional[str] = None,
        category_id: Optional[List[int]] = None,
        source_id: Optional[List[int]] = None,
        telegram_published: Optional[bool] = None,
        from_date: Optional[int] = None,
        search_phrase: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get RSS items via internal API."""
        params = {
            "original_language": original_language,
            "category_id": category_id,
            "source_id": source_id,
            "telegram_published": telegram_published,
            "from_date": from_date,
            "search_phrase": search_phrase,
            "limit": limit,
            "offset": offset
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return await self._make_request("GET", "/api/v1/internal/rss/items", params=params)
    
    async def get_rss_item_by_id(self, rss_item_id: str) -> Dict[str, Any]:
        """Get RSS item by ID via internal API."""
        return await self._make_request("GET", f"/api/v1/internal/rss/items/{rss_item_id}")
    
    # Categories methods
    
    async def get_categories(
        self,
        limit: int = 100,
        offset: int = 0,
        source_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Get categories via internal API."""
        params = {
            "limit": limit,
            "offset": offset,
            "source_ids": source_ids
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return await self._make_request("GET", "/api/v1/internal/categories", params=params)
    
    # Sources methods
    
    async def get_sources(
        self,
        limit: int = 100,
        offset: int = 0,
        category_id: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Get sources via internal API."""
        params = {
            "limit": limit,
            "offset": offset,
            "category_id": category_id
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return await self._make_request("GET", "/api/v1/internal/sources", params=params)
    
    # Languages methods
    
    async def get_languages(self) -> Dict[str, Any]:
        """Get supported languages via internal API."""
        return await self._make_request("GET", "/api/v1/internal/languages")
    
    # Health check
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check via internal API."""
        return await self._make_request("GET", "/api/v1/internal/health")
    
    # RSS feeds methods
    
    async def get_rss_feeds(
        self,
        page: int = 1,
        size: int = 100,
        is_active: Optional[bool] = None,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get RSS feeds via internal API."""
        params = {
            "page": page,
            "size": size,
            "is_active": is_active,
            "category_id": category_id
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return await self._make_request("GET", "/api/v1/internal/rss/feeds", params=params)
    
    async def get_rss_feed_by_id(self, feed_id: int) -> Dict[str, Any]:
        """Get RSS feed by ID via internal API."""
        return await self._make_request("GET", f"/api/v1/internal/rss/feeds/{feed_id}")
    
    # Translation methods
    
    async def translate_text(self, translation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate text via internal API."""
        return await self._make_request("POST", "/api/v1/internal/translation/translate", json_data=translation_data)
    
    # User-specific methods
    
    async def get_user_rss_items(
        self,
        user_id: int,
        display_language: Optional[str] = None,
        original_language: Optional[str] = None,
        from_date: Optional[int] = None,
        search_phrase: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's RSS items via internal API."""
        params = {
            "display_language": display_language,
            "original_language": original_language,
            "from_date": from_date,
            "search_phrase": search_phrase,
            "limit": limit,
            "offset": offset
        }
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return await self._make_request("GET", f"/api/v1/internal/users/{user_id}/rss-items", params=params)
    
    async def get_user_categories(self, user_id: int, source_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Get user's categories via internal API."""
        params = {}
        if source_ids:
            params["source_ids"] = source_ids
        
        return await self._make_request("GET", f"/api/v1/internal/users/{user_id}/categories", params=params)
    
    async def update_user_categories(self, user_id: int, category_ids: List[int]) -> Dict[str, Any]:
        """Update user's categories via internal API."""
        update_data = {"category_ids": category_ids}
        return await self._make_request("PUT", f"/api/v1/internal/users/{user_id}/categories", json_data=update_data)
    
    async def get_user_rss_feeds(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get user's RSS feeds via internal API."""
        params = {
            "limit": limit,
            "offset": offset
        }
        
        return await self._make_request("GET", f"/api/v1/internal/users/{user_id}/rss-feeds", params=params)
    
    async def create_user_rss_feed(self, user_id: int, feed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user's RSS feed via internal API."""
        feed_data["user_id"] = user_id
        return await self._make_request("POST", "/api/v1/internal/user-rss-feeds", json_data=feed_data)
    
    async def get_user_rss_feed_by_id(self, user_id: int, feed_id: int) -> Dict[str, Any]:
        """Get user's RSS feed by ID via internal API."""
        return await self._make_request("GET", f"/api/v1/internal/user-rss-feeds/{user_id}/{feed_id}")
    
    async def update_user_rss_feed(self, user_id: int, feed_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's RSS feed via internal API."""
        return await self._make_request("PUT", f"/api/v1/internal/user-rss-feeds/{user_id}/{feed_id}", json_data=update_data)
    
    async def delete_user_rss_feed(self, user_id: int, feed_id: int) -> Dict[str, Any]:
        """Delete user's RSS feed via internal API."""
        return await self._make_request("DELETE", f"/api/v1/internal/user-rss-feeds/{user_id}/{feed_id}")
    
    async def get_user_api_keys(self, user_id: int) -> Dict[str, Any]:
        """Get user's API keys via internal API."""
        return await self._make_request("GET", f"/api/v1/internal/api-keys/{user_id}")
    
    async def create_user_api_key(self, user_id: int, key_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user's API key via internal API."""
        key_data["user_id"] = user_id
        return await self._make_request("POST", "/api/v1/internal/api-keys", json_data=key_data)
    
    async def delete_user_api_key(self, user_id: int, key_id: int) -> Dict[str, Any]:
        """Delete user's API key via internal API."""
        return await self._make_request("DELETE", f"/api/v1/internal/api-keys/{user_id}/{key_id}")
    
    async def generate_telegram_link(self, user_id: int) -> Dict[str, Any]:
        """Generate Telegram link via internal API."""
        return await self._make_request("POST", f"/api/v1/internal/users/{user_id}/telegram-link")
    
    async def get_telegram_link_status(self, user_id: int) -> Dict[str, Any]:
        """Get Telegram link status via internal API."""
        return await self._make_request("GET", f"/api/v1/internal/users/{user_id}/telegram-link/status")