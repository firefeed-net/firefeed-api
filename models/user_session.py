from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserSessionBase(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime


class UserSessionCreate(UserSessionBase):
    pass


class UserSessionUpdate(BaseModel):
    user_id: Optional[str] = None
    session_token: Optional[str] = None
    expires_at: Optional[datetime] = None


class UserSessionResponse(BaseModel):
    id: str
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class UserSession(UserSessionBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True