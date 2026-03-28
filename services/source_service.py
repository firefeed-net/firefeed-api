# services/source_service.py - Source service using repositories
import logging
from typing import List, Dict, Any, Optional
from firefeed_core.interfaces import ISourceRepository

logger = logging.getLogger(__name__)


class SourceService:
    """Source service using repository pattern"""
    
    def __init__(self, source_repository: ISourceRepository):
        self.source_repository = source_repository
    
    async def get_source_by_id(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Get source by ID"""
        try:
            return await self.source_repository.get_source_by_id(source_id)
        except Exception as e:
            logger.error(f"Error getting source by ID {source_id}: {e}")
            raise
    
    async def get_source_by_url(self, source_url: str) -> Optional[Dict[str, Any]]:
        """Get source by URL"""
        try:
            return await self.source_repository.get_source_by_url(source_url)
        except Exception as e:
            logger.error(f"Error getting source by URL {source_url}: {e}")
            raise
    
    async def create_source(self, source_data: Dict[str, Any]) -> int:
        """Create new source"""
        try:
            return await self.source_repository.create_source(source_data)
        except Exception as e:
            logger.error(f"Error creating source: {e}")
            raise
    
    async def update_source(self, source_id: int, source_data: Dict[str, Any]) -> bool:
        """Update source"""
        try:
            return await self.source_repository.update_source(source_id, source_data)
        except Exception as e:
            logger.error(f"Error updating source {source_id}: {e}")
            raise
    
    async def delete_source(self, source_id: int) -> bool:
        """Delete source"""
        try:
            return await self.source_repository.delete_source(source_id)
        except Exception as e:
            logger.error(f"Error deleting source {source_id}: {e}")
            raise
    
    async def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all sources"""
        try:
            return await self.source_repository.get_all_sources()
        except Exception as e:
            logger.error(f"Error getting all sources: {e}")
            raise
    
    async def get_sources_by_category_id(self, category_id: int) -> List[Dict[str, Any]]:
        """Get sources by category ID"""
        try:
            return await self.source_repository.get_sources_by_category_id(category_id)
        except Exception as e:
            logger.error(f"Error getting sources for category {category_id}: {e}")
            raise