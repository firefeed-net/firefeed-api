# services/translation_service.py - Translation service using repositories
import logging
from typing import List, Dict, Any, Optional
from firefeed_core.interfaces import ITranslationRepository

logger = logging.getLogger(__name__)


class TranslationService:
    """Translation service using repository pattern"""
    
    def __init__(self, translation_repository: ITranslationRepository):
        self.translation_repository = translation_repository
    
    async def get_translation(self, news_id: str, language: str) -> Optional[Dict[str, Any]]:
        """Get translation by news ID and language"""
        try:
            return await self.translation_repository.get_translation(news_id, language)
        except Exception as e:
            logger.error(f"Error getting translation for news {news_id} and language {language}: {e}")
            raise
    
    async def create_translation(self, translation_data: Dict[str, Any]) -> int:
        """Create new translation"""
        try:
            return await self.translation_repository.create_translation(translation_data)
        except Exception as e:
            logger.error(f"Error creating translation: {e}")
            raise
    
    async def update_translation(self, translation_id: int, translation_data: Dict[str, Any]) -> bool:
        """Update translation"""
        try:
            return await self.translation_repository.update_translation(translation_id, translation_data)
        except Exception as e:
            logger.error(f"Error updating translation {translation_id}: {e}")
            raise
    
    async def delete_translation(self, translation_id: int) -> bool:
        """Delete translation"""
        try:
            return await self.translation_repository.delete_translation(translation_id)
        except Exception as e:
            logger.error(f"Error deleting translation {translation_id}: {e}")
            raise
    
    async def get_translations_by_news_id(self, news_id: str) -> List[Dict[str, Any]]:
        """Get translations by news ID"""
        try:
            return await self.translation_repository.get_translations_by_news_id(news_id)
        except Exception as e:
            logger.error(f"Error getting translations for news {news_id}: {e}")
            raise
    
    async def get_translations_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get translations by language"""
        try:
            return await self.translation_repository.get_translations_by_language(language)
        except Exception as e:
            logger.error(f"Error getting translations for language {language}: {e}")
            raise