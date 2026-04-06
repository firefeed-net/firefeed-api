"""
Environment configuration for FireFeed API

This module provides environment configuration management
for the application.
"""

import os
import warnings
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class Settings(BaseSettings):
    """Application settings"""

    # In Docker, environment variables are injected by docker-compose.
    # For local development, you can create a .env file in the project root.
    # pydantic-settings v2 reads env vars directly, not from env_file by default.
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="FIREFEED_",
    )

    # Project settings
    project_name: str = Field(default="FireFeed API")
    project_version: str = Field(default="1.0.0")
    project_description: str = Field(default="Microservices-based RSS feed management API")

    # Database settings
    database_url: str = Field(default="")
    redis_url: str = Field(default="redis://localhost:6379/0")

    # API settings (align with docker-compose)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_debug: bool = Field(default=True)
    api_environment: str = Field(default="development")
    api_log_level: str = Field(default="debug")
    api_access_log: bool = Field(default=True)

    # Authentication settings
    jwt_secret_key: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # Service settings
    internal_api_url: str = Field(default="http://localhost:8001")
    internal_api_token: str = Field(default="internal-service-token")

    # External services
    telegram_bot_token: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    yandex_api_key: Optional[str] = Field(default=None)

    # Logging settings
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Cache settings
    cache_ttl: int = Field(default=3600)
    cache_max_size: int = Field(default=1000)

    # Performance settings
    max_requests_per_minute: int = Field(default=60)
    max_concurrent_requests: int = Field(default=100)

    # Security settings
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:8080")
    cors_allow_credentials: bool = Field(default=True)
    secure_cookies: bool = Field(default=False)

    # Monitoring settings
    enable_metrics: bool = Field(default=True)
    enable_health_check: bool = Field(default=True)
    enable_tracing: bool = Field(default=False)

    # Development settings
    dev_mode: bool = Field(default=True)
    hot_reload: bool = Field(default=True)
    auto_migrate: bool = Field(default=True)

    @model_validator(mode='after')
    def validate_all(self) -> 'Settings':
        """Combined validator for jwt_secret_key and database_url."""
        # Validate jwt_secret_key
        if not self.jwt_secret_key:
            raise ValueError(
                "FIREFEED_JWT_SECRET_KEY environment variable is required. "
                "Please set it to a secure random string, e.g.: "
                "export FIREFEED_JWT_SECRET_KEY=$(openssl rand -hex 32)"
            )
        if len(self.jwt_secret_key) < 32:
            raise ValueError(
                "FIREFEED_JWT_SECRET_KEY must be at least 32 characters (64 hex chars). "
                "Please generate a new key: export FIREFEED_JWT_SECRET_KEY=$(openssl rand -hex 32)"
            )
        # Check for common weak patterns
        if self.jwt_secret_key == 'a' * len(self.jwt_secret_key) or \
           self.jwt_secret_key == '0' * len(self.jwt_secret_key) or \
           self.jwt_secret_key.lower() in ('secretkey', 'mysecretkey', 'supersecret', 'changeme'):
            raise ValueError(
                "FIREFEED_JWT_SECRET_KEY appears to be a weak pattern. "
                "Please generate a secure random key: export FIREFEED_JWT_SECRET_KEY=$(openssl rand -hex 32)"
            )

        # Validate database_url
        if not self.database_url and self.api_environment == "production":
            raise ValueError(
                "DATABASE_URL environment variable is required in production. "
                "Please configure a secure database connection string."
            )
        # Warn if using default credentials in non-production
        if self.database_url and "postgres:password" in self.database_url:
            warnings.warn(
                "Default database credentials detected. "
                "Please update DATABASE_URL to use secure credentials."
            )
        return self


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