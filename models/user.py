from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Use unified model from firefeed_core - no local definition needed
# This file kept for backward compatibility imports only
# All models now imported from firefeed_core.models.base_models
from firefeed_core.models.base_models import (
    User as _CoreUser,
    UserResponse as _CoreUserResponse,
    UserUpdate as _CoreUserUpdate,
    UserCreate as _CoreUserCreate,
)

# Aliases for backward compatibility
User = _CoreUser
UserCreate = _CoreUserCreate
UserUpdate = _CoreUserUpdate  
UserResponse = _CoreUserResponse


__all__ = ['User', 'UserCreate', 'UserUpdate', 'UserResponse']