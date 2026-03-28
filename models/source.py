from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SourceBase(BaseModel):
    name: str
    url: str
    category_id: str
    is_active: bool = True


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    category_id: Optional[str] = None
    is_active: Optional[bool] = None


class SourceResponse(BaseModel):
    id: str
    name: str
    url: str
    category_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Source(SourceBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True