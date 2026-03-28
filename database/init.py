"""
Database initialization for FireFeed API

This module provides database initialization utilities for the application.
"""

import asyncio
from typing import Optional
from loguru import logger

from .migrations import (
    migration_manager,
    create_tables,
    drop_tables,
    run_migrations,
    create_all_migrations
)
from .models import Base
from .config.environment import get_settings


class DatabaseInitializer:
    """Database initializer for FireFeed API"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def initialize(self, force: bool = False) -> None:
        """
        Initialize database
        
        Args:
            force: Whether to force initialization (drop and recreate)
        """
        try:
            logger.info("Initializing database...")
            
            # Connect to database
            await migration_manager.connect()
            
            if force:
                logger.info("Force initialization enabled - dropping existing tables")
                await drop_tables()
            
            # Create tables if they don't exist
            await create_tables()
            
            # Create migrations
            await create_all_migrations()
            
            # Run migrations
            await run_migrations()
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
        finally:
            # Disconnect from database
            await migration_manager.disconnect()
    
    async def check_health(self) -> dict:
        """Check database health"""
        try:
            await migration_manager.connect()
            health = await migration_manager.check_health()
            await migration_manager.disconnect()
            return health
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": None
            }
    
    async def get_migration_status(self) -> list:
        """Get migration status"""
        try:
            await migration_manager.connect()
            status = await migration_manager.get_migration_status()
            await migration_manager.disconnect()
            return status
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return []
    
    async def create_migration(self, name: str, description: str) -> str:
        """Create new migration"""
        try:
            await migration_manager.connect()
            migration_id = await migration_manager.create_migration(name, description)
            await migration_manager.disconnect()
            return migration_id
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise


# Global database initializer instance
database_initializer = DatabaseInitializer()


async def initialize_database(force: bool = False) -> None:
    """Initialize database"""
    await database_initializer.initialize(force)


async def check_database_health() -> dict:
    """Check database health"""
    return await database_initializer.check_health()


async def get_database_migration_status() -> list:
    """Get database migration status"""
    return await database_initializer.get_migration_status()


async def create_database_migration(name: str, description: str) -> str:
    """Create new database migration"""
    return await database_initializer.create_migration(name, description)


# Database initialization scripts
INITIALIZATION_SCRIPTS = {
    "create_extensions": """
        -- Create required extensions
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";
        CREATE EXTENSION IF NOT EXISTS "vector";
    """,
    
    "create_functions": """
        -- Create helper functions
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """,
    
    "create_triggers": """
        -- Create triggers for updated_at
        DROP TRIGGER IF EXISTS update_users_updated_at ON users;
        CREATE TRIGGER update_users_updated_at 
            BEFORE UPDATE ON users 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_categories_updated_at ON categories;
        CREATE TRIGGER update_categories_updated_at 
            BEFORE UPDATE ON categories 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_rss_feeds_updated_at ON rss_feeds;
        CREATE TRIGGER update_rss_feeds_updated_at 
            BEFORE UPDATE ON rss_feeds 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_rss_data_updated_at ON rss_data;
        CREATE TRIGGER update_rss_data_updated_at 
            BEFORE UPDATE ON rss_data 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    """,
    
    "create_indexes": """
        -- Create additional indexes for performance
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
        CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
        CREATE INDEX IF NOT EXISTS idx_rss_feeds_source_id ON rss_feeds(source_id);
        CREATE INDEX IF NOT EXISTS idx_rss_feeds_url ON rss_feeds(url);
        CREATE INDEX IF NOT EXISTS idx_rss_data_news_id ON rss_data(news_id);
        CREATE INDEX IF NOT EXISTS idx_rss_data_source_url ON rss_data(source_url);
        CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
        CREATE INDEX IF NOT EXISTS idx_user_categories_user_id ON user_categories(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_categories_category_id ON user_categories(category_id);
        CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_user_id ON user_rss_feeds(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_rss_feeds_rss_feed_id ON user_rss_feeds(rss_feed_id);
    """,
    
    "create_views": """
        -- Create views for common queries
        CREATE OR REPLACE VIEW user_rss_items AS
        SELECT 
            rd.*,
            rf.title as feed_title,
            rf.description as feed_description,
            c.name as category_name,
            s.name as source_name
        FROM rss_data rd
        JOIN rss_feeds rf ON rd.rss_feed_id = rf.id
        JOIN categories c ON rd.category_id = c.id
        JOIN sources s ON rf.source_id = s.id;
        
        CREATE OR REPLACE VIEW user_categories_with_feeds AS
        SELECT 
            uc.user_id,
            c.id as category_id,
            c.name as category_name,
            c.description as category_description,
            COUNT(rf.id) as feed_count
        FROM user_categories uc
        JOIN categories c ON uc.category_id = c.id
        LEFT JOIN rss_feeds rf ON c.id = rf.category_id
        GROUP BY uc.user_id, c.id, c.name, c.description;
    """
}


async def run_initialization_scripts() -> None:
    """Run database initialization scripts"""
    try:
        await migration_manager.connect()
        
        for script_name, script_sql in INITIALIZATION_SCRIPTS.items():
            logger.info(f"Running initialization script: {script_name}")
            await migration_manager.execute_sql(script_sql)
        
        logger.info("Database initialization scripts completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization scripts failed: {e}")
        raise
    finally:
        await migration_manager.disconnect()


async def setup_database() -> None:
    """Setup complete database"""
    try:
        logger.info("Setting up database...")
        
        # Initialize database
        await initialize_database()
        
        # Run initialization scripts
        await run_initialization_scripts()
        
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise


# Database seeding
SEED_DATA = {
    "categories": [
        {"name": "Technology", "description": "Technology news and updates"},
        {"name": "Science", "description": "Scientific discoveries and research"},
        {"name": "Business", "description": "Business news and financial updates"},
        {"name": "Health", "description": "Health and medical news"},
        {"name": "Sports", "description": "Sports news and events"},
        {"name": "Entertainment", "description": "Entertainment news and media"},
        {"name": "Politics", "description": "Political news and analysis"},
        {"name": "World", "description": "International news and events"}
    ],
    
    "sources": [
        {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml"},
        {"name": "Reuters", "url": "http://feeds.reuters.com/reuters/topNews"},
        {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss"},
        {"name": "TechCrunch", "url": "http://feeds.feedburner.com/TechCrunch/"},
        {"name": "Hacker News", "url": "http://hnrss.org/frontpage"},
        {"name": "ArXiv", "url": "http://export.arxiv.org/rss/cs.AI"},
        {"name": "NASA", "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss"},
        {"name": "World Health Organization", "url": "https://www.who.int/feeds/who_rss_feed/en/"},
        {"name": "ESPN", "url": "https://www.espn.com/espn/rss/news"},
        {"name": "IMDB", "url": "http://www.imdb.com/rss/news/"},
        {"name": "BBC Sport", "url": "http://feeds.bbci.co.uk/sport/rss.xml"},
        {"name": "Financial Times", "url": "https://www.ft.com/?format=rss"}
    ]
}


async def seed_database() -> None:
    """Seed database with initial data"""
    try:
        await migration_manager.connect()
        
        # Seed categories
        for category in SEED_DATA["categories"]:
            sql = """
                INSERT INTO categories (name, description)
                VALUES (:name, :description)
                ON CONFLICT (name) DO NOTHING
            """
            await migration_manager.execute_sql(sql, category)
        
        # Seed sources
        for source in SEED_DATA["sources"]:
            sql = """
                INSERT INTO sources (name, url)
                VALUES (:name, :url)
                ON CONFLICT (url) DO NOTHING
            """
            await migration_manager.execute_sql(sql, source)
        
        logger.info("Database seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        raise
    finally:
        await migration_manager.disconnect()


async def setup_and_seed_database() -> None:
    """Setup and seed complete database"""
    try:
        logger.info("Setting up and seeding database...")
        
        # Setup database
        await setup_database()
        
        # Seed database
        await seed_database()
        
        logger.info("Database setup and seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Database setup and seeding failed: {e}")
        raise