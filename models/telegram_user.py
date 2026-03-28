from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TelegramUserBase(BaseModel):
    user_id: str
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramUserCreate(TelegramUserBase):
    pass


class TelegramUserUpdate(BaseModel):
    user_id: Optional[str] = None
    telegram_id: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramUserResponse(BaseModel):
    id: str
    user_id: str
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TelegramUser(TelegramUserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True