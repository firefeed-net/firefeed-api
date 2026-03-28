# services/telegram_service.py - Telegram service using repositories
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from firefeed_core.interfaces import ITelegramRepository

logger = logging.getLogger(__name__)


class TelegramService:
    """Telegram service using repository pattern"""
    
    def __init__(self, telegram_repository: ITelegramRepository):
        self.telegram_repository = telegram_repository
    
    async def mark_bot_published(
        self, 
        news_id: Optional[str], 
        translation_id: Optional[int], 
        recipient_type: str, 
        recipient_id: int, 
        message_id: int, 
        language: str
    ) -> bool:
        """Mark item as published to Telegram"""
        try:
            return await self.telegram_repository.mark_bot_published(
                news_id, translation_id, recipient_type, recipient_id, message_id, language
            )
        except Exception as e:
            logger.error(f"Error marking bot published: {e}")
            raise
    
    async def check_bot_published(
        self, 
        news_id: Optional[str], 
        translation_id: Optional[int], 
        recipient_type: str, 
        recipient_id: int
    ) -> bool:
        """Check if item was published to Telegram"""
        try:
            return await self.telegram_repository.check_bot_published(
                news_id, translation_id, recipient_type, recipient_id
            )
        except Exception as e:
            logger.error(f"Error checking bot published: {e}")
            raise
    
    async def get_news_id_from_translation(self, translation_id: int) -> Optional[str]:
        """Get news ID from translation ID"""
        try:
            return await self.telegram_repository.get_news_id_from_translation(translation_id)
        except Exception as e:
            logger.error(f"Error getting news ID from translation {translation_id}: {e}")
            raise
    
    async def get_translation_id(self, news_id: str, language: str) -> Optional[int]:
        """Get translation ID by news ID and language"""
        try:
            return await self.telegram_repository.get_translation_id(news_id, language)
        except Exception as e:
            logger.error(f"Error getting translation ID for news {news_id} and language {language}: {e}")
            raise
    
    async def get_feed_cooldown_and_max_news(self, feed_id: int) -> Tuple[int, int]:
        """Get feed cooldown and max news per hour"""
        try:
            return await self.telegram_repository.get_feed_cooldown_and_max_news(feed_id)
        except Exception as e:
            logger.error(f"Error getting feed cooldown and max news for feed {feed_id}: {e}")
            raise
    
    async def get_last_telegram_publication_time(self, feed_id: int) -> Optional[datetime]:
        """Get last Telegram publication time for feed"""
        try:
            return await self.telegram_repository.get_last_telegram_publication_time(feed_id)
        except Exception as e:
            logger.error(f"Error getting last Telegram publication time for feed {feed_id}: {e}")
            raise
    
    async def get_recent_telegram_publications_count(self, feed_id: int, minutes: int) -> int:
        """Get recent Telegram publications count for feed"""
        try:
            return await self.telegram_repository.get_recent_telegram_publications_count(feed_id, minutes)
        except Exception as e:
            logger.error(f"Error getting recent Telegram publications count for feed {feed_id}: {e}")
            raise