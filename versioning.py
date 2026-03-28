"""
API versioning utilities for FireFeed API

This module provides utilities for API versioning and backward compatibility.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class APIVersion(BaseModel):
    """API version information"""
    version: str
    status: str  # active, deprecated, removed
    deprecated_at: Optional[str] = None
    removed_at: Optional[str] = None
    migration_guide: Optional[str] = None


class VersionManager:
    """Manages API versions and backward compatibility"""
    
    def __init__(self):
        self.versions: Dict[str, APIVersion] = {
            "v1": APIVersion(
                version="v1",
                status="active",
                migration_guide="https://docs.firefeed.net/migration/v1"
            ),
            "v2": APIVersion(
                version="v2",
                status="active",
                migration_guide="https://docs.firefeed.net/migration/v2"
            )
        }
    
    def get_version_info(self, version: str) -> Optional[APIVersion]:
        """Get version information"""
        return self.versions.get(version)
    
    def is_version_active(self, version: str) -> bool:
        """Check if version is active"""
        version_info = self.get_version_info(version)
        return version_info is not None and version_info.status == "active"
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if version is deprecated"""
        version_info = self.get_version_info(version)
        return version_info is not None and version_info.status == "deprecated"
    
    def get_active_versions(self) -> list[str]:
        """Get list of active versions"""
        return [v for v, info in self.versions.items() if info.status == "active"]
    
    def get_deprecated_versions(self) -> list[str]:
        """Get list of deprecated versions"""
        return [v for v, info in self.versions.items() if info.status == "deprecated"]


# Global version manager instance
version_manager = VersionManager()


def check_api_version(version: str) -> None:
    """
    Check if API version is valid and active
    
    Args:
        version: API version to check
        
    Raises:
        HTTPException: If version is not found or deprecated
    """
    if not version_manager.is_version_active(version):
        if version_manager.is_version_deprecated(version):
            raise HTTPException(
                status_code=status.HTTP_426_UPGRADE_REQUIRED,
                detail={
                    "error": "API version deprecated",
                    "message": f"API version {version} is deprecated",
                    "migration_guide": version_manager.get_version_info(version).migration_guide
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "API version not found",
                    "message": f"API version {version} not found",
                    "available_versions": version_manager.get_active_versions()
                }
            )


def create_versioned_response(
    data: Any,
    version: str,
    meta: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a versioned API response
    
    Args:
        data: Response data
        version: API version
        meta: Additional metadata
        
    Returns:
        JSONResponse: Versioned response
    """
    response_data = {
        "version": version,
        "data": data
    }
    
    if meta:
        response_data["meta"] = meta
    
    return JSONResponse(content=response_data)


def create_backward_compatible_response(
    data: Any,
    version: str,
    legacy_format: bool = False
) -> JSONResponse:
    """
    Create a backward compatible API response
    
    Args:
        data: Response data
        version: API version
        legacy_format: Whether to use legacy format
        
    Returns:
        JSONResponse: Backward compatible response
    """
    if legacy_format:
        # Return legacy format for backward compatibility
        return JSONResponse(content=data)
    else:
        # Return new format
        return create_versioned_response(data, version)


class VersionedEndpoint:
    """Decorator for versioned endpoints"""
    
    def __init__(self, version: str, deprecated: bool = False):
        self.version = version
        self.deprecated = deprecated
    
    def __call__(self, func):
        """Decorator function"""
        async def wrapper(*args, **kwargs):
            # Check version compatibility
            check_api_version(self.version)
            
            # Call original function
            result = await func(*args, **kwargs)
            
            # Create versioned response
            return create_versioned_response(result, self.version)
        
        # Copy function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        
        return wrapper


def setup_versioning(app: FastAPI) -> None:
    """Attach version manager and defaults to the FastAPI app state."""
    app.state.version_manager = version_manager
    app.state.current_api_version = CURRENT_API_VERSION
    app.state.legacy_api_version = LEGACY_API_VERSION


# Version constants
API_VERSION_V1 = "v1"
API_VERSION_V2 = "v2"
CURRENT_API_VERSION = API_VERSION_V2
LEGACY_API_VERSION = API_VERSION_V1