from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserRSSFeedBase(BaseModel):
    user_id: str
    rss_feed_id: str


class UserRSSFeedCreate(UserRSSFeedBase):
    pass


class UserRSSFeedUpdate(BaseModel):
    user_id: Optional[str] = None
    rss_feed_id: Optional[str] = None


class UserRSSFeedResponse(BaseModel):
    id: str
    user_id: str
    rss_feed_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserRSSFeed(UserRSSFeedBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True