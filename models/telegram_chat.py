from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TelegramChatBase(BaseModel):
    chat_id: str
    title: Optional[str] = None
    type: str  # group, supergroup, channel, private
    username: Optional[str] = None


class TelegramChatCreate(TelegramChatBase):
    pass


class TelegramChatUpdate(BaseModel):
    chat_id: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    username: Optional[str] = None


class TelegramChatResponse(BaseModel):
    id: str
    chat_id: str
    title: Optional[str] = None
    type: str
    username: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramChat(TelegramChatBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True