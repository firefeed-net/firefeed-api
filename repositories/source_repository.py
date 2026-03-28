"""Source repository implementation for FireFeed API."""
import logging
from typing import List, Dict, Any, Optional
from .interfaces import ISourceRepository
from firefeed_core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class SourceRepository(ISourceRepository):
    """PostgreSQL implementation of source repository."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_source_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get source by name."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, name, description, created_at, updated_at, alias, logo, site_url FROM sources WHERE name = %s",
                        (name,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "created_at": row[3],
                            "updated_at": row[4],
                            "alias": row[5],
                            "logo": row[6],
                            "site_url": row[7]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get source by name {name}: {str(e)}")

    async def get_source_by_id(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Get source by ID."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, name, description, created_at, updated_at, alias, logo, site_url FROM sources WHERE id = %s",
                        (source_id,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "created_at": row[3],
                            "updated_at": row[4],
                            "alias": row[5],
                            "logo": row[6],
                            "site_url": row[7]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get source by ID {source_id}: {str(e)}")

    async def create_source(self, name: str, description: Optional[str] = None, alias: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create new source."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")
                
                try:
                    # Check if source already exists
                    await cur.execute("SELECT id FROM sources WHERE name = %s", (name,))
                    if await cur.fetchone():
                        await cur.execute("ROLLBACK")
                        return {"error": "duplicate_name"}
                    
                    # Create source
                    await cur.execute(
                        "INSERT INTO sources (name, description, alias) VALUES (%s, %s, %s) RETURNING id, name, description, created_at, alias",
                        (name, description, alias)
                    )
                    row = await cur.fetchone()
                    
                    await cur.execute("COMMIT")
                    
                    if row:
                        return {
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "created_at": row[3],
                            "alias": row[4]
                        }
                    
                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise DatabaseException(f"Failed to create source: {str(e)}")
        
        return None

    async def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all sources."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, name, description, created_at, updated_at, alias, logo, site_url FROM sources ORDER BY name"
                    )
                    results = await cur.fetchall()
                    
                    if not results:
                        return []
                    
                    return [
                        {
                            "id": row[0],
                            "name": row[1],
                            "description": row[2],
                            "created_at": row[3],
                            "updated_at": row[4],
                            "alias": row[5],
                            "logo": row[6],
                            "site_url": row[7]
                        }
                        for row in results
                    ]
                    
                except Exception as e:
                    raise DatabaseException(f"Failed to get all sources: {str(e)}")