from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserCategoryBase(BaseModel):
    user_id: str
    category_id: str


class UserCategoryCreate(UserCategoryBase):
    pass


class UserCategoryUpdate(BaseModel):
    user_id: Optional[str] = None
    category_id: Optional[str] = None


class UserCategoryResponse(BaseModel):
    id: str
    user_id: str
    category_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserCategory(UserCategoryBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True