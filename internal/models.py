"""
Models for FireFeed Internal API

This module provides Pydantic models for the internal API endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp")


class ServiceInfo(BaseModel):
    """Service information response model"""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    description: str = Field(..., description="Service description")
    status: str = Field(..., description="Service status")


class ServiceTokenResponse(BaseModel):
    """Service token response model"""
    token: str = Field(..., description="JWT service token")
    service_name: str = Field(..., description="Service name")
    expires_at: str = Field(..., description="Token expiration time")
    created_at: str = Field(..., description="Token creation time")


class ServiceAuthResponse(BaseModel):
    """Service authentication response model"""
    service_name: str = Field(..., description="Service name")
    token_valid: bool = Field(..., description="Token validity status")
    expires_at: Optional[str] = Field(None, description="Token expiration time")
    issued_at: Optional[str] = Field(None, description="Token issue time")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class UserResponse(BaseModel):
    """User response model"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    language: str = Field(..., description="User language")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="User verification status")
    created_at: datetime = Field(..., description="User creation time")
    updated_at: datetime = Field(..., description="User last update time")


class RSSItemResponse(BaseModel):
    """RSS item response model"""
    news_id: str = Field(..., description="RSS item ID")
    original_title: str = Field(..., description="Original title")
    original_content: Optional[str] = Field(None, description="Original content")
    original_language: str = Field(..., description="Original language")
    category_id: int = Field(..., description="Category ID")
    image_filename: Optional[str] = Field(None, description="Image filename")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Update time")
    rss_feed_id: int = Field(..., description="RSS feed ID")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    source_url: Optional[str] = Field(None, description="Source URL")
    video_filename: Optional[str] = Field(None, description="Video filename")


class CategoryResponse(BaseModel):
    """Category response model"""
    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Update time")


class SourceResponse(BaseModel):
    """Source response model"""
    id: int = Field(..., description="Source ID")
    name: str = Field(..., description="Source name")
    url: str = Field(..., description="Source URL")
    is_active: bool = Field(..., description="Source active status")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Update time")


class RSSFeedResponse(BaseModel):
    """RSS feed response model"""
    id: int = Field(..., description="RSS feed ID")
    source_id: int = Field(..., description="Source ID")
    category_id: int = Field(..., description="Category ID")
    title: str = Field(..., description="RSS feed title")
    description: Optional[str] = Field(None, description="RSS feed description")
    url: str = Field(..., description="RSS feed URL")
    is_active: bool = Field(..., description="RSS feed active status")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Update time")


class TranslationRequest(BaseModel):
    """Translation request model"""
    text: str = Field(..., description="Text to translate")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    provider: Optional[str] = Field(None, description="Translation provider")


class TranslationResponse(BaseModel):
    """Translation response model"""
    model_config = {"protected_namespaces": ()}

    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Source language")
    target_language: str = Field(..., description="Target language")
    provider: str = Field(..., description="Translation provider")
    created_at: datetime = Field(..., description="Translation creation time")


class MediaRequest(BaseModel):
    """Media request model"""
    url: str = Field(..., description="Media URL")
    media_type: str = Field(..., description="Media type (image/video)")
    file_path: Optional[str] = Field(None, description="Local file path")


class MediaResponse(BaseModel):
    """Media response model"""
    media_id: str = Field(..., description="Media ID")
    original_url: str = Field(..., description="Original URL")
    file_path: str = Field(..., description="Processed file path")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    media_type: str = Field(..., description="Media type")
    created_at: datetime = Field(..., description="Creation time")


class EmailRequest(BaseModel):
    """Email request model"""
    to: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    html_body: Optional[str] = Field(None, description="HTML email body")


class EmailResponse(BaseModel):
    """Email response model"""
    message_id: str = Field(..., description="Email message ID")
    to: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    status: str = Field(..., description="Email status")
    sent_at: datetime = Field(..., description="Email sent time")


class TaskStatusResponse(BaseModel):
    """Task status response model"""
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: Optional[int] = Field(None, description="Task progress (0-100)")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Task error message")
    created_at: datetime = Field(..., description="Task creation time")
    updated_at: datetime = Field(..., description="Task update time")


class MetricsResponse(BaseModel):
    """Metrics response model"""
    requests_total: int = Field(..., description="Total requests")
    requests_by_method: Dict[str, int] = Field(..., description="Requests by HTTP method")
    requests_by_path: Dict[str, int] = Field(..., description="Requests by path")
    errors_total: int = Field(..., description="Total errors")
    errors_by_type: Dict[str, int] = Field(..., description="Errors by type")
    processing_time_total: float = Field(..., description="Total processing time")
    processing_time_avg: float = Field(..., description="Average processing time")


class CacheStatsResponse(BaseModel):
    """Cache statistics response model"""
    status: str = Field(..., description="Cache status")
    memory_usage: str = Field(..., description="Memory usage")
    keyspace_hits: int = Field(..., description="Keyspace hits")
    keyspace_misses: int = Field(..., description="Keyspace misses")
    connected_clients: int = Field(..., description="Connected clients")
    total_commands_processed: int = Field(..., description="Total commands processed")
    timestamp: str = Field(..., description="Statistics timestamp")


class DatabaseHealthResponse(BaseModel):
    """Database health response model"""
    status: str = Field(..., description="Database status")
    version: str = Field(..., description="Database version")
    connection_pool_size: int = Field(..., description="Connection pool size")
    active_connections: int = Field(..., description="Active connections")
    idle_connections: int = Field(..., description="Idle connections")
    timestamp: str = Field(..., description="Health check timestamp")


class SystemHealthResponse(BaseModel):
    """System health response model"""
    status: str = Field(..., description="System status")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    memory_usage: float = Field(..., description="Memory usage percentage")
    disk_usage: float = Field(..., description="Disk usage percentage")
    uptime: str = Field(..., description="System uptime")
    timestamp: str = Field(..., description="Health check timestamp")


class ServiceStatusResponse(BaseModel):
    """Service status response model"""
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime: str = Field(..., description="Service uptime")
    dependencies: List[str] = Field(..., description="Service dependencies")
    timestamp: str = Field(..., description="Status check timestamp")