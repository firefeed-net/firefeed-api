from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class APIKeyBase(BaseModel):
    name: str
    key: str
    user_id: str


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    user_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class APIKey(APIKeyBase):
    id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True