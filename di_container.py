"""
Dependency Injection Container for FireFeed API

This module provides the dependency injection container configuration
for the entire application using the dependency-injector library.
"""

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .config.environment import get_settings
from .config.logging_config import setup_logging
from .services.public_api_client import PublicAPIClient
from .services.user_service import UserService
from .services.rss_service import RSSService
from .services.category_service import CategoryService
from .services.source_service import SourceService
from .services.translation_service import TranslationService
from .services.media_service import MediaService
from .services.email_service import EmailService
from .services.maintenance_service import MaintenanceService
from .services.database_service import DatabaseService
from .services.text_analysis_service import TextAnalysisService
from .services.api_key_service import APIKeyService
from .services.telegram_service import TelegramService
from .cache import cache_service
from .background_tasks import BackgroundTaskManager


class Container(containers.DeclarativeContainer):
    """Dependency injection container for FireFeed API"""
    
    wiring_config = containers.WiringConfiguration(
        modules=[
            "firefeed-api.main",
            "firefeed-api.routers.public_auth",
            "firefeed-api.routers.public_users", 
            "firefeed-api.routers.public_rss",
            "firefeed-api.services.public_api_client",
            "firefeed-api.services.user_service",
            "firefeed-api.services.rss_service",
            "firefeed-api.services.category_service",
            "firefeed-api.services.source_service",
            "firefeed-api.services.translation_service",
            "firefeed-api.services.media_service",
            "firefeed-api.services.email_service",
            "firefeed-api.services.maintenance_service",
            "firefeed-api.services.database_service",
            "firefeed-api.services.text_analysis_service",
            "firefeed-api.services.api_key_service",
            "firefeed-api.services.telegram_service",
            "firefeed-api.background_tasks"
        ]
    )
    
    # Configuration
    config = providers.Configuration()
    
    # Logging
    logging = providers.Resource(
        setup_logging,
        log_level=config.log_level,
        log_format=config.log_format
    )
    
    # Cache service
    cache_service = providers.Singleton(
        lambda: cache_service
    )
    
    # Services
    public_api_client = providers.Factory(
        PublicAPIClient,
        base_url=config.internal_api_url,
        service_token=config.internal_api_token
    )
    
    user_service = providers.Factory(
        UserService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    rss_service = providers.Factory(
        RSSService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    category_service = providers.Factory(
        CategoryService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    source_service = providers.Factory(
        SourceService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    translation_service = providers.Factory(
        TranslationService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    media_service = providers.Factory(
        MediaService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    email_service = providers.Factory(
        EmailService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    maintenance_service = providers.Factory(
        MaintenanceService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    database_service = providers.Factory(
        DatabaseService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    text_analysis_service = providers.Factory(
        TextAnalysisService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    api_key_service = providers.Factory(
        APIKeyService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    telegram_service = providers.Factory(
        TelegramService,
        public_api_client=public_api_client,
        cache_service=cache_service
    )
    
    # Background task manager
    background_task_manager = providers.Factory(
        BackgroundTaskManager,
        maintenance_service=maintenance_service,
        translation_service=translation_service,
        media_service=media_service,
        email_service=email_service,
        text_analysis_service=text_analysis_service,
        database_service=database_service,
        cache_service=cache_service
    )


# Global container instance
container = Container()


# Dependency injection providers
@inject
def get_user_service(
    user_service: UserService = Provide[container.user_service]
) -> UserService:
    """Get user service dependency"""
    return user_service


@inject 
def get_rss_service(
    rss_service: RSSService = Provide[container.rss_service]
) -> RSSService:
    """Get RSS service dependency"""
    return rss_service


@inject
def get_category_service(
    category_service: CategoryService = Provide[container.category_service]
) -> CategoryService:
    """Get category service dependency"""
    return category_service


@inject
def get_source_service(
    source_service: SourceService = Provide[container.source_service]
) -> SourceService:
    """Get source service dependency"""
    return source_service


@inject
def get_translation_service(
    translation_service: TranslationService = Provide[container.translation_service]
) -> TranslationService:
    """Get translation service dependency"""
    return translation_service


@inject
def get_media_service(
    media_service: MediaService = Provide[container.media_service]
) -> MediaService:
    """Get media service dependency"""
    return media_service


@inject
def get_email_service(
    email_service: EmailService = Provide[container.email_service]
) -> EmailService:
    """Get email service dependency"""
    return email_service


@inject
def get_maintenance_service(
    maintenance_service: MaintenanceService = Provide[container.maintenance_service]
) -> MaintenanceService:
    """Get maintenance service dependency"""
    return maintenance_service


@inject
def get_database_service(
    database_service: DatabaseService = Provide[container.database_service]
) -> DatabaseService:
    """Get database service dependency"""
    return database_service


@inject
def get_text_analysis_service(
    text_analysis_service: TextAnalysisService = Provide[container.text_analysis_service]
) -> TextAnalysisService:
    """Get text analysis service dependency"""
    return text_analysis_service


@inject
def get_api_key_service(
    api_key_service: APIKeyService = Provide[container.api_key_service]
) -> APIKeyService:
    """Get API key service dependency"""
    return api_key_service


@inject
def get_telegram_service(
    telegram_service: TelegramService = Provide[container.telegram_service]
) -> TelegramService:
    """Get Telegram service dependency"""
    return telegram_service


@inject
def get_background_task_manager(
    background_task_manager: BackgroundTaskManager = Provide[container.background_task_manager]
) -> BackgroundTaskManager:
    """Get background task manager dependency"""
    return background_task_manager


# Type annotations for dependency injection
UserServiceDep = Provide[container.user_service]
RSSServiceDep = Provide[container.rss_service]
CategoryServiceDep = Provide[container.category_service]
SourceServiceDep = Provide[container.source_service]
TranslationServiceDep = Provide[container.translation_service]
MediaServiceDep = Provide[container.media_service]
EmailServiceDep = Provide[container.email_service]
MaintenanceServiceDep = Provide[container.maintenance_service]
DatabaseServiceDep = Provide[container.database_service]
TextAnalysisServiceDep = Provide[container.text_analysis_service]
APIKeyServiceDep = Provide[container.api_key_service]
TelegramServiceDep = Provide[container.telegram_service]
BackgroundTaskManagerDep = Provide[container.background_task_manager]