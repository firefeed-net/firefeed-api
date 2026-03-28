# database_config.py - Database configuration for firefeed-api
import os
from typing import Optional
from pydantic import BaseModel, Field


class DatabaseConfiguration(BaseModel):
    """Database configuration model."""

    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    name: str = Field("firefeed", description="Database name")
    user: str = Field("your_db_user", description="Database user")
    password: str = Field("your_db_password", description="Database password")
    minsize: int = Field(1, description="Minimum connection pool size")
    maxsize: int = Field(20, description="Maximum connection pool size")
    timeout: int = Field(30, description="Connection timeout in seconds")

    @classmethod
    def from_env(cls) -> 'DatabaseConfiguration':
        """Load config from environment. Supports both DB_* and DATABASE_* prefixes."""
        host = os.getenv('DB_HOST') or os.getenv('DATABASE_HOST', 'localhost')
        port = int(os.getenv('DB_PORT') or os.getenv('DATABASE_PORT', '5432'))
        name = os.getenv('DB_NAME') or os.getenv('DATABASE_NAME', 'firefeed')
        user = os.getenv('DB_USER') or os.getenv('DATABASE_USER', 'your_db_user')
        password = os.getenv('DB_PASSWORD') or os.getenv('DATABASE_PASSWORD', 'your_db_password')
        minsize = int(os.getenv('DB_MINSIZE', os.getenv('DATABASE_MINSIZE', '1')))
        maxsize = int(os.getenv('DB_MAXSIZE', os.getenv('DATABASE_MAXSIZE', '20')))
        timeout = int(os.getenv('DB_TIMEOUT', os.getenv('DATABASE_TIMEOUT', '30')))
        return cls(
            host=host,
            port=port,
            name=name,
            user=user,
            password=password,
            minsize=minsize,
            maxsize=maxsize,
            timeout=timeout,
        )


# Backward compatibility alias
DatabaseConfig = DatabaseConfiguration