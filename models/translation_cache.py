from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TranslationCacheBase(BaseModel):
    source_text: str
    target_text: str
    source_language: str
    target_language: str
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    cache_key: str


class TranslationCacheCreate(TranslationCacheBase):
    pass


class TranslationCacheUpdate(BaseModel):
    source_text: Optional[str] = None
    target_text: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    cache_key: Optional[str] = None


class TranslationCacheResponse(BaseModel):
    id: str
    source_text: str
    target_text: str
    source_language: str
    target_language: str
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    cache_key: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranslationCache(TranslationCacheBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True