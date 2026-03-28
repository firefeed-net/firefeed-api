"""Database service for FireFeed API."""
import logging
from typing import Optional
import aiopg
from config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for managing database connections."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
    
    async def connect(self):
        """Connect to database."""
        try:
            dsn = f"postgresql://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.name}"
            self.pool = await aiopg.create_pool(
                dsn=dsn,
                minsize=self.config.minsize,
                maxsize=self.config.maxsize
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from database."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection closed")

    async def initialize(self):
        """Initialize database connections and pool."""
        await self.connect()

    async def close(self):
        """Close database connections and pool."""
        await self.disconnect()

    async def health_check(self):
        """Perform a simple health check query against the database."""
        try:
            if self.pool is None:
                await self.connect()
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    row = await cur.fetchone()
            return {"status": "ok", "details": {"result": row[0] if row else None}}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_pool(self):
        """Get database pool."""
        return self.pool