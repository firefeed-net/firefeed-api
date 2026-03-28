from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PasswordResetTokenBase(BaseModel):
    user_id: str
    token: str
    expires_at: datetime


class PasswordResetTokenCreate(PasswordResetTokenBase):
    pass


class PasswordResetTokenUpdate(BaseModel):
    user_id: Optional[str] = None
    token: Optional[str] = None
    expires_at: Optional[datetime] = None


class PasswordResetTokenResponse(BaseModel):
    id: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordResetToken(PasswordResetTokenBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True