# services/rss_service.py - RSS service using repositories
import logging
from typing import List, Dict, Any, Optional
from firefeed_core.interfaces import IRssRepository

logger = logging.getLogger(__name__)


class RssService:
    """RSS service using repository pattern"""
    
    def __init__(self, rss_repository: IRssRepository):
        self.rss_repository = rss_repository
    
    async def get_rss_data_by_id(self, rss_id: int) -> Optional[Dict[str, Any]]:
        """Get RSS data by ID"""
        try:
            return await self.rss_repository.get_rss_data_by_id(rss_id)
        except Exception as e:
            logger.error(f"Error getting RSS data by ID {rss_id}: {e}")
            raise
    
    async def get_rss_data_by_news_id(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get RSS data by news ID"""
        try:
            return await self.rss_repository.get_rss_data_by_news_id(news_id)
        except Exception as e:
            logger.error(f"Error getting RSS data by news ID {news_id}: {e}")
            raise
    
    async def create_rss_data(self, rss_data: Dict[str, Any]) -> int:
        """Create new RSS data"""
        try:
            return await self.rss_repository.create_rss_data(rss_data)
        except Exception as e:
            logger.error(f"Error creating RSS data: {e}")
            raise
    
    async def update_rss_data(self, rss_id: int, rss_data: Dict[str, Any]) -> bool:
        """Update RSS data"""
        try:
            return await self.rss_repository.update_rss_data(rss_id, rss_data)
        except Exception as e:
            logger.error(f"Error updating RSS data {rss_id}: {e}")
            raise
    
    async def delete_rss_data(self, rss_id: int) -> bool:
        """Delete RSS data"""
        try:
            return await self.rss_repository.delete_rss_data(rss_id)
        except Exception as e:
            logger.error(f"Error deleting RSS data {rss_id}: {e}")
            raise
    
    async def get_rss_data_by_source_id(self, source_id: int) -> List[Dict[str, Any]]:
        """Get RSS data by source ID"""
        try:
            return await self.rss_repository.get_rss_data_by_source_id(source_id)
        except Exception as e:
            logger.error(f"Error getting RSS data for source {source_id}: {e}")
            raise
    
    async def get_rss_data_by_category_id(self, category_id: int) -> List[Dict[str, Any]]:
        """Get RSS data by category ID"""
        try:
            return await self.rss_repository.get_rss_data_by_category_id(category_id)
        except Exception as e:
            logger.error(f"Error getting RSS data for category {category_id}: {e}")
            raise
    
    async def get_rss_data_by_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get RSS data by date range"""
        try:
            return await self.rss_repository.get_rss_data_by_date_range(start_date, end_date, limit, offset)
        except Exception as e:
            logger.error(f"Error getting RSS data by date range {start_date} to {end_date}: {e}")
            raise
    
    async def get_rss_data_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Get RSS data by title"""
        try:
            return await self.rss_repository.get_rss_data_by_title(title)
        except Exception as e:
            logger.error(f"Error getting RSS data by title {title}: {e}")
            raise
    
    async def get_rss_data_by_description(self, description: str) -> List[Dict[str, Any]]:
        """Get RSS data by description"""
        try:
            return await self.rss_repository.get_rss_data_by_description(description)
        except Exception as e:
            logger.error(f"Error getting RSS data by description {description}: {e}")
            raise
    
    async def get_rss_data_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get RSS data by language"""
        try:
            return await self.rss_repository.get_rss_data_by_language(language)
        except Exception as e:
            logger.error(f"Error getting RSS data by language {language}: {e}")
            raise