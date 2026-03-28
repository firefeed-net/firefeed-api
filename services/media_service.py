# services/media_service.py - Media service using repositories
import logging
from typing import List, Dict, Any, Optional
from firefeed_core.interfaces import IMediaRepository

logger = logging.getLogger(__name__)


class MediaService:
    """Media service using repository pattern"""
    
    def __init__(self, media_repository: IMediaRepository):
        self.media_repository = media_repository
    
    async def get_media_by_id(self, media_id: int) -> Optional[Dict[str, Any]]:
        """Get media by ID"""
        try:
            return await self.media_repository.get_media_by_id(media_id)
        except Exception as e:
            logger.error(f"Error getting media by ID {media_id}: {e}")
            raise
    
    async def create_media(self, media_data: Dict[str, Any]) -> int:
        """Create new media"""
        try:
            return await self.media_repository.create_media(media_data)
        except Exception as e:
            logger.error(f"Error creating media: {e}")
            raise
    
    async def update_media(self, media_id: int, media_data: Dict[str, Any]) -> bool:
        """Update media"""
        try:
            return await self.media_repository.update_media(media_id, media_data)
        except Exception as e:
            logger.error(f"Error updating media {media_id}: {e}")
            raise
    
    async def delete_media(self, media_id: int) -> bool:
        """Delete media"""
        try:
            return await self.media_repository.delete_media(media_id)
        except Exception as e:
            logger.error(f"Error deleting media {media_id}: {e}")
            raise
    
    async def get_media_by_news_id(self, news_id: str) -> List[Dict[str, Any]]:
        """Get media by news ID"""
        try:
            return await self.media_repository.get_media_by_news_id(news_id)
        except Exception as e:
            logger.error(f"Error getting media for news {news_id}: {e}")
            raise
    
    async def get_media_by_type(self, media_type: str) -> List[Dict[str, Any]]:
        """Get media by type"""
        try:
            return await self.media_repository.get_media_by_type(media_type)
        except Exception as e:
            logger.error(f"Error getting media by type {media_type}: {e}")
            raise