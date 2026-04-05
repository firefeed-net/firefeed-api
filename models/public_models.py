"""Public API models for FireFeed API - maintaining backward compatibility with monolithic version."""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Import models from firefeed-core to ensure compatibility
from firefeed_core.models.base_models import (
    RSSItem as CoreRSSItem,
    UserResponse as CoreUserResponse,
    Category as CoreCategory,
    Source as CoreSource,
    LanguageTranslation as CoreLanguageTranslation
)

# Language enum for validation
class LanguageEnum(str, Enum):
    EN = "en"
    RU = "ru"
    DE = "de"
    FR = "fr"

# Model for representing translation to a specific language (backward compatible)
class LanguageTranslation(BaseModel):
    """Language translation model (backward compatible with monolithic version)."""
    title: Optional[str] = None
    content: Optional[str] = None

# Complete RSS Item Model - matches monolithic version exactly
class RSSItem(CoreRSSItem):
    """RSS Item model (backward compatible with monolithic version)."""
    # All fields are inherited from CoreRSSItem
    # This ensures complete compatibility with the monolithic version
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User Response Model - for API responses (backward compatible)
class UserResponse(CoreUserResponse):
    """User response model (backward compatible with monolithic version)."""
    # All fields are inherited from CoreUserResponse
    # This ensures complete compatibility with the monolithic version
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User Create Model - for creating users (backward compatible)
class UserCreate(BaseModel):
    """User creation model (backward compatible with monolithic version)."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    language: str = "en"

# User Update Model - for updating user information (backward compatible)
class UserUpdate(BaseModel):
    """User update model (backward compatible with monolithic version)."""
    email: Optional[EmailStr] = None
    language: Optional[str] = None

# Category Model - matches monolithic version
class CategoryItem(CoreCategory):
    """Category model (backward compatible with monolithic version)."""
    # All fields are inherited from CoreCategory
    # This ensures complete compatibility with the monolithic version
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Source Model - matches monolithic version
class SourceItem(CoreSource):
    """Source model (backward compatible with monolithic version)."""
    # All fields are inherited from CoreSource
    # This ensures complete compatibility with the monolithic version
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Language Model - matches monolithic version
class LanguageItem(BaseModel):
    """Language model (backward compatible with monolithic version)."""
    language: str

# User RSS Feed Model - matches monolithic version
class UserRSSFeedBase(BaseModel):
    """User RSS feed base model (backward compatible with monolithic version)."""
    url: str
    name: Optional[str] = None
    category_id: Optional[int] = None
    language: str = "en"

class UserRSSFeedCreate(UserRSSFeedBase):
    """User RSS feed creation model (backward compatible with monolithic version)."""
    pass

class UserRSSFeedUpdate(BaseModel):
    """User RSS feed update model (backward compatible with monolithic version)."""
    name: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None

class UserRSSFeedResponse(UserRSSFeedBase):
    """User RSS feed response model (backward compatible with monolithic version)."""
    id: int
    user_id: int
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    category_name: Optional[str] = None

# User API Key Models - matches monolithic version
class UserAPIKeyBase(BaseModel):
    """User API key base model (backward compatible with monolithic version)."""
    limits: Dict[str, Any] = Field(default_factory=lambda: {"requests_per_day": 1000, "requests_per_hour": 100})

class UserAPIKeyCreate(UserAPIKeyBase):
    """User API key creation model (backward compatible with monolithic version)."""
    pass

class UserAPIKeyUpdate(BaseModel):
    """User API key update model (backward compatible with monolithic version)."""
    is_active: Optional[bool] = None
    limits: Optional[Dict[str, Any]] = None

class UserAPIKeyResponse(UserAPIKeyBase):
    """User API key response model (backward compatible with monolithic version)."""
    id: int
    user_id: int
    key_hash: str
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None

# Telegram Link Models - matches monolithic version
class TelegramLinkResponse(BaseModel):
    """Telegram link response model (backward compatible with monolithic version)."""
    link_code: str
    instructions: str

class TelegramLinkStatusResponse(BaseModel):
    """Telegram link status response model (backward compatible with monolithic version)."""
    is_linked: bool
    telegram_id: Optional[int] = None
    linked_at: Optional[str] = None

# Authentication Models - matches monolithic version
class Token(BaseModel):
    """Token response model (backward compatible with monolithic version)."""
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    """Token data model (backward compatible with monolithic version)."""
    user_id: Optional[int] = None

class PasswordResetRequest(BaseModel):
    """Password reset request model (backward compatible with monolithic version)."""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirm model (backward compatible with monolithic version)."""
    token: str
    new_password: str = Field(..., min_length=8)

class EmailVerificationRequest(BaseModel):
    """Email verification request model (backward compatible with monolithic version)."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

class ResendVerificationRequest(BaseModel):
    """Resend verification request model (backward compatible with monolithic version)."""
    email: EmailStr

# Success Response Model - matches monolithic version
class SuccessResponse(BaseModel):
    """Success response model (backward compatible with monolithic version)."""
    message: str

# Error Response Model - matches monolithic version
class HTTPError(BaseModel):
    """Error response model (backward compatible with monolithic version)."""
    detail: str

# User Categories Models - matches monolithic version
class UserCategoriesUpdate(BaseModel):
    """User categories update model (backward compatible with monolithic version)."""
    category_ids: List[int]

class UserCategoriesResponse(BaseModel):
    """User categories response model (backward compatible with monolithic version)."""
    category_ids: List[int]

# Paginated Response Model - matches monolithic version
class PaginatedResponse(BaseModel):
    """Generic paginated response model (backward compatible with monolithic version)."""
    count: int
    results: List[Any]
    
    class Config:
        from_attributes = True

# Translation Request/Response Models - matches monolithic version
class TranslationRequest(BaseModel):
    """Translation request model (backward compatible with monolithic version)."""
    text: str
    target_language: str
    source_language: Optional[str] = None
    model: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class TranslationResponse(BaseModel):
    """Translation response model (backward compatible with monolithic version)."""
    model_config = {"protected_namespaces": ()}

    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None

# Health Check Response Model - matches monolithic version
class HealthCheckResponse(BaseModel):
    """Health check response model (backward compatible with monolithic version)."""
    status: str
    database: str
    redis: Optional[str] = None
    db_pool: Optional[Dict[str, int]] = None
    redis_pool: Optional[Dict[str, int]] = None

# Metrics Response Model - matches monolithic version
class MetricsResponse(BaseModel):
    """Metrics response model (backward compatible with monolithic version)."""
    service_id: str
    timestamp: str  # ISO date-time format
    requests_total: int
    requests_per_minute: float
    error_rate: float
    avg_response_time: float
    active_users: int
    rss_feeds_total: int
    rss_items_total: int
    categories_total: int
    sources_total: int
    translation_requests_total: int
    cache_hit_rate: float
    db_connections_active: int
    redis_connections_active: int

# Service Token Payload Model - matches monolithic version
class ServiceTokenPayload(BaseModel):
    """Service token payload model (backward compatible with monolithic version)."""
    service_id: str
    service_name: str
    scopes: List[str]
    exp: int  # Expiration time
    iat: int  # Issued at
    iss: str  # Issuer

# API Key Create Request Model - matches monolithic version
class APIKeyCreateRequest(BaseModel):
    """API key create request model (backward compatible with monolithic version)."""
    name: str
    user_id: int

# RSS Feed Create Request Model - matches monolithic version
class RSSFeedCreateRequest(BaseModel):
    """RSS feed create request model (backward compatible with monolithic version)."""
    source_id: int
    url: str
    name: str
    category_id: Optional[int] = None
    language: str = "en"
    is_active: bool = True
    cooldown_minutes: int = 10
    max_news_per_hour: int = 10

# User RSS Feed Create Request Model - matches monolithic version
class UserRSSFeedCreateRequest(BaseModel):
    """User RSS feed create request model (backward compatible with monolithic version)."""
    url: str
    name: Optional[str] = None
    category_id: Optional[int] = None
    language: str = "en"

# User Update Request Model - matches monolithic version
class UserUpdateRequest(BaseModel):
    """User update request model (backward compatible with monolithic version)."""
    email: Optional[EmailStr] = None
    language: Optional[str] = None

# Password Reset Request Model - matches monolithic version
class PasswordResetRequestModel(BaseModel):
    """Password reset request model (backward compatible with monolithic version)."""
    email: EmailStr

# Password Reset Confirm Model - matches monolithic version
class PasswordResetConfirmModel(BaseModel):
    """Password reset confirm model (backward compatible with monolithic version)."""
    token: str
    new_password: str = Field(..., min_length=8)

# Email Verification Request Model - matches monolithic version
class EmailVerificationRequestModel(BaseModel):
    """Email verification request model (backward compatible with monolithic version)."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

# Resend Verification Request Model - matches monolithic version
class ResendVerificationRequestModel(BaseModel):
    """Resend verification request model (backward compatible with monolithic version)."""
    email: EmailStr

# Telegram Link Response Model - matches monolithic version
class TelegramLinkResponseModel(BaseModel):
    """Telegram link response model (backward compatible with monolithic version)."""
    link_code: str
    instructions: str

# Telegram Link Status Response Model - matches monolithic version
class TelegramLinkStatusResponseModel(BaseModel):
    """Telegram link status response model (backward compatible with monolithic version)."""
    is_linked: bool
    telegram_id: Optional[int] = None
    linked_at: Optional[str] = None

# User Create Request Model - matches monolithic version
class UserCreateRequest(BaseModel):
    """User creation request model (backward compatible with monolithic version)."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    language: str = "en"

# User Response Model - matches monolithic version
class UserResponse(BaseModel):
    """User response model (backward compatible with monolithic version)."""
    id: int
    email: str
    language: str
    is_active: bool
    is_verified: bool
    created_at: str
    updated_at: Optional[str] = None

# Token Response Model - matches monolithic version
class TokenResponse(BaseModel):
    """Token response model (backward compatible with monolithic version)."""
    access_token: str
    token_type: str
    expires_in: int

# Login Request Model - matches monolithic version
class LoginRequest(BaseModel):
    """Login request model (backward compatible with monolithic version)."""
    email: EmailStr
    password: str

# RSS Item Response Model - matches monolithic version
class RSSItemResponse(BaseModel):
    """RSS item response model (backward compatible with monolithic version)."""
    id: int
    title: str
    content: str
    link: str
    guid: str
    pub_date: str
    feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    language: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    is_published: bool
    published_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# RSS Item Filter Model - matches monolithic version
class RSSItemFilter(BaseModel):
    """RSS item filter model (backward compatible with monolithic version)."""
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    language: Optional[str] = None
    published_after: Optional[str] = None
    published_before: Optional[str] = None
    limit: int = 100
    offset: int = 0

# RSS Item Pagination Model - matches monolithic version
class RSSItemPagination(BaseModel):
    """RSS item pagination model (backward compatible with monolithic version)."""
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0

# RSS Feed Response Model - matches monolithic version
class RSSFeedResponse(BaseModel):
    """RSS feed response model (backward compatible with monolithic version)."""
    id: int
    source_id: int
    url: str
    name: str
    category_id: Optional[int] = None
    language: str
    is_active: bool
    cooldown_minutes: int
    max_news_per_hour: int
    created_at: str
    updated_at: Optional[str] = None
    category_name: Optional[str] = None
    source_name: Optional[str] = None

# Category Response Model - matches monolithic version
class CategoryResponse(BaseModel):
    """Category response model (backward compatible with monolithic version)."""
    id: int
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

# Source Response Model - matches monolithic version
class SourceResponse(BaseModel):
    """Source response model (backward compatible with monolithic version)."""
    id: int
    name: str
    url: str
    description: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

# Language Response Model - matches monolithic version
class LanguageResponse(BaseModel):
    """Language response model (backward compatible with monolithic version)."""
    language: str
    name: str
    is_active: bool

# Media Request Model - matches monolithic version
class MediaRequest(BaseModel):
    """Media request model (backward compatible with monolithic version)."""
    url: str
    content: Optional[str] = None

# Media Response Model - matches monolithic version
class MediaResponse(BaseModel):
    """Media response model (backward compatible with monolithic version)."""
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    extracted_text: Optional[str] = None
    processing_time: Optional[float] = None

# Email Request Model - matches monolithic version
class EmailRequest(BaseModel):
    """Email request model (backward compatible with monolithic version)."""
    to: str
    subject: str
    body: str
    html_body: Optional[str] = None

# Email Response Model - matches monolithic version
class EmailResponse(BaseModel):
    """Email response model (backward compatible with monolithic version)."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None

# Health Response Model - matches monolithic version
class HealthResponse(BaseModel):
    """Health response model (backward compatible with monolithic version)."""
    status: str
    database: str
    redis: Optional[str] = None
    db_pool: Optional[Dict[str, int]] = None
    redis_pool: Optional[Dict[str, int]] = None

# Service Info Model - matches monolithic version
class ServiceInfo(BaseModel):
    """Service info model (backward compatible with monolithic version)."""
    service_id: str
    service_name: str
    version: str
    uptime: float
    timestamp: str

# Error Response Model - matches monolithic version
class ErrorResponse(BaseModel):
    """Error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

# Validation Error Response Model - matches monolithic version
class ValidationErrorResponse(BaseModel):
    """Validation error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    errors: List[Dict[str, Any]]

# Not Found Error Response Model - matches monolithic version
class NotFoundErrorResponse(BaseModel):
    """Not found error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    resource: str

# Authentication Error Response Model - matches monolithic version
class AuthenticationErrorResponse(BaseModel):
    """Authentication error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    details: Optional[str] = None

# Authorization Error Response Model - matches monolithic version
class AuthorizationErrorResponse(BaseModel):
    """Authorization error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    required_permission: Optional[str] = None

# Service Error Response Model - matches monolithic version
class ServiceErrorResponse(BaseModel):
    """Service error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    service: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Rate Limit Error Response Model - matches monolithic version
class RateLimitErrorResponse(BaseModel):
    """Rate limit error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    limit: int
    remaining: int
    reset_time: str

# Network Error Response Model - matches monolithic version
class NetworkErrorResponse(BaseModel):
    """Network error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    url: Optional[str] = None
    status_code: Optional[int] = None

# Maintenance Error Response Model - matches monolithic version
class MaintenanceErrorResponse(BaseModel):
    """Maintenance error response model (backward compatible with monolithic version)."""
    error: str
    message: str
    scheduled_time: Optional[str] = None
    estimated_duration: Optional[str] = None

# Duplicate Detection Request Model - matches monolithic version
class DuplicateDetectionRequest(BaseModel):
    """Duplicate detection request model (backward compatible with monolithic version)."""
    text: str
    threshold: Optional[float] = 0.8
    language: Optional[str] = None

# Duplicate Detection Response Model - matches monolithic version
class DuplicateDetectionResponse(BaseModel):
    """Duplicate detection response model (backward compatible with monolithic version)."""
    is_duplicate: bool
    similarity_score: Optional[float] = None
    existing_news_id: Optional[str] = None
    processing_time: Optional[float] = None

# Media Extraction Request Model - matches monolithic version
class MediaExtractionRequest(BaseModel):
    """Media extraction request model (backward compatible with monolithic version)."""
    url: str
    content: Optional[str] = None

# Media Extraction Response Model - matches monolithic version
class MediaExtractionResponse(BaseModel):
    """Media extraction response model (backward compatible with monolithic version)."""
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    extracted_text: Optional[str] = None
    processing_time: Optional[float] = None

# RSS Item Processing Request Model - matches monolithic version
class RSSItemProcessingRequest(BaseModel):
    """RSS item processing request model (backward compatible with monolithic version)."""
    title: str
    content: str
    link: str
    guid: str
    pub_date: str  # ISO date-time format
    feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    language: str = "en"
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# RSS Item Processing Response Model - matches monolithic version
class RSSItemProcessingResponse(BaseModel):
    """RSS item processing response model (backward compatible with monolithic version)."""
    news_id: str
    title: str
    content: str
    link: str
    guid: str
    pub_date: str  # ISO date-time format
    feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    language: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: str  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    is_published: bool = False
    published_at: Optional[str] = None  # ISO date-time format
    metadata: Optional[Dict[str, Any]] = None

# Service Health Check Request Model - matches monolithic version
class ServiceHealthCheckRequest(BaseModel):
    """Service health check request model (backward compatible with monolithic version)."""
    service_id: str
    check_database: bool = True
    check_redis: bool = True
    check_external_services: bool = False

# Service Health Check Response Model - matches monolithic version
class ServiceHealthCheckResponse(BaseModel):
    """Service health check response model (backward compatible with monolithic version)."""
    service_id: str
    status: str
    timestamp: str  # ISO date-time format
    checks: Dict[str, Dict[str, Any]]
    uptime: Optional[float] = None

# Rate Limit Check Request Model - matches monolithic version
class RateLimitCheckRequest(BaseModel):
    """Rate limit check request model (backward compatible with monolithic version)."""
    service_id: str
    endpoint: str
    client_id: Optional[str] = None

# Rate Limit Check Response Model - matches monolithic version
class RateLimitCheckResponse(BaseModel):
    """Rate limit check response model (backward compatible with monolithic version)."""
    allowed: bool
    limit: int
    remaining: int
    reset_time: str  # ISO date-time format
    retry_after: Optional[int] = None

# Cache Operation Request Model - matches monolithic version
class CacheOperationRequest(BaseModel):
    """Cache operation request model (backward compatible with monolithic version)."""
    key: str
    value: Optional[Any] = None
    ttl: Optional[int] = None  # Time to live in seconds

# Cache Operation Response Model - matches monolithic version
class CacheOperationResponse(BaseModel):
    """Cache operation response model (backward compatible with monolithic version)."""
    success: bool
    key: str
    value: Optional[Any] = None
    ttl: Optional[int] = None

# Database Operation Request Model - matches monolithic version
class DatabaseOperationRequest(BaseModel):
    """Database operation request model (backward compatible with monolithic version)."""
    query: str
    parameters: Optional[Dict[str, Any]] = None
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE

# Database Operation Response Model - matches monolithic version
class DatabaseOperationResponse(BaseModel):
    """Database operation response model (backward compatible with monolithic version)."""
    success: bool
    rows_affected: int
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

# Notification Request Model - matches monolithic version
class NotificationRequest(BaseModel):
    """Notification request model (backward compatible with monolithic version)."""
    recipient_type: str  # "channel" or "user"
    recipient_id: int
    message: str
    language: Optional[str] = None
    media_url: Optional[str] = None

# Notification Response Model - matches monolithic version
class NotificationResponse(BaseModel):
    """Notification response model (backward compatible with monolithic version)."""
    success: bool
    recipient_type: str
    recipient_id: int
    message_id: Optional[int] = None
    sent_at: Optional[str] = None  # ISO date-time format
    error: Optional[str] = None

# Subscription Request Model - matches monolithic version
class SubscriptionRequest(BaseModel):
    """Subscription request model (backward compatible with monolithic version)."""
    user_id: int
    category_ids: List[int]
    source_ids: Optional[List[int]] = None
    languages: Optional[List[str]] = None

# Subscription Response Model - matches monolithic version
class SubscriptionResponse(BaseModel):
    """Subscription response model (backward compatible with monolithic version)."""
    user_id: int
    category_ids: List[int]
    source_ids: Optional[List[int]] = None
    languages: Optional[List[str]] = None
    updated_at: Optional[str] = None  # ISO date-time format

# User State Model - matches monolithic version
class UserState(BaseModel):
    """User state model for telegram bot (backward compatible with monolithic version)."""
    current_subs: List[int] = []
    language: str = "en"
    last_access: float

# User Menu Model - matches monolithic version
class UserMenu(BaseModel):
    """User menu state model for telegram bot (backward compatible with monolithic version)."""
    menu: str
    last_access: float

# User Language Model - matches monolithic version
class UserLanguage(BaseModel):
    """User language state model for telegram bot (backward compatible with monolithic version)."""
    language: str
    last_access: float

# Telegram Bot State Model - matches monolithic version
class TelegramBotState(BaseModel):
    """Telegram bot state model (backward compatible with monolithic version)."""
    user_states: Dict[int, UserState] = {}
    user_menus: Dict[int, UserMenu] = {}
    user_languages: Dict[int, UserLanguage] = {}
    last_cleanup: float = 0.0

# RSS Parser State Model - matches monolithic version
class RSSParserState(BaseModel):
    """RSS parser state model (backward compatible with monolithic version)."""
    last_processed_feeds: Dict[str, float] = {}
    processing_errors: Dict[str, int] = {}
    last_cleanup: float = 0.0

# API Service State Model - matches monolithic version
class APIServiceState(BaseModel):
    """API service state model (backward compatible with monolithic version)."""
    active_connections: int = 0
    request_count: int = 0
    error_count: int = 0
    last_cleanup: float = 0.0

# Service Configuration Model - matches monolithic version
class ServiceConfiguration(BaseModel):
    """Service configuration model (backward compatible with monolithic version)."""
    service_id: str
    service_name: str
    service_version: str
    database_url: str
    redis_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    log_level: str = "INFO"
    cors_allowed_origins: List[str] = []
    allowed_hosts: List[str] = []
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    translation_enabled: bool = True
    duplicate_detection_enabled: bool = True
    cache_enabled: bool = True

# Database Configuration Model - matches monolithic version
class DatabaseConfiguration(BaseModel):
    """Database configuration model (backward compatible with monolithic version)."""
    host: str
    port: int = 5432
    name: str
    user: str
    password: str
    minsize: int = 1
    maxsize: int = 20
    timeout: int = 30

# Redis Configuration Model - matches monolithic version
class RedisConfiguration(BaseModel):
    """Redis configuration model (backward compatible with monolithic version)."""
    host: str
    port: int = 6379
    db: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30

# Translation Configuration Model - matches monolithic version
class TranslationConfiguration(BaseModel):
    """Translation configuration model (backward compatible with monolithic version)."""
    enabled: bool = True
    default_model: str = "facebook/m2m100_418M"
    supported_languages: List[str] = ["en", "ru", "de", "fr"]
    max_text_length: int = 10000
    timeout: int = 30

# Duplicate Detection Configuration Model - matches monolithic version
class DuplicateDetectionConfiguration(BaseModel):
    """Duplicate detection configuration model (backward compatible with monolithic version)."""
    enabled: bool = True
    threshold: float = 0.8
    max_age_hours: int = 24
    timeout: int = 10

# Cache Configuration Model - matches monolithic version
class CacheConfiguration(BaseModel):
    """Cache configuration model (backward compatible with monolithic version)."""
    enabled: bool = True
    default_ttl: int = 3600
    max_size: int = 1000
    timeout: int = 5

# Rate Limiting Configuration Model - matches monolithic version
class RateLimitingConfiguration(BaseModel):
    """Rate limiting configuration model (backward compatible with monolithic version)."""
    enabled: bool = True
    default_requests: int = 100
    default_window: int = 60
    burst_size: int = 10

# Monitoring Configuration Model - matches monolithic version
class MonitoringConfiguration(BaseModel):
    """Monitoring configuration model (backward compatible with monolithic version)."""
    enabled: bool = True
    metrics_enabled: bool = True
    health_check_enabled: bool = True
    log_level: str = "INFO"
    log_file: Optional[str] = None

# Security Configuration Model - matches monolithic version
class SecurityConfiguration(BaseModel):
    """Security configuration model (backward compatible with monolithic version)."""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_minutes: int = 30

# Application Configuration Model - matches monolithic version
class ApplicationConfiguration(BaseModel):
    """Application configuration model (backward compatible with monolithic version)."""
    service: ServiceConfiguration
    database: DatabaseConfiguration
    redis: RedisConfiguration
    translation: TranslationConfiguration
    duplicate_detection: DuplicateDetectionConfiguration
    cache: CacheConfiguration
    rate_limiting: RateLimitingConfiguration
    monitoring: MonitoringConfiguration
    security: SecurityConfiguration

# RSS Feed Create Request Model - matches monolithic version
class RSSFeedCreateRequest(BaseModel):
    """RSS feed create request model (backward compatible with monolithic version)."""
    source_id: int
    url: str
    name: str
    category_id: Optional[int] = None
    language: str = "en"
    is_active: bool = True
    cooldown_minutes: int = 10
    max_news_per_hour: int = 10

# RSS Feed Update Request Model - matches monolithic version
class RSSFeedUpdateRequest(BaseModel):
    """RSS feed update request model (backward compatible with monolithic version)."""
    name: Optional[str] = None
    category_id: Optional[int] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None
    cooldown_minutes: Optional[int] = None
    max_news_per_hour: Optional[int] = None

# Category Response Model - matches monolithic version
class CategoryResponse(BaseModel):
    """Category response model (backward compatible with monolithic version)."""
    id: int
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

# Source Response Model - matches monolithic version
class SourceResponse(BaseModel):
    """Source response model (backward compatible with monolithic version)."""
    id: int
    name: str
    url: str
    description: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

# Language Response Model - matches monolithic version
class LanguageResponse(BaseModel):
    """Language response model (backward compatible with monolithic version)."""
    language: str
    name: str
    is_active: bool

# API Key Create Model - matches monolithic version
class APIKeyCreate(BaseModel):
    """API key create model (backward compatible with monolithic version)."""
    name: str
    user_id: int

# API Key Response Model - matches monolithic version
class APIKeyResponse(BaseModel):
    """API key response model (backward compatible with monolithic version)."""
    id: int
    user_id: int
    key_hash: str
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None