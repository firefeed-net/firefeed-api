from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TelegramMessageBase(BaseModel):
    message_id: str
    chat_id: str
    user_id: Optional[str] = None
    text: Optional[str] = None
    message_type: str  # text, photo, video, etc.
    timestamp: datetime


class TelegramMessageCreate(TelegramMessageBase):
    pass


class TelegramMessageUpdate(BaseModel):
    message_id: Optional[str] = None
    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    text: Optional[str] = None
    message_type: Optional[str] = None
    timestamp: Optional[datetime] = None


class TelegramMessageResponse(BaseModel):
    id: str
    message_id: str
    chat_id: str
    user_id: Optional[str] = None
    text: Optional[str] = None
    message_type: str
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramMessage(TelegramMessageBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True