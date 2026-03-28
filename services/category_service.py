# services/category_service.py - Category service using repositories
import logging
from typing import List, Dict, Any, Optional
from firefeed_core.interfaces import ICategoryRepository

logger = logging.getLogger(__name__)


class CategoryService:
    """Category service using repository pattern"""
    
    def __init__(self, category_repository: ICategoryRepository):
        self.category_repository = category_repository
    
    async def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID"""
        try:
            return await self.category_repository.get_category_by_id(category_id)
        except Exception as e:
            logger.error(f"Error getting category by ID {category_id}: {e}")
            raise
    
    async def get_category_by_name(self, category_name: str) -> Optional[Dict[str, Any]]:
        """Get category by name"""
        try:
            return await self.category_repository.get_category_by_name(category_name)
        except Exception as e:
            logger.error(f"Error getting category by name {category_name}: {e}")
            raise
    
    async def create_category(self, category_data: Dict[str, Any]) -> int:
        """Create new category"""
        try:
            return await self.category_repository.create_category(category_data)
        except Exception as e:
            logger.error(f"Error creating category: {e}")
            raise
    
    async def update_category(self, category_id: int, category_data: Dict[str, Any]) -> bool:
        """Update category"""
        try:
            return await self.category_repository.update_category(category_id, category_data)
        except Exception as e:
            logger.error(f"Error updating category {category_id}: {e}")
            raise
    
    async def delete_category(self, category_id: int) -> bool:
        """Delete category"""
        try:
            return await self.category_repository.delete_category(category_id)
        except Exception as e:
            logger.error(f"Error deleting category {category_id}: {e}")
            raise
    
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories"""
        try:
            return await self.category_repository.get_all_categories()
        except Exception as e:
            logger.error(f"Error getting all categories: {e}")
            raise
    
    async def get_categories_by_source_id(self, source_id: int) -> List[Dict[str, Any]]:
        """Get categories by source ID"""
        try:
            return await self.category_repository.get_categories_by_source_id(source_id)
        except Exception as e:
            logger.error(f"Error getting categories for source {source_id}: {e}")
            raise