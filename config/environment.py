"""
Environment configuration for FireFeed API

This module provides environment configuration management
for the application.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class Settings(BaseSettings):
    @model_validator(mode='after')
    def validate_secret_key(self) -> 'Settings':
        """Validate that secret_key is set and is sufficiently strong."""
        if not self.secret_key:
            raise ValueError(
                "FIREFEED_JWT_SECRET_KEY environment variable is required. "
                "Please set it to a secure random string, e.g.: "
                "export FIREFEED_JWT_SECRET_KEY=$(openssl rand -hex 32)"
            )
        if len(self.secret_key) < 32:
            raise ValueError(
                "FIREFEED_JWT_SECRET_KEY must be at least 32 characters (64 hex chars). "
                "Please generate a new key: export FIREFEED_JWT_SECRET_KEY=$(openssl rand -hex 32)"
            )
        return self
    """Application settings"""

    # Allow unknown env vars to be present without breaking validation
    model_config = SettingsConfigDict(
        env_file="./firefeed-api/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Project settings
    project_name: str = Field(default="FireFeed API", env="PROJECT_NAME")
    project_version: str = Field(default="1.0.0", env="PROJECT_VERSION")
    project_description: str = Field(default="Microservices-based RSS feed management API", env="PROJECT_DESCRIPTION")

    # Database settings
    database_url: str = Field(default="postgresql://postgres:password@localhost:5432/firefeed", env="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # API settings (align with docker-compose)
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_debug: bool = Field(default=True, env="API_DEBUG")
    api_environment: str = Field(default="development", env="API_ENVIRONMENT")
    api_log_level: str = Field(default="debug", env="API_LOG_LEVEL")
    api_access_log: bool = Field(default=True, env="API_ACCESS_LOG")

    # Authentication settings
    secret_key: str = Field(default="", env="FIREFEED_JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # Service settings
    internal_api_url: str = Field(default="http://localhost:8001", env="INTERNAL_API_URL")
    internal_api_token: str = Field(default="internal-service-token", env="INTERNAL_API_TOKEN")

    # External services
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    yandex_api_key: Optional[str] = Field(default=None, env="YANDEX_API_KEY")

    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT")

    # Cache settings
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")

    # Performance settings
    max_requests_per_minute: int = Field(default=60, env="MAX_REQUESTS_PER_MINUTE")
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")

    # Security settings
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:8080", env="ALLOWED_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    secure_cookies: bool = Field(default=False, env="SECURE_COOKIES")

    # Monitoring settings
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_health_check: bool = Field(default=True, env="ENABLE_HEALTH_CHECK")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")

    # Development settings
    dev_mode: bool = Field(default=True, env="DEV_MODE")
    hot_reload: bool = Field(default=True, env="HOT_RELOAD")
    auto_migrate: bool = Field(default=True, env="AUTO_MIGRATE")


def get_settings() -> Settings:
    """
    Get application settings

    Returns:
        Settings: Application settings instance
    """
    return Settings()


def get_environment() -> str:
    """Convenience accessor for current environment name"""
    return get_settings().api_environment


# Global settings instance
settings = get_settings()