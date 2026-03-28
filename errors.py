"""
Custom error classes for FireFeed API

This module defines custom exception classes for the application.
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class FireFeedError(Exception):
    """Base exception for FireFeed API"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(FireFeedError):
    """Validation error"""
    pass


class NotFoundError(FireFeedError):
    """Resource not found error"""
    pass


class ConflictError(FireFeedError):
    """Resource conflict error"""
    pass


class AuthenticationError(FireFeedError):
    """Authentication error"""
    pass


class AuthorizationError(FireFeedError):
    """Authorization error"""
    pass


class ServiceError(FireFeedError):
    """Service error"""
    pass


class DatabaseError(FireFeedError):
    """Database error"""
    pass


class CacheError(FireFeedError):
    """Cache error"""
    pass


class TranslationError(FireFeedError):
    """Translation service error"""
    pass


class MediaProcessingError(FireFeedError):
    """Media processing error"""
    pass


class EmailError(FireFeedError):
    """Email service error"""
    pass


class MaintenanceError(FireFeedError):
    """Maintenance error"""
    pass


class RateLimitError(FireFeedError):
    """Rate limit exceeded error"""
    pass


class NetworkError(FireFeedError):
    """Network error"""
    pass


class ConfigurationError(FireFeedError):
    """Configuration error"""
    pass


def create_http_exception(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    Create HTTP exception with standardized format
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Optional error code
        details: Optional additional details
        
    Returns:
        HTTPException: Standardized HTTP exception
    """
    error_response = {
        "error": message,
        "status_code": status_code
    }
    
    if error_code:
        error_response["error_code"] = error_code
    
    if details:
        error_response["details"] = details
    
    return HTTPException(
        status_code=status_code,
        detail=error_response
    )


def create_validation_error(
    message: str,
    field: Optional[str] = None,
    value: Optional[Any] = None
) -> HTTPException:
    """
    Create validation error with standardized format
    
    Args:
        message: Error message
        field: Optional field name
        value: Optional field value
        
    Returns:
        HTTPException: Validation error
    """
    details = {}
    if field:
        details["field"] = field
    if value is not None:
        details["value"] = value
    
    return create_http_exception(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=message,
        error_code="VALIDATION_ERROR",
        details=details
    )


def create_not_found_error(
    resource_type: str,
    resource_id: Optional[str] = None
) -> HTTPException:
    """
    Create not found error with standardized format
    
    Args:
        resource_type: Type of resource
        resource_id: Optional resource ID
        
    Returns:
        HTTPException: Not found error
    """
    message = f"{resource_type} not found"
    if resource_id:
        message = f"{resource_type} with ID {resource_id} not found"
    
    return create_http_exception(
        status_code=status.HTTP_404_NOT_FOUND,
        message=message,
        error_code="NOT_FOUND"
    )


def create_conflict_error(
    message: str,
    resource_type: Optional[str] = None
) -> HTTPException:
    """
    Create conflict error with standardized format
    
    Args:
        message: Error message
        resource_type: Optional resource type
        
    Returns:
        HTTPException: Conflict error
    """
    error_code = "CONFLICT"
    if resource_type:
        error_code = f"CONFLICT_{resource_type.upper()}"
    
    return create_http_exception(
        status_code=status.HTTP_409_CONFLICT,
        message=message,
        error_code=error_code
    )


def create_authentication_error(
    message: str = "Authentication required"
) -> HTTPException:
    """
    Create authentication error with standardized format
    
    Args:
        message: Error message
        
    Returns:
        HTTPException: Authentication error
    """
    return create_http_exception(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message=message,
        error_code="AUTHENTICATION_ERROR",
        details={"www_authenticate": "Bearer"}
    )


def create_authorization_error(
    message: str = "Insufficient permissions"
) -> HTTPException:
    """
    Create authorization error with standardized format
    
    Args:
        message: Error message
        
    Returns:
        HTTPException: Authorization error
    """
    return create_http_exception(
        status_code=status.HTTP_403_FORBIDDEN,
        message=message,
        error_code="AUTHORIZATION_ERROR"
    )


def create_service_error(
    message: str,
    service_name: Optional[str] = None
) -> HTTPException:
    """
    Create service error with standardized format
    
    Args:
        message: Error message
        service_name: Optional service name
        
    Returns:
        HTTPException: Service error
    """
    error_code = "SERVICE_ERROR"
    if service_name:
        error_code = f"SERVICE_ERROR_{service_name.upper()}"
    
    return create_http_exception(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message=message,
        error_code=error_code
    )


def create_rate_limit_error(
    message: str = "Rate limit exceeded"
) -> HTTPException:
    """
    Create rate limit error with standardized format
    
    Args:
        message: Error message
        
    Returns:
        HTTPException: Rate limit error
    """
    return create_http_exception(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        message=message,
        error_code="RATE_LIMIT_EXCEEDED"
    )


def create_network_error(
    message: str,
    service_name: Optional[str] = None
) -> HTTPException:
    """
    Create network error with standardized format
    
    Args:
        message: Error message
        service_name: Optional service name
        
    Returns:
        HTTPException: Network error
    """
    error_code = "NETWORK_ERROR"
    if service_name:
        error_code = f"NETWORK_ERROR_{service_name.upper()}"
    
    return create_http_exception(
        status_code=status.HTTP_502_BAD_GATEWAY,
        message=message,
        error_code=error_code
    )


def create_maintenance_error(
    message: str = "Service is under maintenance"
) -> HTTPException:
    """
    Create maintenance error with standardized format
    
    Args:
        message: Error message
        
    Returns:
        HTTPException: Maintenance error
    """
    return create_http_exception(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message=message,
        error_code="MAINTENANCE_MODE"
    )