"""
Dependency injection container setup for FireFeed API

This module sets up the dependency injection container using
dependency-injector for managing service dependencies.
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .config.environment import get_environment
from .config.database_config import DatabaseConfig
from .config.redis_config import RedisConfig
from .services.database_service import DatabaseService
from .services.redis_service import RedisService
from .services.cache_service import CacheService
from .services.session_service import SessionService
from .services.rate_limit_service import RateLimitService
from .services.user_service import UserService
from .services.api_key_service import ApiKeyService
from .services.category_service import CategoryService
from .services.rss_service import RssService
from .services.source_service import SourceService
from .services.email_service import EmailService
from .services.maintenance_service import MaintenanceService
from .services.media_service import MediaService
from .services.text_analysis_service import TextAnalysisService
from .services.translation_service import TranslationService
from .services.telegram_service import TelegramService


class Container(containers.DeclarativeContainer):
    """Dependency injection container for FireFeed API"""
    
    config = providers.Configuration()
    
    # Configuration providers
    database_config = providers.Factory(
        DatabaseConfig.from_env
    )
    
    redis_config = providers.Factory(
        RedisConfig.from_env
    )
    
    # Core services
    database_service = providers.Factory(
        DatabaseService,
        config=database_config
    )
    
    redis_service = providers.Factory(
        RedisService,
        config=redis_config
    )
    
    # Redis-based services
    cache_service = providers.Factory(
        CacheService,
        redis_service=redis_service
    )
    
    session_service = providers.Factory(
        SessionService,
        redis_service=redis_service
    )
    
    rate_limit_service = providers.Factory(
        RateLimitService,
        redis_service=redis_service
    )
    
    # Business services
    user_service = providers.Factory(
        UserService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    api_key_service = providers.Factory(
        ApiKeyService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    category_service = providers.Factory(
        CategoryService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    rss_service = providers.Factory(
        RssService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    source_service = providers.Factory(
        SourceService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    email_service = providers.Factory(
        EmailService
    )
    
    maintenance_service = providers.Factory(
        MaintenanceService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    media_service = providers.Factory(
        MediaService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    text_analysis_service = providers.Factory(
        TextAnalysisService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    translation_service = providers.Factory(
        TranslationService,
        db_service=database_service,
        cache_service=cache_service
    )
    
    telegram_service = providers.Factory(
        TelegramService,
        db_service=database_service,
        cache_service=cache_service
    )


# Global container instance
container = Container()


@inject
def setup_container():
    """Setup and initialize the dependency injection container"""
    # Configure container
    container.config.from_dict({
        'environment': get_environment(),
    })
    
    # Initialize container
    container.wire(
        modules=[
            # Routers
            'routers.public_auth',
            'routers.public_users', 
            'routers.public_rss',
            'routers.internal',
            
            # Middleware
            'middleware.public_auth',
            
            # Services
            'services.user_service',
            'services.api_key_service',
            'services.category_service',
            'services.rss_service',
            'services.source_service',
            'services.email_service',
            'services.maintenance_service',
            'services.media_service',
            'services.text_analysis_service',
            'services.translation_service',
            'services.telegram_service',
            
            # Dependencies
            'dependencies',
        ]
    )
    
    return container


def get_container() -> Container:
    """Get the global container instance"""
    return container


# Wiring decorators for dependency injection
def inject_db_service(func):
    """Decorator to inject database service"""
    return inject(func, db_service=Provide[Container.database_service])


def inject_redis_service(func):
    """Decorator to inject Redis service"""
    return inject(func, redis_service=Provide[Container.redis_service])


def inject_cache_service(func):
    """Decorator to inject cache service"""
    return inject(func, cache_service=Provide[Container.cache_service])


def inject_session_service(func):
    """Decorator to inject session service"""
    return inject(func, session_service=Provide[Container.session_service])


def inject_rate_limit_service(func):
    """Decorator to inject rate limiting service"""
    return inject(func, rate_limit_service=Provide[Container.rate_limit_service])


def inject_user_service(func):
    """Decorator to inject user service"""
    return inject(func, user_service=Provide[Container.user_service])


def inject_api_key_service(func):
    """Decorator to inject API key service"""
    return inject(func, api_key_service=Provide[Container.api_key_service])


def inject_category_service(func):
    """Decorator to inject category service"""
    return inject(func, category_service=Provide[Container.category_service])


def inject_rss_service(func):
    """Decorator to inject RSS service"""
    return inject(func, rss_service=Provide[Container.rss_service])


def inject_source_service(func):
    """Decorator to inject source service"""
    return inject(func, source_service=Provide[Container.source_service])


def inject_email_service(func):
    """Decorator to inject email service"""
    return inject(func, email_service=Provide[Container.email_service])


def inject_maintenance_service(func):
    """Decorator to inject maintenance service"""
    return inject(func, maintenance_service=Provide[Container.maintenance_service])


def inject_media_service(func):
    """Decorator to inject media service"""
    return inject(func, media_service=Provide[Container.media_service])


def inject_text_analysis_service(func):
    """Decorator to inject text analysis service"""
    return inject(func, text_analysis_service=Provide[Container.text_analysis_service])


def inject_translation_service(func):
    """Decorator to inject translation service"""
    return inject(func, translation_service=Provide[Container.translation_service])


def inject_telegram_service(func):
    """Decorator to inject Telegram service"""
    return inject(func, telegram_service=Provide[Container.telegram_service])