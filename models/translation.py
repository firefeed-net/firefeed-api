from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TranslationBase(BaseModel):
    source_text: str
    target_text: str
    source_language: str
    target_language: str
    model_used: Optional[str] = None
    confidence: Optional[float] = None


class TranslationCreate(TranslationBase):
    pass


class TranslationUpdate(BaseModel):
    source_text: Optional[str] = None
    target_text: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    model_used: Optional[str] = None
    confidence: Optional[float] = None


class TranslationResponse(BaseModel):
    id: str
    source_text: str
    target_text: str
    source_language: str
    target_language: str
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Translation(TranslationBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True