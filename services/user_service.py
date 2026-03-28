# services/user_service.py - User service using repositories
import logging
from typing import List, Dict, Any, Optional
from firefeed_core.interfaces import IUserRepository

logger = logging.getLogger(__name__)


class UserService:
    """User service using repository pattern"""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            return await self.user_repository.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            return await self.user_repository.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    async def create_user(self, user_data: Dict[str, Any]) -> int:
        """Create new user"""
        try:
            return await self.user_repository.create_user(user_data)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """Update user"""
        try:
            return await self.user_repository.update_user(user_id, user_data)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        try:
            return await self.user_repository.delete_user(user_id)
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            raise
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        try:
            return await self.user_repository.get_all_users()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise
    
    async def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get users by role"""
        try:
            return await self.user_repository.get_users_by_role(role)
        except Exception as e:
            logger.error(f"Error getting users by role {role}: {e}")
            raise