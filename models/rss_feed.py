from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RSSFeedBase(BaseModel):
    title: str
    url: str
    source_id: str
    is_active: bool = True


class RSSFeedCreate(RSSFeedBase):
    pass


class RSSFeedUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    source_id: Optional[str] = None
    is_active: Optional[bool] = None


class RSSFeedResponse(BaseModel):
    id: str
    title: str
    url: str
    source_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RSSFeed(RSSFeedBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True