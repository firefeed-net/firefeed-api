"""
Command Line Interface for FireFeed API

This module provides CLI commands for managing the application.
"""

import asyncio
import click
from loguru import logger

from .config.environment import get_settings
from .config.logging_config import setup_logging
from .main import app
from .database.migration import run_migrations
from .services.maintenance_service import MaintenanceService
from .services.translation_service import TranslationService
from .services.media_service import MediaService
from .services.email_service import EmailService
from .services.text_analysis_service import TextAnalysisService
from .services.database_service import DatabaseService
from .services.cache_service import cache_service
from .background_tasks import start_background_tasks, stop_background_tasks


@click.group()
def cli():
    """FireFeed API CLI"""
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def run(host: str, port: int, reload: bool, debug: bool):
    """Run the FireFeed API server"""
    import uvicorn
    
    settings = get_settings()
    
    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format
    )
    
    logger.info(f"Starting FireFeed API server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Auto-reload: {reload}")
    
    uvicorn.run(
        "firefeed-api.main:app",
        host=host,
        port=port,
        reload=reload,
        debug=debug,
        log_level=settings.log_level.lower()
    )


@cli.command()
def migrate():
    """Run database migrations"""
    logger.info("Running database migrations...")
    
    try:
        asyncio.run(run_migrations())
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Database migrations failed: {e}")
        raise


@cli.command()
@click.option('--force', is_flag=True, help='Force cleanup without confirmation')
def cleanup(force: bool):
    """Clean up expired data"""
    if not force:
        click.confirm('This will clean up expired data. Continue?', abort=True)
    
    logger.info("Starting cleanup of expired data...")
    
    async def cleanup_async():
        try:
            # Initialize cache service
            await cache_service.connect()
            
            # Clean up cache
            await cache_service.cleanup_expired()
            logger.info("Cache cleanup completed")
            
            # Initialize database service
            db_service = DatabaseService()
            
            # Clean up expired sessions and tokens
            await db_service.cleanup_expired_sessions()
            await db_service.cleanup_expired_tokens()
            logger.info("Database cleanup completed")
            
            # Disconnect cache
            await cache_service.disconnect()
            
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise
    
    asyncio.run(cleanup_async())


@cli.command()
def maintenance():
    """Run maintenance tasks"""
    logger.info("Starting maintenance tasks...")
    
    async def maintenance_async():
        try:
            # Initialize services
            maintenance_service = MaintenanceService()
            
            # Run maintenance tasks
            await maintenance_service.run_maintenance_tasks()
            logger.info("Maintenance tasks completed successfully")
        except Exception as e:
            logger.error(f"Maintenance tasks failed: {e}")
            raise
    
    asyncio.run(maintenance_async())


@cli.command()
@click.option('--task', type=click.Choice(['translation', 'media', 'email', 'analysis']), help='Task to process')
def process(task: str):
    """Process background tasks"""
    logger.info(f"Processing {task} tasks...")
    
    async def process_async():
        try:
            if task == 'translation':
                translation_service = TranslationService()
                await translation_service.process_pending_translations()
                logger.info("Translation tasks completed")
            
            elif task == 'media':
                media_service = MediaService()
                await media_service.process_pending_media()
                logger.info("Media tasks completed")
            
            elif task == 'email':
                email_service = EmailService()
                await email_service.send_scheduled_emails()
                logger.info("Email tasks completed")
            
            elif task == 'analysis':
                text_analysis_service = TextAnalysisService()
                await text_analysis_service.update_analysis()
                logger.info("Text analysis tasks completed")
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            raise
    
    asyncio.run(process_async())


@cli.command()
def health():
    """Check application health"""
    logger.info("Checking application health...")
    
    async def health_async():
        try:
            # Check cache health
            await cache_service.connect()
            cache_stats = await cache_service.get_stats()
            await cache_service.disconnect()
            
            logger.info(f"Cache status: {cache_stats.get('status', 'unknown')}")
            
            # Check database health
            db_service = DatabaseService()
            db_health = await db_service.check_health()
            logger.info(f"Database status: {db_health.get('status', 'unknown')}")
            
            logger.info("Health check completed successfully")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    asyncio.run(health_async())


@cli.command()
def metrics():
    """Show application metrics"""
    logger.info("Showing application metrics...")
    
    async def metrics_async():
        try:
            # Get cache metrics
            await cache_service.connect()
            cache_stats = await cache_service.get_stats()
            await cache_service.disconnect()
            
            logger.info("Cache Metrics:")
            for key, value in cache_stats.items():
                logger.info(f"  {key}: {value}")
            
            # Get database metrics
            db_service = DatabaseService()
            db_metrics = await db_service.get_metrics()
            
            logger.info("Database Metrics:")
            for key, value in db_metrics.items():
                logger.info(f"  {key}: {value}")
            
            logger.info("Metrics collection completed")
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            raise
    
    asyncio.run(metrics_async())


@cli.command()
@click.option('--background', is_flag=True, help='Run in background mode')
def start(background: bool):
    """Start the application"""
    if background:
        logger.info("Starting FireFeed API in background mode...")
        
        async def start_background():
            try:
                # Initialize cache service
                await cache_service.connect()
                
                # Start background tasks
                task_manager = None  # Create task manager instance
                await start_background_tasks(task_manager)
                
                logger.info("FireFeed API started in background mode")
                
                # Keep running
                while True:
                    await asyncio.sleep(60)
                    
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                await stop_background_tasks()
                await cache_service.disconnect()
                logger.info("FireFeed API stopped")
            except Exception as e:
                logger.error(f"Background mode failed: {e}")
                raise
        
        asyncio.run(start_background())
    else:
        # Run in foreground mode
        run()


@cli.command()
def stop():
    """Stop the application"""
    logger.info("Stopping FireFeed API...")
    # Implementation for stopping the application
    logger.info("FireFeed API stopped")


@cli.command()
def version():
    """Show application version"""
    settings = get_settings()
    logger.info(f"FireFeed API v{settings.project_version}")
    logger.info(f"Description: {settings.project_description}")


if __name__ == '__main__':
    cli()