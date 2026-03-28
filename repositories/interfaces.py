"""Repository interfaces for FireFeed API."""
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from datetime import datetime


class IUserRepository(ABC):
    """Interface for user repository operations."""
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def create_user(self, email: str, password_hash: str, language: str = 'en') -> Optional[Dict[str, Any]]:
        """Create new user."""
        pass
    
    @abstractmethod
    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user."""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        pass


class IRSSFeedRepository(ABC):
    """Interface for RSS feed repository operations."""
    
    @abstractmethod
    async def get_rss_feed_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get RSS feed by URL."""
        pass
    
    @abstractmethod
    async def create_rss_feed(self, source_id: int, url: str, name: str, category_id: int, language: str) -> Optional[Dict[str, Any]]:
        """Create new RSS feed."""
        pass
    
    @abstractmethod
    async def update_rss_feed(self, feed_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update RSS feed."""
        pass
    
    @abstractmethod
    async def delete_rss_feed(self, feed_id: int) -> bool:
        """Delete RSS feed."""
        pass


class IRSSItemRepository(ABC):
    """Interface for RSS item repository operations."""
    
    @abstractmethod
    async def get_rss_item_by_id(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get RSS item by ID."""
        pass
    
    @abstractmethod
    async def create_rss_item(self, news_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new RSS item."""
        pass
    
    @abstractmethod
    async def update_rss_item(self, news_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update RSS item."""
        pass
    
    @abstractmethod
    async def delete_rss_item(self, news_id: str) -> bool:
        """Delete RSS item."""
        pass
    
    @abstractmethod
    async def get_rss_items_by_category(self, category_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Get RSS items by category."""
        pass


class ICategoryRepository(ABC):
    """Interface for category repository operations."""
    
    @abstractmethod
    async def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get category by name."""
        pass
    
    @abstractmethod
    async def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID."""
        pass
    
    @abstractmethod
    async def create_category(self, name: str, display_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create new category."""
        pass
    
    @abstractmethod
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories."""
        pass


class ISourceRepository(ABC):
    """Interface for source repository operations."""
    
    @abstractmethod
    async def get_source_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get source by name."""
        pass
    
    @abstractmethod
    async def get_source_by_id(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Get source by ID."""
        pass
    
    @abstractmethod
    async def create_source(self, name: str, description: Optional[str] = None, alias: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create new source."""
        pass
    
    @abstractmethod
    async def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all sources."""
        pass


class IApiKeyRepository(ABC):
    """Interface for API key repository operations."""
    
    @abstractmethod
    async def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash."""
        pass
    
    @abstractmethod
    async def create_api_key(self, user_id: int, key_hash: str, limits: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new API key."""
        pass
    
    @abstractmethod
    async def update_api_key(self, key_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update API key."""
        pass
    
    @abstractmethod
    async def delete_api_key(self, key_id: int) -> bool:
        """Delete API key."""
        pass