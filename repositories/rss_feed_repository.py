"""RSS feed repository implementation for FireFeed API."""
import logging
from typing import List, Dict, Any, Optional
from .interfaces import IRSSFeedRepository
from firefeed_core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class RSSFeedRepository(IRSSFeedRepository):
    """PostgreSQL implementation of RSS feed repository."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_rss_feed_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get RSS feed by URL."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, source_id, url, name, category_id, language, is_active, created_at, updated_at, cooldown_minutes, max_news_per_hour FROM rss_feeds WHERE url = %s",
                        (url,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "source_id": row[1],
                            "url": row[2],
                            "name": row[3],
                            "category_id": row[4],
                            "language": row[5],
                            "is_active": row[6],
                            "created_at": row[7],
                            "updated_at": row[8],
                            "cooldown_minutes": row[9],
                            "max_news_per_hour": row[10]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get RSS feed by URL {url}: {str(e)}")

    async def create_rss_feed(self, source_id: int, url: str, name: str, category_id: int, language: str) -> Optional[Dict[str, Any]]:
        """Create new RSS feed."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")
                
                try:
                    # Check if feed already exists
                    await cur.execute("SELECT id FROM rss_feeds WHERE url = %s", (url,))
                    if await cur.fetchone():
                        await cur.execute("ROLLBACK")
                        return {"error": "duplicate_url"}
                    
                    # Create RSS feed
                    await cur.execute(
                        "INSERT INTO rss_feeds (source_id, url, name, category_id, language) VALUES (%s, %s, %s, %s, %s) RETURNING id, source_id, url, name, category_id, language, is_active, created_at, cooldown_minutes, max_news_per_hour",
                        (source_id, url, name, category_id, language)
                    )
                    row = await cur.fetchone()
                    
                    await cur.execute("COMMIT")
                    
                    if row:
                        return {
                            "id": row[0],
                            "source_id": row[1],
                            "url": row[2],
                            "name": row[3],
                            "category_id": row[4],
                            "language": row[5],
                            "is_active": row[6],
                            "created_at": row[7],
                            "cooldown_minutes": row[8],
                            "max_news_per_hour": row[9]
                        }
                    
                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise DatabaseException(f"Failed to create RSS feed: {str(e)}")
        
        return None

    async def update_rss_feed(self, feed_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update RSS feed."""
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)
        
        query = f"UPDATE rss_feeds SET {', '.join(set_parts)}, updated_at = NOW() WHERE id = %s RETURNING id, source_id, url, name, category_id, language, is_active, updated_at, cooldown_minutes, max_news_per_hour"
        values.append(feed_id)
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "source_id": row[1],
                            "url": row[2],
                            "name": row[3],
                            "category_id": row[4],
                            "language": row[5],
                            "is_active": row[6],
                            "updated_at": row[7],
                            "cooldown_minutes": row[8],
                            "max_news_per_hour": row[9]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to update RSS feed {feed_id}: {str(e)}")

    async def delete_rss_feed(self, feed_id: int) -> bool:
        """Delete RSS feed."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("DELETE FROM rss_feeds WHERE id = %s", (feed_id,))
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to delete RSS feed {feed_id}: {str(e)}")