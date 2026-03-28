"""
Database migrations for FireFeed API

This module provides database migration utilities for the application.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection
from sqlalchemy.exc import SQLAlchemyError

from .migration import Migration, MigrationManager
from .models import Base
from .config.environment import get_settings


class DatabaseMigrationManager:
    """Database migration manager for FireFeed API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.migration_manager = MigrationManager()
        self.engine: Optional[AsyncEngine] = None
    
    async def connect(self) -> None:
        """Connect to database"""
        try:
            self.engine = create_async_engine(
                self.settings.database_url,
                echo=False,
                pool_size=20,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600
            )
            logger.info("Connected to database for migrations")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from database"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Disconnected from database")
    
    async def create_tables(self) -> None:
        """Create database tables"""
        if not self.engine:
            await self.connect()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """Drop database tables"""
        if not self.engine:
            await self.connect()
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    async def run_migrations(self) -> None:
        """Run database migrations"""
        if not self.engine:
            await self.connect()
        
        try:
            # Run the migration manager
            await self.migration_manager.run_migrations()
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Database migrations failed: {e}")
            raise
    
    async def rollback_migration(self, migration_id: str) -> None:
        """Rollback specific migration"""
        if not self.engine:
            await self.connect()
        
        try:
            await self.migration_manager.rollback_migration(migration_id)
            logger.info(f"Migration {migration_id} rolled back successfully")
        except Exception as e:
            logger.error(f"Failed to rollback migration {migration_id}: {e}")
            raise
    
    async def get_migration_status(self) -> List[Dict[str, Any]]:
        """Get migration status"""
        if not self.engine:
            await self.connect()
        
        try:
            return await self.migration_manager.get_migration_status()
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            raise
    
    async def create_migration(self, name: str, description: str) -> str:
        """Create new migration"""
        try:
            migration_id = await self.migration_manager.create_migration(name, description)
            logger.info(f"Migration {migration_id} created successfully")
            return migration_id
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise
    
    async def add_migration_step(
        self,
        migration_id: str,
        step_name: str,
        sql: str,
        rollback_sql: Optional[str] = None
    ) -> None:
        """Add migration step"""
        try:
            await self.migration_manager.add_migration_step(
                migration_id,
                step_name,
                sql,
                rollback_sql
            )
            logger.info(f"Migration step added to {migration_id}")
        except Exception as e:
            logger.error(f"Failed to add migration step: {e}")
            raise
    
    async def execute_sql(self, sql: str) -> Any:
        """Execute raw SQL"""
        if not self.engine:
            await self.connect()
        
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text(sql))
                await conn.commit()
                return result
        except Exception as e:
            logger.error(f"Failed to execute SQL: {e}")
            raise
    
    async def check_health(self) -> Dict[str, Any]:
        """Check database health"""
        if not self.engine:
            await self.connect()
        
        try:
            async with self.engine.connect() as conn:
                # Test connection
                await conn.execute(text("SELECT 1"))
                
                # Get database info
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                
                return {
                    "status": "healthy",
                    "version": version,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global migration manager instance
migration_manager = DatabaseMigrationManager()


async def run_migrations() -> None:
    """Run database migrations"""
    await migration_manager.run_migrations()


async def create_tables() -> None:
    """Create database tables"""
    await migration_manager.create_tables()


async def drop_tables() -> None:
    """Drop database tables"""
    await migration_manager.drop_tables()


async def check_health() -> Dict[str, Any]:
    """Check database health"""
    return await migration_manager.check_health()


# Migration scripts
MIGRATION_SCRIPTS = {
    "001_initial_schema": """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            language VARCHAR(10) DEFAULT 'en',
            is_active BOOLEAN DEFAULT true,
            is_verified BOOLEAN DEFAULT false,
            is_deleted BOOLEAN DEFAULT false,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS api_keys (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            key_hash VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS sources (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            url VARCHAR(500) NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS rss_feeds (
            id SERIAL PRIMARY KEY,
            source_id INTEGER REFERENCES sources(id),
            category_id INTEGER REFERENCES categories(id),
            title VARCHAR(500) NOT NULL,
            description TEXT,
            url VARCHAR(500) NOT NULL,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS rss_data (
            news_id VARCHAR(255) PRIMARY KEY,
            original_title TEXT NOT NULL,
            original_content TEXT,
            original_language VARCHAR(10) DEFAULT 'en',
            category_id INTEGER REFERENCES categories(id),
            image_filename VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rss_feed_id INTEGER REFERENCES rss_feeds(id),
            embedding VECTOR(1536),
            source_url VARCHAR(500),
            video_filename VARCHAR(255)
        );
        
        CREATE TABLE IF NOT EXISTS user_categories (
            user_id INTEGER REFERENCES users(id),
            category_id INTEGER REFERENCES categories(id),
            PRIMARY KEY (user_id, category_id)
        );
        
        CREATE TABLE IF NOT EXISTS user_rss_feeds (
            user_id INTEGER REFERENCES users(id),
            rss_feed_id INTEGER REFERENCES rss_feeds(id),
            PRIMARY KEY (user_id, rss_feed_id)
        );
        
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            session_token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            token_hash VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS email_verification_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            token_hash VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_rss_data_created_at ON rss_data(created_at);
        CREATE INDEX IF NOT EXISTS idx_rss_data_category_id ON rss_data(category_id);
        CREATE INDEX IF NOT EXISTS idx_rss_data_rss_feed_id ON rss_data(rss_feed_id);
        CREATE INDEX IF NOT EXISTS idx_rss_data_original_language ON rss_data(original_language);
    """,
    
    "002_add_telegram_support": """
        CREATE TABLE IF NOT EXISTS telegram_users (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            telegram_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            language_code VARCHAR(10),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS telegram_chats (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            chat_id BIGINT NOT NULL,
            chat_type VARCHAR(50) NOT NULL,
            title VARCHAR(255),
            username VARCHAR(255),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS telegram_messages (
            id SERIAL PRIMARY KEY,
            telegram_chat_id INTEGER REFERENCES telegram_chats(id),
            message_id BIGINT NOT NULL,
            message_type VARCHAR(50) NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_telegram_users_telegram_id ON telegram_users(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_telegram_chats_chat_id ON telegram_chats(chat_id);
    """,
    
    "003_add_translation_support": """
        CREATE TABLE IF NOT EXISTS translations (
            id SERIAL PRIMARY KEY,
            rss_item_id VARCHAR(255) REFERENCES rss_data(news_id),
            source_language VARCHAR(10) NOT NULL,
            target_language VARCHAR(10) NOT NULL,
            translated_title TEXT,
            translated_content TEXT,
            translation_provider VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS translation_cache (
            id SERIAL PRIMARY KEY,
            text_hash VARCHAR(255) UNIQUE NOT NULL,
            source_language VARCHAR(10) NOT NULL,
            target_language VARCHAR(10) NOT NULL,
            translated_text TEXT,
            translation_provider VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_translations_rss_item_id ON translations(rss_item_id);
        CREATE INDEX IF NOT EXISTS idx_translations_source_language ON translations(source_language);
        CREATE INDEX IF NOT EXISTS idx_translations_target_language ON translations(target_language);
        CREATE INDEX IF NOT EXISTS idx_translation_cache_text_hash ON translation_cache(text_hash);
    """,
    
    "004_add_media_support": """
        CREATE TABLE IF NOT EXISTS media_files (
            id SERIAL PRIMARY KEY,
            rss_item_id VARCHAR(255) REFERENCES rss_data(news_id),
            file_type VARCHAR(50) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER,
            mime_type VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS media_cache (
            id SERIAL PRIMARY KEY,
            url_hash VARCHAR(255) UNIQUE NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER,
            mime_type VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_media_files_rss_item_id ON media_files(rss_item_id);
        CREATE INDEX IF NOT EXISTS idx_media_files_file_type ON media_files(file_type);
        CREATE INDEX IF NOT EXISTS idx_media_cache_url_hash ON media_cache(url_hash);
    """
}


async def create_initial_migration() -> None:
    """Create initial migration"""
    try:
        migration_id = await migration_manager.create_migration(
            "001_initial_schema",
            "Initial database schema"
        )
        
        await migration_manager.add_migration_step(
            migration_id,
            "create_tables",
            MIGRATION_SCRIPTS["001_initial_schema"]
        )
        
        logger.info("Initial migration created successfully")
    except Exception as e:
        logger.error(f"Failed to create initial migration: {e}")
        raise


async def create_telegram_migration() -> None:
    """Create Telegram support migration"""
    try:
        migration_id = await migration_manager.create_migration(
            "002_add_telegram_support",
            "Add Telegram support tables"
        )
        
        await migration_manager.add_migration_step(
            migration_id,
            "create_telegram_tables",
            MIGRATION_SCRIPTS["002_add_telegram_support"]
        )
        
        logger.info("Telegram migration created successfully")
    except Exception as e:
        logger.error(f"Failed to create Telegram migration: {e}")
        raise


async def create_translation_migration() -> None:
    """Create translation support migration"""
    try:
        migration_id = await migration_manager.create_migration(
            "003_add_translation_support",
            "Add translation support tables"
        )
        
        await migration_manager.add_migration_step(
            migration_id,
            "create_translation_tables",
            MIGRATION_SCRIPTS["003_add_translation_support"]
        )
        
        logger.info("Translation migration created successfully")
    except Exception as e:
        logger.error(f"Failed to create translation migration: {e}")
        raise


async def create_media_migration() -> None:
    """Create media support migration"""
    try:
        migration_id = await migration_manager.create_migration(
            "004_add_media_support",
            "Add media support tables"
        )
        
        await migration_manager.add_migration_step(
            migration_id,
            "create_media_tables",
            MIGRATION_SCRIPTS["004_add_media_support"]
        )
        
        logger.info("Media migration created successfully")
    except Exception as e:
        logger.error(f"Failed to create media migration: {e}")
        raise


async def create_all_migrations() -> None:
    """Create all migrations"""
    await create_initial_migration()
    await create_telegram_migration()
    await create_translation_migration()
    await create_media_migration()
    logger.info("All migrations created successfully")