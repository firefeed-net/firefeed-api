"""
Models package for FireFeed API.

This package contains all the data models for the application.
Models are imported from firefeed_core where applicable to avoid duplication.

Note: Unified models are now imported from firefeed_core for consistency across services.
Local definitions are only kept for models that don't exist in firefeed_core.
"""

# Import unified models from firefeed_core (base_models.py is the single source of truth)
from firefeed_core.models.base_models import (
    UserResponse,
    UserUpdate,
    Token,
)
# UserCreate is defined in base_models as UserCreateRequest, use that
from firefeed_core.models.base_models import UserCreate as UserCreate
from firefeed_core.models.user_models import UserLogin
from firefeed_core.models.base_models import (
    Category,
    CategoryItem,
    Source,
    SourceItem,
    RSSFeed,
    RSSItem,
    UserRSSFeedCreateRequest,
    UserRSSFeedUpdate,
    UserCategoriesUpdate,
)
from firefeed_core.models.api_key_models import (
    UserApiKeyCreate,
    UserApiKeyUpdate,
)

# Other models still use local definitions (not in firefeed_core)
from .base import Base
from .api_key import APIKey, APIKeyResponse
from .user_category import UserCategory
from .user_rss_feed import UserRSSFeed
from .user_session import UserSession
from .password_reset_token import PasswordResetToken
from .email_verification_token import EmailVerificationToken
from .telegram_user import TelegramUser
from .telegram_chat import TelegramChat
from .telegram_message import TelegramMessage
from .translation import Translation
from .translation_cache import TranslationCache
from .media_file import MediaFile
from .media_cache import MediaCache
from .user import User
from .rss_item import RSSItemCreate, RSSItemUpdate

# Alias for backward compatibility
CategoryCreate = Category
CategoryUpdate = Category
SourceCreate = Source
SourceUpdate = Source
RSSFeedCreate = RSSFeed
RSSFeedUpdate = RSSFeed

# Import public models
from .public_models import (
    # Authentication models
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse as PublicUserResponse,
    TokenResponse,
    LoginRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    EmailVerificationRequest,
    ResendVerificationRequest,
    
    # RSS models
    RSSItemResponse as PublicRSSItemResponse,
    RSSItemFilter,
    RSSItemPagination,
    RSSFeedResponse as PublicRSSFeedResponse,
    RSSFeedCreateRequest,
    RSSFeedUpdateRequest,
    CategoryResponse as PublicCategoryResponse,
    SourceResponse as PublicSourceResponse,
    LanguageResponse,
    
    # Translation models
    TranslationRequest,
    TranslationResponse,
    
    # Media models
    MediaRequest,
    MediaResponse,
    
    # Email models
    EmailRequest,
    EmailResponse,
    
    # Health models
    HealthResponse,
    ServiceInfo,
    
    # Error models
    ErrorResponse,
    ValidationErrorResponse,
    NotFoundErrorResponse,
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    ServiceErrorResponse,
    RateLimitErrorResponse,
    NetworkErrorResponse,
    MaintenanceErrorResponse
)

# Export commonly used models
__all__ = [
    # Base models
    'Base',
    
    # User models
    'User', 'UserCreate', 'UserUpdate', 'UserResponse',
    
    # API key models
    'APIKey', 'APIKeyCreate', 'APIKeyResponse',
    
    # Category models
    'Category', 'CategoryCreate', 'CategoryUpdate', 'CategoryResponse',
    
    # Source models
    'Source', 'SourceCreate', 'SourceUpdate', 'SourceResponse',
    
    # RSS feed models
    'RSSFeed', 'RSSFeedCreate', 'RSSFeedUpdate', 'RSSFeedResponse',
    
    # RSS item models
    'RSSItem', 'RSSItemCreate', 'RSSItemUpdate', 'RSSItemResponse',
    
    # User relationship models
    'UserCategory', 'UserRSSFeed',
    
    # Session models
    'UserSession',
    
    # Token models
    'PasswordResetToken', 'EmailVerificationToken',
    
    # Telegram models
    'TelegramUser', 'TelegramChat', 'TelegramMessage',
    
    # Translation models
    'Translation', 'TranslationCache',
    
    # Media models
    'MediaFile', 'MediaCache',
    
    # Public models
    'UserCreateRequest', 'UserUpdateRequest', 'PublicUserResponse',
    'TokenResponse', 'LoginRequest', 'PasswordResetRequest', 'PasswordResetConfirmRequest',
    'EmailVerificationRequest', 'ResendVerificationRequest',
    'PublicRSSItemResponse', 'RSSItemFilter', 'RSSItemPagination',
    'PublicRSSFeedResponse', 'RSSFeedCreateRequest', 'RSSFeedUpdateRequest',
    'PublicCategoryResponse', 'PublicSourceResponse', 'LanguageResponse',
    'TranslationRequest', 'TranslationResponse',
    'MediaRequest', 'MediaResponse',
    'EmailRequest', 'EmailResponse',
    'HealthResponse', 'ServiceInfo',
    'ErrorResponse', 'ValidationErrorResponse', 'NotFoundErrorResponse',
    'AuthenticationErrorResponse', 'AuthorizationErrorResponse', 'ServiceErrorResponse',
    'RateLimitErrorResponse', 'NetworkErrorResponse', 'MaintenanceErrorResponse'
]