"""
Models package for FireFeed API

This package contains all the data models for the application.
"""

# Import models
from .base import Base
from .user import User, UserCreate, UserUpdate, UserResponse
from .api_key import APIKey, APIKeyCreate, APIKeyResponse
from .category import Category, CategoryCreate, CategoryUpdate, CategoryResponse
from .source import Source, SourceCreate, SourceUpdate, SourceResponse
from .rss_feed import RSSFeed, RSSFeedCreate, RSSFeedUpdate, RSSFeedResponse
from .rss_item import RSSItem, RSSItemCreate, RSSItemUpdate, RSSItemResponse
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