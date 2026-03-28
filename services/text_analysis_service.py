# services/text_analysis_service.py - Text analysis service using repositories
import logging
from typing import List, Dict, Any, Optional
from firefeed_core.interfaces import ITextAnalysisRepository

logger = logging.getLogger(__name__)


class TextAnalysisService:
    """Text analysis service using repository pattern"""
    
    def __init__(self, text_analysis_repository: ITextAnalysisRepository):
        self.text_analysis_repository = text_analysis_repository
    
    async def get_text_analysis(self, news_id: str) -> Optional[Dict[str, Any]]:
        """Get text analysis by news ID"""
        try:
            return await self.text_analysis_repository.get_text_analysis(news_id)
        except Exception as e:
            logger.error(f"Error getting text analysis for news {news_id}: {e}")
            raise
    
    async def create_text_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """Create new text analysis"""
        try:
            return await self.text_analysis_repository.create_text_analysis(analysis_data)
        except Exception as e:
            logger.error(f"Error creating text analysis: {e}")
            raise
    
    async def update_text_analysis(self, analysis_id: int, analysis_data: Dict[str, Any]) -> bool:
        """Update text analysis"""
        try:
            return await self.text_analysis_repository.update_text_analysis(analysis_id, analysis_data)
        except Exception as e:
            logger.error(f"Error updating text analysis {analysis_id}: {e}")
            raise
    
    async def delete_text_analysis(self, analysis_id: int) -> bool:
        """Delete text analysis"""
        try:
            return await self.text_analysis_repository.delete_text_analysis(analysis_id)
        except Exception as e:
            logger.error(f"Error deleting text analysis {analysis_id}: {e}")
            raise
    
    async def get_text_analyses_by_news_id(self, news_id: str) -> List[Dict[str, Any]]:
        """Get text analyses by news ID"""
        try:
            return await self.text_analysis_repository.get_text_analyses_by_news_id(news_id)
        except Exception as e:
            logger.error(f"Error getting text analyses for news {news_id}: {e}")
            raise