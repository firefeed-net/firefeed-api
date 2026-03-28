"""Category repository implementation for FireFeed API."""
import logging
from typing import List, Dict, Any, Optional
from .interfaces import ICategoryRepository
from firefeed_core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class CategoryRepository(ICategoryRepository):
    """PostgreSQL implementation of category repository."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get category by name."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, name, display_name, created_at, updated_at FROM categories WHERE name = %s",
                        (name,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "name": row[1],
                            "display_name": row[2],
                            "created_at": row[3],
                            "updated_at": row[4]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get category by name {name}: {str(e)}")

    async def get_category_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category by ID."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, name, display_name, created_at, updated_at FROM categories WHERE id = %s",
                        (category_id,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "name": row[1],
                            "display_name": row[2],
                            "created_at": row[3],
                            "updated_at": row[4]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get category by ID {category_id}: {str(e)}")

    async def create_category(self, name: str, display_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create new category."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")
                
                try:
                    # Check if category already exists
                    await cur.execute("SELECT id FROM categories WHERE name = %s", (name,))
                    if await cur.fetchone():
                        await cur.execute("ROLLBACK")
                        return {"error": "duplicate_name"}
                    
                    # Create category
                    await cur.execute(
                        "INSERT INTO categories (name, display_name) VALUES (%s, %s) RETURNING id, name, display_name, created_at",
                        (name, display_name)
                    )
                    row = await cur.fetchone()
                    
                    await cur.execute("COMMIT")
                    
                    if row:
                        return {
                            "id": row[0],
                            "name": row[1],
                            "display_name": row[2],
                            "created_at": row[3]
                        }
                    
                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise DatabaseException(f"Failed to create category: {str(e)}")
        
        return None

    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, name, display_name, created_at, updated_at FROM categories ORDER BY name"
                    )
                    results = await cur.fetchall()
                    
                    if not results:
                        return []
                    
                    return [
                        {
                            "id": row[0],
                            "name": row[1],
                            "display_name": row[2],
                            "created_at": row[3],
                            "updated_at": row[4]
                        }
                        for row in results
                    ]
                    
                except Exception as e:
                    raise DatabaseException(f"Failed to get all categories: {str(e)}")