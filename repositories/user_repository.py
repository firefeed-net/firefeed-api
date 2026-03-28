"""User repository implementation for FireFeed API."""
import logging
from typing import List, Dict, Any, Optional
from .interfaces import IUserRepository
from firefeed_core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class UserRepository(IUserRepository):
    """PostgreSQL implementation of user repository."""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, email, password_hash, language, is_active, created_at, updated_at, is_verified, is_deleted FROM users WHERE email = %s AND is_deleted = false",
                        (email,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "email": row[1],
                            "password_hash": row[2],
                            "language": row[3],
                            "is_active": row[4],
                            "created_at": row[5],
                            "updated_at": row[6],
                            "is_verified": row[7],
                            "is_deleted": row[8]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get user by email {email}: {str(e)}")

    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "SELECT id, email, password_hash, language, is_active, created_at, updated_at, is_verified, is_deleted FROM users WHERE id = %s AND is_deleted = false",
                        (user_id,)
                    )
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "email": row[1],
                            "password_hash": row[2],
                            "language": row[3],
                            "is_active": row[4],
                            "created_at": row[5],
                            "updated_at": row[6],
                            "is_verified": row[7],
                            "is_deleted": row[8]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to get user by ID {user_id}: {str(e)}")

    async def create_user(self, email: str, password_hash: str, language: str = 'en') -> Optional[Dict[str, Any]]:
        """Create new user."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("BEGIN")
                
                try:
                    # Check if user already exists
                    await cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if await cur.fetchone():
                        await cur.execute("ROLLBACK")
                        return {"error": "duplicate_email"}
                    
                    # Create user
                    await cur.execute(
                        "INSERT INTO users (email, password_hash, language) VALUES (%s, %s, %s) RETURNING id, email, language, is_active, created_at, is_verified, is_deleted",
                        (email, password_hash, language)
                    )
                    row = await cur.fetchone()
                    
                    await cur.execute("COMMIT")
                    
                    if row:
                        return {
                            "id": row[0],
                            "email": row[1],
                            "language": row[2],
                            "is_active": row[3],
                            "created_at": row[4],
                            "is_verified": row[5],
                            "is_deleted": row[6]
                        }
                    
                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise DatabaseException(f"Failed to create user: {str(e)}")
        
        return None

    async def update_user(self, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user."""
        set_parts = []
        values = []
        for key, value in update_data.items():
            set_parts.append(f"{key} = %s")
            values.append(value)
        
        query = f"UPDATE users SET {', '.join(set_parts)}, updated_at = NOW() WHERE id = %s AND is_deleted = false RETURNING id, email, language, is_active, updated_at, is_verified"
        values.append(user_id)
        
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(query, values)
                    row = await cur.fetchone()
                    if row:
                        return {
                            "id": row[0],
                            "email": row[1],
                            "language": row[2],
                            "is_active": row[3],
                            "updated_at": row[4],
                            "is_verified": row[5]
                        }
                    return None
                except Exception as e:
                    raise DatabaseException(f"Failed to update user {user_id}: {str(e)}")

    async def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete)."""
        async with self.db_pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "UPDATE users SET is_deleted = true, updated_at = NOW() WHERE id = %s",
                        (user_id,)
                    )
                    return cur.rowcount > 0
                except Exception as e:
                    raise DatabaseException(f"Failed to delete user {user_id}: {str(e)}")