"""
Media cache models for FireFeed API
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field
import uuid

from .base import Base


class MediaCache(Base):
    """Media cache model"""
    __tablename__ = "media_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    original_url = Column(String(500), nullable=False)
    cached_url = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False)
    
    # Cache metadata
    cache_key = Column(String(255), nullable=False, unique=True)
    cache_ttl = Column(Integer, nullable=False)  # TTL in seconds
    
    # Processing status
    is_cached = Column(Boolean, default=False)
    cache_error = Column(Text, nullable=True)
    
    # Relationships
    rss_item_id = Column(UUID(as_uuid=True), ForeignKey("rss_items.id"), nullable=True)
    rss_item = relationship("RSSItem", back_populates="media_cache")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class MediaCacheCreate(BaseModel):
    """Schema for creating a media cache entry"""
    original_url: str = Field(..., description="Original URL")
    cached_url: str = Field(..., description="Cached URL")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="Content type")
    file_hash: str = Field(..., description="File hash")
    cache_key: str = Field(..., description="Cache key")
    cache_ttl: int = Field(..., description="Cache TTL in seconds")
    expires_at: datetime = Field(..., description="Cache expiration time")


class MediaCacheResponse(BaseModel):
    """Schema for media cache response"""
    id: uuid.UUID
    original_url: str
    cached_url: str
    file_path: str
    file_size: int
    content_type: str
    file_hash: str
    cache_key: str
    cache_ttl: int
    is_cached: bool
    cache_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True