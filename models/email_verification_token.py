from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmailVerificationTokenBase(BaseModel):
    user_id: str
    token: str
    expires_at: datetime


class EmailVerificationTokenCreate(EmailVerificationTokenBase):
    pass


class EmailVerificationTokenUpdate(BaseModel):
    user_id: Optional[str] = None
    token: Optional[str] = None
    expires_at: Optional[datetime] = None


class EmailVerificationTokenResponse(BaseModel):
    id: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class EmailVerificationToken(EmailVerificationTokenBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True