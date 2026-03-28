"""
Media file models for FireFeed API
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field
import uuid

from .base import Base


class MediaFile(Base):
    """Media file model"""
    __tablename__ = "media_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False)
    
    # Media type
    media_type = Column(String(50), nullable=False)  # image, video, audio, document
    
    # Optional metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds for audio/video
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # Relationships
    rss_item_id = Column(UUID(as_uuid=True), ForeignKey("rss_items.id"), nullable=True)
    rss_item = relationship("RSSItem", back_populates="media_files")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MediaFileCreate(BaseModel):
    """Schema for creating a media file"""
    original_filename: str = Field(..., description="Original filename")
    stored_filename: str = Field(..., description="Stored filename")
    file_path: str = Field(..., description="File path")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="Content type")
    file_hash: str = Field(..., description="File hash")
    media_type: str = Field(..., description="Media type")
    width: Optional[int] = Field(None, description="Image width")
    height: Optional[int] = Field(None, description="Image height")
    duration: Optional[int] = Field(None, description="Duration in seconds")


class MediaFileResponse(BaseModel):
    """Schema for media file response"""
    id: uuid.UUID
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    content_type: str
    file_hash: str
    media_type: str
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    is_processed: bool
    processing_error: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True