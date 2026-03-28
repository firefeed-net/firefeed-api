"""API key repository implementation for FireFeed API."""
import logging
from typing import List, Dict, Any, Optional
from .interfaces import IApiKeyRepository
from firefeed_core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class APIKeyRepository(IApiKeyRepository):
    """PostgreSQL implementation of API key repository."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_api_key_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Get API key by hash."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, user_id, key_hash, limits, is_active, created_at, expires_at FROM user_api_keys WHERE key_hash = %s AND is_active = true",
                        (key_hash,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "user_id": row[1],
                            "key_hash": row[2],
                            "limits": row[3],
                            "is_active": row[4],
                            "created_at": row[5],
                            "expires_at": row[6]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get API key by hash: {str(e)}")

    async def create_api_key(self, user_id: int, key_hash: str, limits: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new API key."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")
                
                try:
                    # Check if key already exists
                    await cur.execute("SELECT id FROM user_api_keys WHERE key_hash = %s", (key_hash,))
                    if await cur.fetchone():
                        await cur.execute("ROLLBACK")
                        return {"error": "duplicate_key"}
                    
                    # Create API key
                    await cur.execute(
                        "INSERT INTO user_api_keys (user_id, key_hash, limits) VALUES (%s, %s, %s) RETURNING id, user_id, key_hash, limits, is_active, created_at",
                        (user_id, key_hash, limits)
                    )
                    row = await cur.fetchone()
                    
                    await cur.execute("COMMIT")
                    
                    if row:
                        return {
                            "id": row[0],
                            "user_id": row[1],
                            "key_hash": row[2],
                            "limits": row[3],
                            "is_active": row[4],
                            "created_at": row[5]
                        }
                    
                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise DatabaseException(f"Failed to create API key: {str(e)}")
        
        return None

    async def update_api_key(self, key_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update API key."""
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)
        
        query = f"UPDATE user_api_keys SET {', '.join(set_parts)}, updated_at = NOW() WHERE id = %s RETURNING id, user_id, key_hash, limits, is_active, created_at, expires_at, updated_at"
        values.append(key_id)
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "user_id": row[1],
                            "key_hash": row[2],
                            "limits": row[3],
                            "is_active": row[4],
                            "created_at": row[5],
                            "expires_at": row[6],
                            "updated_at": row[7]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to update API key {key_id}: {str(e)}")

    async def delete_api_key(self, key_id: int) -> bool:
        """Delete API key (soft delete)."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "UPDATE user_api_keys SET is_active = false, updated_at = NOW() WHERE id = %s",
                        (key_id,)
                    )
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to delete API key {key_id}: {str(e)}")