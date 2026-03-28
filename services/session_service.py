"""
Session service for FireFeed API

This module provides session management using Redis for the API service.
"""

import json
import uuid
from typing import Optional, Dict, Any, Union, List
from datetime import datetime, timedelta
from services.redis_service import RedisService
from config.redis_config import RedisConfig


class SessionService:
    """Session service for FireFeed API using Redis"""
    
    def __init__(self, redis_service: Optional[RedisService] = None):
        """
        Initialize session service
        
        Args:
            redis_service: Redis service instance
        """
        self.redis_service = redis_service or RedisService()
        self.config = self.redis_service.config
    
    def create_session(
        self,
        user_id: Union[int, str],
        data: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> str:
        """
        Create a new session
        
        Args:
            user_id: User ID
            data: Additional session data
            ttl: Session TTL in seconds (uses default if None)
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        ttl = ttl or self.config.session_ttl
        
        session_data = {
            'user_id': str(user_id),
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'data': data or {}
        }
        
        try:
            session_key = self.redis_service.get_session_key(session_id)
            serialized_data = json.dumps(session_data)
            
            result = self.redis_service.get_client().setex(
                session_key,
                ttl,
                serialized_data
            )
            
            if result:
                return session_id
            else:
                raise RuntimeError("Failed to create session")
                
        except Exception as e:
            raise RuntimeError(f"Failed to create session: {e}")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            session_key = self.redis_service.get_session_key(session_id)
            data = self.redis_service.get_client().get(session_key)
            
            if data is None:
                return None
            
            session_data = json.loads(data.decode('utf-8'))
            
            # Update last activity
            session_data['last_activity'] = datetime.utcnow().isoformat()
            self.redis_service.get_client().setex(
                session_key,
                self.config.session_ttl,
                json.dumps(session_data)
            )
            
            return session_data
            
        except Exception as e:
            print(f"Session get error for session {session_id}: {e}")
            return None
    
    def update_session(
        self,
        session_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID
            data: Additional session data to merge
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if session_data is None:
                return False
            
            # Merge new data
            if data:
                session_data['data'].update(data)
            
            session_data['last_activity'] = datetime.utcnow().isoformat()
            
            session_key = self.redis_service.get_session_key(session_id)
            serialized_data = json.dumps(session_data)
            
            result = self.redis_service.get_client().setex(
                session_key,
                self.config.session_ttl,
                serialized_data
            )
            
            return bool(result)
            
        except Exception as e:
            print(f"Session update error for session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_key = self.redis_service.get_session_key(session_id)
            result = self.redis_service.get_client().delete(session_key)
            return bool(result)
            
        except Exception as e:
            print(f"Session delete error for session {session_id}: {e}")
            return False
    
    def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Extend session expiration
        
        Args:
            session_id: Session ID
            ttl: New TTL in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_data = self.get_session(session_id)
            if session_data is None:
                return False
            
            ttl = ttl or self.config.session_ttl
            
            session_key = self.redis_service.get_session_key(session_id)
            serialized_data = json.dumps(session_data)
            
            result = self.redis_service.get_client().setex(
                session_key,
                ttl,
                serialized_data
            )
            
            return bool(result)
            
        except Exception as e:
            print(f"Session extend error for session {session_id}: {e}")
            return False
    
    def get_user_sessions(self, user_id: Union[int, str]) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of session data
        """
        try:
            pattern = self.redis_service.get_session_key("*")
            keys = self.redis_service.get_client().keys(pattern)
            
            sessions = []
            for key in keys:
                data = self.redis_service.get_client().get(key)
                if data:
                    session_data = json.loads(data.decode('utf-8'))
                    if session_data.get('user_id') == str(user_id):
                        sessions.append(session_data)
            
            return sessions
            
        except Exception as e:
            print(f"Get user sessions error for user {user_id}: {e}")
            return []
    
    def delete_user_sessions(self, user_id: Union[int, str]) -> int:
        """
        Delete all sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deleted
        """
        try:
            sessions = self.get_user_sessions(user_id)
            deleted_count = 0
            
            for session in sessions:
                session_id = session.get('session_id')
                if session_id and self.delete_session(session_id):
                    deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            print(f"Delete user sessions error for user {user_id}: {e}")
            return 0
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            pattern = self.redis_service.get_session_key("*")
            keys = self.redis_service.get_client().keys(pattern)
            
            cleaned_count = 0
            for key in keys:
                ttl = self.redis_service.get_client().ttl(key)
                if ttl == -1:  # Key exists but has no expiration
                    self.redis_service.get_client().delete(key)
                    cleaned_count += 1
            
            return cleaned_count
            
        except Exception as e:
            print(f"Session cleanup error: {e}")
            return 0