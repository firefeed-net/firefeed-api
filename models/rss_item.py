from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RSSItemBase(BaseModel):
    title: str
    link: str
    description: Optional[str] = None
    pub_date: Optional[datetime] = None
    rss_feed_id: str
    guid: Optional[str] = None


class RSSItemCreate(RSSItemBase):
    pass


class RSSItemUpdate(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None
    description: Optional[str] = None
    pub_date: Optional[datetime] = None
    guid: Optional[str] = None


class RSSItemResponse(BaseModel):
    id: str
    title: str
    link: str
    description: Optional[str] = None
    pub_date: Optional[datetime] = None
    rss_feed_id: str
    guid: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RSSItem(RSSItemBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True