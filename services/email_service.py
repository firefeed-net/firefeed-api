# services/email_service.py - Email service using repositories
import logging
from typing import List, Dict, Any, Optional
from firefeed_core.interfaces import IEmailRepository

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using repository pattern"""
    
    def __init__(self, email_repository: IEmailRepository):
        self.email_repository = email_repository
    
    async def get_email_by_id(self, email_id: int) -> Optional[Dict[str, Any]]:
        """Get email by ID"""
        try:
            return await self.email_repository.get_email_by_id(email_id)
        except Exception as e:
            logger.error(f"Error getting email by ID {email_id}: {e}")
            raise
    
    async def create_email(self, email_data: Dict[str, Any]) -> int:
        """Create new email"""
        try:
            return await self.email_repository.create_email(email_data)
        except Exception as e:
            logger.error(f"Error creating email: {e}")
            raise
    
    async def update_email(self, email_id: int, email_data: Dict[str, Any]) -> bool:
        """Update email"""
        try:
            return await self.email_repository.update_email(email_id, email_data)
        except Exception as e:
            logger.error(f"Error updating email {email_id}: {e}")
            raise
    
    async def delete_email(self, email_id: int) -> bool:
        """Delete email"""
        try:
            return await self.email_repository.delete_email(email_id)
        except Exception as e:
            logger.error(f"Error deleting email {email_id}: {e}")
            raise
    
    async def get_emails_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        """Get emails by user ID"""
        try:
            return await self.email_repository.get_emails_by_user_id(user_id)
        except Exception as e:
            logger.error(f"Error getting emails for user {user_id}: {e}")
            raise
    
    async def get_emails_by_news_id(self, news_id: str) -> List[Dict[str, Any]]:
        """Get emails by news ID"""
        try:
            return await self.email_repository.get_emails_by_news_id(news_id)
        except Exception as e:
            logger.error(f"Error getting emails for news {news_id}: {e}")
            raise