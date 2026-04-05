"""RSS item repository implementation for FireFeed API."""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from .interfaces import IRSSItemRepository
from firefeed_core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class RSSItemRepository(IRSSItemRepository):
    """PostgreSQL implementation of RSS item repository."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_rss_item_by_id(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get RSS item by ID."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    query = """
                        SELECT
                            rd.news_id,
                            rd.original_title,
                            rd.original_content,
                            rd.original_language,
                            rd.image_filename,
                            c.name as category_name,
                            s.name as source_name,
                            rd.source_url,
                            rd.created_at,
                            rd.embedding,
                            nt_ru.translated_title as title_ru,
                            nt_ru.translated_content as content_ru,
                            nt_de.translated_title as title_de,
                            nt_de.translated_content as content_de,
                            nt_fr.translated_title as title_fr,
                            nt_fr.translated_content as content_fr,
                            nt_en.translated_title as title_en,
                            nt_en.translated_content as content_en
                        FROM rss_data rd
                        JOIN categories c ON rd.category_id = c.id
                        LEFT JOIN rss_feeds rf ON rd.rss_feed_id = rf.id
                        LEFT JOIN sources s ON rf.source_id = s.id
                        LEFT JOIN news_translations nt_ru ON rd.news_id = nt_ru.news_id AND nt_ru.language = 'ru'
                        LEFT JOIN news_translations nt_de ON rd.news_id = nt_de.news_id AND nt_de.language = 'de'
                        LEFT JOIN news_translations nt_fr ON rd.news_id = nt_fr.news_id AND nt_fr.language = 'fr'
                        LEFT JOIN news_translations nt_en ON rd.news_id = nt_en.news_id AND nt_en.language = 'en'
                        WHERE rd.news_id = %s
                    """
                    await cur.execute(query, (news_id,))
                    result = await cur.fetchone()
                    if result:
                        columns = [desc[0] for desc in cur.description]
                        return dict(zip(columns, result))
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get RSS item by ID {news_id}: {str(e)}")

    async def create_rss_item(self, news_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new RSS item."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    # Use ON CONFLICT DO NOTHING to handle duplicate news_id gracefully
                    await cur.execute(
                        """INSERT INTO rss_data (news_id, original_title, original_content, original_language, category_id, image_filename, rss_feed_id, source_url, video_filename)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (news_id) DO NOTHING
                           RETURNING news_id, original_title, original_content, original_language, category_id, image_filename, created_at, rss_feed_id, source_url, video_filename""",
                        (
                            news_data['news_id'],
                            news_data['original_title'],
                            news_data['original_content'],
                            news_data['original_language'],
                            news_data.get('category_id'),
                            news_data.get('image_filename'),
                            news_data.get('rss_feed_id'),
                            news_data.get('source_url'),
                            news_data.get('video_filename')
                        )
                    )
                    row = await cur.fetchone()
                    
                    if row:
                        return {
                            "news_id": row[0],
                            "original_title": row[1],
                            "original_content": row[2],
                            "original_language": row[3],
                            "category_id": row[4],
                            "image_filename": row[5],
                            "created_at": row[6],
                            "rss_feed_id": row[7],
                            "source_url": row[8],
                            "video_filename": row[9]
                        }
                    else:
                        # Item already exists, fetch and return it
                        await cur.execute(
                            """SELECT news_id, original_title, original_content, original_language, category_id, image_filename, created_at, rss_feed_id, source_url, video_filename
                               FROM rss_data WHERE news_id = %s""",
                            (news_data['news_id'],)
                        )
                        row = await cur.fetchone()
                        if row:
                            return {
                                "news_id": row[0],
                                "original_title": row[1],
                                "original_content": row[2],
                                "original_language": row[3],
                                "category_id": row[4],
                                "image_filename": row[5],
                                "created_at": row[6],
                                "rss_feed_id": row[7],
                                "source_url": row[8],
                                "video_filename": row[9]
                            }
                    
                except Exception as e:
                    raise DatabaseException(f"Failed to create RSS item: {str(e)}")
        
        return None

    async def update_rss_item(self, news_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update RSS item."""
        # Whitelist of allowed updatable columns to prevent SQL injection
        ALLOWED_COLUMNS = {
            "original_title", "original_content", "original_language",
            "category_id", "image_filename", "rss_feed_id", "source_url",
            "video_filename", "embedding"
        }

        set_parts = []
        values = []
        for key, value in update_data.items():
            if key not in ALLOWED_COLUMNS:
                logger.warning(f"Attempted to update disallowed column: {key}")
                continue
            # Validate column name is a valid identifier
            if not key.isidentifier():
                logger.warning(f"Invalid column name rejected: {key}")
                continue
            set_parts.append(f"{key} = %s")
            values.append(value)

        if not set_parts:
            logger.warning(f"No valid columns to update for item {news_id}")
            return None

        # Build query with validated, whitelisted column names only
        query = f"UPDATE rss_data SET {', '.join(set_parts)}, updated_at = NOW() WHERE news_id = %s RETURNING news_id, original_title, original_content, original_language, category_id, image_filename, updated_at, rss_feed_id, source_url, video_filename"
        values.append(news_id)

        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    if row:
                        return {
                            "news_id": row[0],
                            "original_title": row[1],
                            "original_content": row[2],
                            "original_language": row[3],
                            "category_id": row[4],
                            "image_filename": row[5],
                            "updated_at": row[6],
                            "rss_feed_id": row[7],
                            "source_url": row[8],
                            "video_filename": row[9]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to update RSS item {news_id}: {str(e)}")

    async def delete_rss_item(self, news_id: str) -> bool:
        """Delete RSS item."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute("DELETE FROM rss_data WHERE news_id = %s", (news_id,))
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to delete RSS item {news_id}: {str(e)}")

    async def get_rss_items_by_category(self, category_id: int, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Get RSS items by category."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    query = """
                        SELECT
                            rd.news_id,
                            rd.original_title,
                            rd.original_content,
                            rd.original_language,
                            rd.image_filename,
                            c.name as category_name,
                            s.name as source_name,
                            rd.source_url,
                            rd.created_at
                        FROM rss_data rd
                        JOIN categories c ON rd.category_id = c.id
                        LEFT JOIN rss_feeds rf ON rd.rss_feed_id = rf.id
                        LEFT JOIN sources s ON rf.source_id = s.id
                        WHERE rd.category_id = %s
                        ORDER BY rd.created_at DESC
                        LIMIT %s OFFSET %s
                    """
                    await cur.execute(query, (category_id, limit, offset))
                    results = await cur.fetchall()
                    
                    if not results:
                        return []
                    
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in results]
                    
                except Exception as e:
                    raise DatabaseException(f"Failed to get RSS items by category {category_id}: {str(e)}")