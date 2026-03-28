"""Internal API router for FireFeed RSS management."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import aiopg
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/internal", tags=["internal"])

# Pydantic models for API requests/responses
class RSSFeedCreate(BaseModel):
    source_id: int
    url: str
    name: str
    category_id: Optional[int] = None
    language: str = "en"
    is_active: bool = True
    cooldown_minutes: int = 10
    max_news_per_hour: int = 10

class RSSFeedResponse(BaseModel):
    id: int
    source_id: int
    url: str
    name: str
    category_id: Optional[int]
    language: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    cooldown_minutes: int
    max_news_per_hour: int
    source_name: Optional[str] = None
    source_alias: Optional[str] = None
    source_logo: Optional[str] = None
    source_site_url: Optional[str] = None

class RSSFeedsListResponse(BaseModel):
    data: List[RSSFeedResponse]
    total: int
    page: int
    size: int

class RSSItemCreate(BaseModel):
    title: str
    content: str
    link: str
    guid: str
    pub_date: str  # ISO date-time format
    feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    language: str = "en"
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RSSItemResponse(BaseModel):
    news_id: str
    title: str
    content: str
    link: str
    guid: str
    pub_date: str  # ISO date-time format
    feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    language: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: str  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    is_published: bool = False
    published_at: Optional[str] = None  # ISO date-time format
    metadata: Optional[Dict[str, Any]] = None


class RSSItemsListResponse(BaseModel):
    """Response model for RSS items list."""
    data: List[RSSItemResponse]
    total: int
    page: int
    size: int

class UserResponse(BaseModel):
    id: int
    email: str
    language: str
    is_active: bool
    is_verified: bool
    is_deleted: bool
    created_at: str
    updated_at: Optional[str] = None

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    language: Optional[str] = None

class UserRSSFeedCreate(BaseModel):
    user_id: int
    url: str
    name: Optional[str] = None
    category_id: Optional[int] = None
    language: str = "en"

class UserRSSFeedResponse(BaseModel):
    id: int
    user_id: int
    url: str
    name: Optional[str] = None
    category_id: Optional[int] = None
    language: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
    category_name: Optional[str] = None

class UserAPIKeyCreate(BaseModel):
    user_id: int
    name: str

class UserAPIKeyResponse(BaseModel):
    id: int
    user_id: int
    key_hash: str
    limits: Dict[str, Any]
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None

class TelegramLinkResponse(BaseModel):
    link_code: str
    instructions: str

class TelegramLinkStatusResponse(BaseModel):
    is_linked: bool
    telegram_id: Optional[int] = None
    linked_at: Optional[str] = None

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    redis: Optional[str] = None
    db_pool: Optional[Dict[str, int]] = None
    redis_pool: Optional[Dict[str, int]] = None

class MetricsResponse(BaseModel):
    service_id: str
    timestamp: str
    requests_total: int
    requests_per_minute: float
    error_rate: float
    avg_response_time: float
    active_users: int
    rss_feeds_total: int
    rss_items_total: int
    categories_total: int
    sources_total: int
    translation_requests_total: int
    cache_hit_rate: float
    db_connections_active: int
    redis_connections_active: int

async def get_db_connection():
    """Get database connection from pool."""
    try:
        from config.database_config import DatabaseConfig
        database_config = DatabaseConfig.from_env()
        
        conn = await aiopg.connect(
            host=database_config.host,
            port=database_config.port,
            database=database_config.name,
            user=database_config.user,
            password=database_config.password
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for internal services."""
    try:
        # Import configurations
        from config.database_config import DatabaseConfig
        from firefeed_core.config.redis_config import RedisConfig
        
        # Check database connection
        database_config = DatabaseConfig.from_env()
        redis_config = RedisConfig.from_env()
        
        # Test database connection
        import aiopg
        db_pool = await aiopg.create_pool(
            host=database_config.host,
            port=database_config.port,
            database=database_config.name,
            user=database_config.user,
            password=database_config.password,
            minsize=1,
            maxsize=1
        )
        
        # Test Redis connection
        import redis
        redis_client = redis.Redis(
            host=redis_config.host,
            port=redis_config.port,
            password=redis_config.password,
            db=redis_config.db,
            decode_responses=True
        )
        
        # Test connections
        conn = await db_pool.acquire()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
        finally:
            db_pool.release(conn)
        db_pool.close()
        
        redis_client.ping()
        redis_client.close()
        
        return {
            "status": "ok",
            "database": "ok",
            "redis": "ok",
            "db_pool": {"total_connections": 20, "free_connections": 15},
            "redis_pool": {"total_connections": 10, "free_connections": 8}
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "database": "error",
            "redis": "error",
            "error": str(e)
        }

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get service metrics for monitoring."""
    return {
        "service_id": "firefeed-api",
        "timestamp": "2024-01-01T12:00:00Z",
        "requests_total": 1000,
        "requests_per_minute": 15.5,
        "error_rate": 0.02,
        "avg_response_time": 150.2,
        "active_users": 500,
        "rss_feeds_total": 100,
        "rss_items_total": 10000,
        "categories_total": 8,
        "sources_total": 25,
        "translation_requests_total": 500,
        "cache_hit_rate": 0.85,
        "db_connections_active": 15,
        "redis_connections_active": 8
    }

@router.post("/auth/token")
async def generate_service_token(token_data: Dict[str, Any]):
    """Generate service token for internal API access."""
    try:
        # Validate service data
        required_fields = ["service_id", "service_name", "scopes"]
        for field in required_fields:
            if field not in token_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Generate JWT token (simplified for now)
        import jwt
        import time
        
        payload = {
            "service_id": token_data["service_id"],
            "service_name": token_data["service_name"],
            "scopes": token_data["scopes"],
            "exp": time.time() + (token_data.get("expires_in", 1800)),
            "iat": time.time(),
            "iss": "firefeed-api"
        }
        
        token = jwt.encode(payload, "your-secret-key", algorithm="HS256")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": token_data.get("expires_in", 1800),
            "scopes": token_data["scopes"],
            "service_id": token_data["service_id"]
        }
        
    except Exception as e:
        logger.error(f"Error generating service token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int):
    """Get user by ID for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, email, language, is_active, created_at, updated_at, is_verified, is_deleted "
                    "FROM users WHERE id = %s",
                    (user_id,)
                )
                row = await cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="User not found")
                
                return UserResponse(
                    id=row[0],
                    email=row[1],
                    language=row[2],
                    is_active=row[3],
                    created_at=row[4].isoformat() if row[4] else None,
                    updated_at=row[5].isoformat() if row[5] else None,
                    is_verified=row[6],
                    is_deleted=row[7]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/by-email/{email}", response_model=Dict[str, Any])
async def get_user_by_email(email: str):
    """Get user by email for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, email, language, is_active, created_at, updated_at, is_verified, is_deleted "
                    "FROM users WHERE email = %s",
                    (email,)
                )
                row = await cur.fetchone()
                
                if not row:
                    return {"exists": False}
                
                return {
                    "exists": True,
                    "user": {
                        "id": row[0],
                        "email": row[1],
                        "language": row[2],
                        "is_active": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "updated_at": row[5].isoformat() if row[5] else None,
                        "is_verified": row[6],
                        "is_deleted": row[7]
                    }
                }
                
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/users", response_model=UserResponse)
async def create_user(user_data: Dict[str, Any]):
    """Create user for internal services."""
    try:
        # Validate user data
        required_fields = ["email", "password", "language"]
        for field in required_fields:
            if field not in user_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Hash password (simplified for now)
        password_hash = f"hashed_{user_data['password']}"
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (email, password_hash, language, is_active, is_verified, is_deleted, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                    "RETURNING id, email, language, is_active, created_at, updated_at, is_verified, is_deleted",
                    (
                        user_data["email"],
                        password_hash,
                        user_data["language"],
                        False,  # is_active
                        False,  # is_verified
                        False,  # is_deleted
                        "NOW()",
                        "NOW()"
                    )
                )
                row = await cur.fetchone()
                
                return UserResponse(
                    id=row[0],
                    email=row[1],
                    language=row[2],
                    is_active=row[3],
                    created_at=row[4].isoformat() if row[4] else None,
                    updated_at=row[5].isoformat() if row[5] else None,
                    is_verified=row[6],
                    is_deleted=row[7]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update_data: UserUpdateRequest):
    """Update user for internal services."""
    try:
        update_fields = []
        params = []
        
        if user_update_data.email is not None:
            update_fields.append("email = %s")
            params.append(user_update_data.email)
        
        if user_update_data.language is not None:
            update_fields.append("language = %s")
            params.append(user_update_data.language)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.extend([user_id])
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s RETURNING id, email, language, is_active, created_at, updated_at, is_verified, is_deleted"
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="User not found")
                
                return UserResponse(
                    id=row[0],
                    email=row[1],
                    language=row[2],
                    is_active=row[3],
                    created_at=row[4].isoformat() if row[4] else None,
                    updated_at=row[5].isoformat() if row[5] else None,
                    is_verified=row[6],
                    is_deleted=row[7]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete user for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE users SET is_deleted = true WHERE id = %s", (user_id,))
                
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="User not found")
                
                return {"message": "User deleted successfully"}
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/rss/feeds", response_model=RSSFeedsListResponse)
async def get_rss_feeds(
    page: int = Query(1, ge=1),
    size: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    category_id: Optional[int] = Query(None)
):
    """Get RSS feeds for internal services."""
    try:
        offset = (page - 1) * size
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if is_active is not None:
                    where_conditions.append("rf.is_active = %s")
                    params.append(is_active)
                
                if category_id is not None:
                    where_conditions.append("rf.category_id = %s")
                    params.append(category_id)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(*) FROM rss_feeds rf
                    LEFT JOIN sources s ON rf.source_id = s.id
                    {where_clause}
                """
                await cur.execute(count_query, params)
                total_row = await cur.fetchone()
                total = total_row[0] if total_row else 0
                
                # Get feeds with source information
                query = f"""
                    SELECT rf.id, rf.source_id, rf.url, rf.name, rf.category_id, rf.language, 
                           rf.is_active, rf.created_at, rf.updated_at, rf.cooldown_minutes, rf.max_news_per_hour,
                           s.name as source_name, s.alias as source_alias, s.logo as source_logo, s.site_url as source_site_url
                    FROM rss_feeds rf
                    LEFT JOIN sources s ON rf.source_id = s.id
                    {where_clause}
                    ORDER BY rf.created_at DESC 
                    LIMIT %s OFFSET %s
                """
                params.extend([size, offset])
                
                await cur.execute(query, params)
                rows = await cur.fetchall()
                
                feeds = []
                for row in rows:
                    feeds.append(RSSFeedResponse(
                        id=row[0],
                        source_id=row[1],
                        url=row[2],
                        name=row[3],
                        category_id=row[4],
                        language=row[5],
                        is_active=row[6],
                        created_at=row[7].isoformat() if row[7] else None,
                        updated_at=row[8].isoformat() if row[8] else None,
                        cooldown_minutes=row[9] or 10,
                        max_news_per_hour=row[10] or 10,
                        source_name=row[11],
                        source_alias=row[12],
                        source_logo=row[13],
                        source_site_url=row[14]
                    ))
                
                return RSSFeedsListResponse(
                    data=feeds,
                    total=total,
                    page=page,
                    size=size
                )
                
    except Exception as e:
        logger.error(f"Error getting RSS feeds: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/rss/feeds", response_model=RSSFeedResponse)
async def create_rss_feed(feed_data: RSSFeedCreate):
    """Create RSS feed for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    INSERT INTO rss_feeds (source_id, url, name, category_id, language, is_active, 
                                         cooldown_minutes, max_news_per_hour)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, source_id, url, name, category_id, language, is_active, 
                              created_at, updated_at, cooldown_minutes, max_news_per_hour
                """
                params = (
                    feed_data.source_id,
                    feed_data.url,
                    feed_data.name,
                    feed_data.category_id,
                    feed_data.language,
                    feed_data.is_active,
                    feed_data.cooldown_minutes,
                    feed_data.max_news_per_hour
                )
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                return RSSFeedResponse(
                    id=row[0],
                    source_id=row[1],
                    url=row[2],
                    name=row[3],
                    category_id=row[4],
                    language=row[5],
                    is_active=row[6],
                    created_at=row[7].isoformat() if row[7] else None,
                    updated_at=row[8].isoformat() if row[8] else None,
                    cooldown_minutes=row[9] or 10,
                    max_news_per_hour=row[10] or 10
                )
                
    except Exception as e:
        logger.error(f"Error creating RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/rss/feeds/{feed_id}", response_model=RSSFeedResponse)
async def get_rss_feed_by_id(feed_id: int):
    """Get RSS feed by ID for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT rf.id, rf.source_id, rf.url, rf.name, rf.category_id, rf.language, 
                           rf.is_active, rf.created_at, rf.updated_at, rf.cooldown_minutes, rf.max_news_per_hour,
                           s.name as source_name, s.alias as source_alias, s.logo as source_logo, s.site_url as source_site_url
                    FROM rss_feeds rf
                    LEFT JOIN sources s ON rf.source_id = s.id
                    WHERE rf.id = %s
                """
                
                await cur.execute(query, (feed_id,))
                row = await cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="RSS feed not found")
                
                return RSSFeedResponse(
                    id=row[0],
                    source_id=row[1],
                    url=row[2],
                    name=row[3],
                    category_id=row[4],
                    language=row[5],
                    is_active=row[6],
                    created_at=row[7].isoformat() if row[7] else None,
                    updated_at=row[8].isoformat() if row[8] else None,
                    cooldown_minutes=row[9] or 10,
                    max_news_per_hour=row[10] or 10,
                    source_name=row[11],
                    source_alias=row[12],
                    source_logo=row[13],
                    source_site_url=row[14]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RSS feed by ID: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/rss/feeds/{feed_id}", response_model=RSSFeedResponse)
async def update_rss_feed(feed_id: int, feed_data: RSSFeedCreate):
    """Update RSS feed for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    UPDATE rss_feeds 
                    SET source_id = %s, url = %s, name = %s, category_id = %s, language = %s,
                        is_active = %s, cooldown_minutes = %s, max_news_per_hour = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, source_id, url, name, category_id, language, is_active, 
                              created_at, updated_at, cooldown_minutes, max_news_per_hour
                """
                params = (
                    feed_data.source_id,
                    feed_data.url,
                    feed_data.name,
                    feed_data.category_id,
                    feed_data.language,
                    feed_data.is_active,
                    feed_data.cooldown_minutes,
                    feed_data.max_news_per_hour,
                    feed_id
                )
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="RSS feed not found")
                
                return RSSFeedResponse(
                    id=row[0],
                    source_id=row[1],
                    url=row[2],
                    name=row[3],
                    category_id=row[4],
                    language=row[5],
                    is_active=row[6],
                    created_at=row[7].isoformat() if row[7] else None,
                    updated_at=row[8].isoformat() if row[8] else None,
                    cooldown_minutes=row[9] or 10,
                    max_news_per_hour=row[10] or 10
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/rss/feeds/{feed_id}")
async def delete_rss_feed(feed_id: int):
    """Delete RSS feed for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM rss_feeds WHERE id = %s", (feed_id,))
                
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="RSS feed not found")
                
                return {"message": "RSS feed deleted successfully"}
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/rss/items", response_model=RSSItemResponse)
async def create_rss_item(item_data: RSSItemCreate):
    """Create RSS item for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                # Check if news_id already exists
                await cur.execute(
                    "SELECT news_id FROM rss_data WHERE news_id = %s",
                    (item_data.guid,)
                )
                existing = await cur.fetchone()
                
                if existing:
                    # Return existing item instead of creating duplicate
                    await cur.execute(
                        """SELECT news_id, original_title, original_content, original_language, 
                                  category_id, image_filename, created_at, updated_at, rss_feed_id, source_url, video_filename
                           FROM rss_data WHERE news_id = %s""",
                        (item_data.guid,)
                    )
                    row = await cur.fetchone()
                    
                    return RSSItemResponse(
                        news_id=row[0],
                        title=row[1],
                        content=row[2],
                        link=row[9] or "",
                        guid=row[0],
                        pub_date=item_data.pub_date,
                        feed_id=item_data.feed_id,
                        category_id=item_data.category_id,
                        source_id=item_data.source_id,
                        language=item_data.language,
                        image_url=item_data.image_url,
                        video_url=item_data.video_url,
                        created_at=row[6].isoformat() if row[6] else None,
                        updated_at=row[7].isoformat() if row[7] else None,
                        is_published=False,
                        published_at=None,
                        metadata=item_data.metadata
                    )
                
                # Insert new item
                query = """
                    INSERT INTO rss_data (news_id, original_title, original_content, original_language, 
                                                   category_id, image_filename, rss_feed_id, source_url, video_filename)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING news_id, original_title, original_content, original_language, 
                              category_id, image_filename, created_at, updated_at, rss_feed_id, source_url, video_filename
                """
                params = (
                    item_data.guid,
                    item_data.title,
                    item_data.content,
                    item_data.language,
                    item_data.category_id,
                    item_data.image_url,
                    item_data.feed_id,
                    item_data.link,
                    item_data.video_url
                )
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                return RSSItemResponse(
                    news_id=row[0],
                    title=row[1],
                    content=row[2],
                    link=row[9] or "",
                    guid=row[0],
                    pub_date=item_data.pub_date,
                    feed_id=item_data.feed_id,
                    category_id=item_data.category_id,
                    source_id=item_data.source_id,
                    language=item_data.language,
                    image_url=item_data.image_url,
                    video_url=item_data.video_url,
                    created_at=row[6].isoformat() if row[6] else None,
                    updated_at=row[7].isoformat() if row[7] else None,
                    is_published=False,
                    published_at=None,
                    metadata=item_data.metadata
                )
                
    except Exception as e:
        logger.error(f"Error creating RSS item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/rss/items", response_model=RSSItemsListResponse)
async def get_rss_items(
    original_language: Optional[str] = Query(None),
    category_id: Optional[List[int]] = Query(None),
    source_id: Optional[List[int]] = Query(None),
    telegram_published: Optional[bool] = Query(None),
    from_date: Optional[int] = Query(None),
    search_phrase: Optional[str] = Query(None, alias="searchPhrase"),
    news_id: Optional[str] = Query(None),
    source_url: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    limit: Optional[int] = Query(None, le=100, gt=0),
    offset: Optional[int] = Query(None, ge=0)
):
    """Get RSS items for internal services."""
    try:
        # Support both pagination styles
        if limit is not None:
            size = limit
        if offset is not None:
            page = (offset // size) + 1
        
        offset_val = (page - 1) * size
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                # Build WHERE clause
                where_conditions = ["1=1"]  # Always true condition
                params = []
                
                if news_id:
                    where_conditions.append("pnd.news_id = %s")
                    params.append(news_id)
                
                if source_url:
                    where_conditions.append("pnd.source_url = %s")
                    params.append(source_url)
                
                if title:
                    where_conditions.append("pnd.original_title = %s")
                    params.append(title)
                
                if original_language:
                    where_conditions.append("pnd.original_language = %s")
                    params.append(original_language)
                
                if category_id:
                    where_conditions.append("pnd.category_id = %s")
                    params.extend(category_id)
                
                if from_date:
                    import datetime
                    from_date_dt = datetime.datetime.fromtimestamp(from_date)
                    where_conditions.append("pnd.created_at >= %s")
                    params.append(from_date_dt)
                
                if search_phrase:
                    where_conditions.append("(pnd.original_title ILIKE %s OR pnd.original_content ILIKE %s)")
                    params.append(f"%{search_phrase}%")
                    params.append(f"%{search_phrase}%")
                
                where_clause = " AND ".join(where_conditions)
                
                # Get total count
                count_query = f"""
                    SELECT COUNT(*) FROM rss_data pnd
                    LEFT JOIN rss_feeds rf ON pnd.rss_feed_id = rf.id
                    WHERE {where_clause}
                """
                await cur.execute(count_query, params)
                total_row = await cur.fetchone()
                total = total_row[0] if total_row else 0
                
                # Get items
                query = f"""
                    SELECT pnd.news_id, pnd.original_title, pnd.original_content, pnd.original_language,
                           pnd.category_id, pnd.image_filename, pnd.created_at, pnd.updated_at, pnd.rss_feed_id,
                           pnd.source_url, pnd.video_filename, rf.source_id
                    FROM rss_data pnd
                    LEFT JOIN rss_feeds rf ON pnd.rss_feed_id = rf.id
                    WHERE {where_clause}
                    ORDER BY pnd.created_at DESC 
                    LIMIT %s OFFSET %s
                """
                params.extend([size, offset_val])
                
                await cur.execute(query, params)
                rows = await cur.fetchall()
                
                items = []
                for row in rows:
                    items.append(RSSItemResponse(
                        news_id=row[0],
                        title=row[1],
                        content=row[2],
                        link=row[9] or "",
                        guid=row[0],
                        pub_date=row[6].isoformat() if row[6] else None,
                        feed_id=row[8],
                        category_id=row[4],
                        source_id=row[11],
                        language=row[3],
                        image_url=row[5],
                        video_url=row[10],
                        created_at=row[6].isoformat() if row[6] else None,
                        updated_at=row[7].isoformat() if row[7] else None,
                        is_published=False,
                        published_at=None,
                        metadata=None
                    ))
                
                return RSSItemsListResponse(
                    data=items,
                    total=total,
                    page=page,
                    size=size
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RSS items: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/rss/items/{news_id}", response_model=RSSItemResponse)
async def get_rss_item_by_id(news_id: str):
    """Get RSS item by ID for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT pnd.news_id, pnd.original_title, pnd.original_content, pnd.original_language,
                           pnd.category_id, pnd.image_filename, pnd.created_at, pnd.updated_at, pnd.rss_feed_id,
                           pnd.source_url, pnd.video_filename, rf.source_id
                    FROM rss_data pnd
                    LEFT JOIN rss_feeds rf ON pnd.rss_feed_id = rf.id
                    WHERE pnd.news_id = %s
                """
                
                await cur.execute(query, (news_id,))
                row = await cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="RSS item not found")
                
                return RSSItemResponse(
                    news_id=row[0],
                    title=row[1],
                    content=row[2],
                    link=row[9] or "",
                    guid=row[0],
                    pub_date=row[6].isoformat() if row[6] else None,
                    feed_id=row[8],
                    category_id=row[4],
                    source_id=row[11],
                    language=row[3],
                    image_url=row[5],
                    video_url=row[10],
                    created_at=row[6].isoformat() if row[6] else None,
                    updated_at=row[7].isoformat() if row[7] else None,
                    is_published=False,
                    published_at=None,
                    metadata=None
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting RSS item by ID: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_categories(
    limit: int = Query(100, le=1000, gt=0),
    offset: int = Query(0, ge=0),
    source_ids: Optional[List[int]] = Query(None)
):
    """Get categories for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if source_ids:
                    where_conditions.append("c.id IN (SELECT category_id FROM source_categories WHERE source_id = ANY(%s))")
                    params.append(source_ids)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Get categories
                query = f"""
                    SELECT c.id, c.name, c.display_name, c.created_at, c.updated_at
                    FROM categories c
                    {where_clause}
                    ORDER BY c.name
                    LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])
                
                await cur.execute(query, params)
                rows = await cur.fetchall()
                
                categories = []
                for row in rows:
                    categories.append({
                        "id": row[0],
                        "name": row[1],
                        "display_name": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                        "updated_at": row[4].isoformat() if row[4] else None
                    })
                
                return categories
                
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sources", response_model=List[Dict[str, Any]])
async def get_sources(
    limit: int = Query(100, le=1000, gt=0),
    offset: int = Query(0, ge=0),
    category_id: Optional[List[int]] = Query(None)
):
    """Get sources for internal services."""
    try:
        # Parse category_id from list of strings
        category_ids = None
        if category_id:
            try:
                ids = []
                for cid in category_id:
                    if ',' in cid:
                        ids.extend(int(x.strip()) for x in cid.split(',') if x.strip())
                    else:
                        ids.append(int(cid.strip()))
                category_ids = ids if ids else None
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category_id format")
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if category_ids:
                    where_conditions.append("s.id IN (SELECT source_id FROM source_categories WHERE category_id = ANY(%s))")
                    params.append(category_ids)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # Get sources
                query = f"""
                    SELECT s.id, s.name, s.description, s.created_at, s.updated_at, s.alias, s.logo, s.site_url
                    FROM sources s
                    {where_clause}
                    ORDER BY s.name
                    LIMIT %s OFFSET %s
                """
                params.extend([limit, offset])
                
                await cur.execute(query, params)
                rows = await cur.fetchall()
                
                sources = []
                for row in rows:
                    sources.append({
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                        "updated_at": row[4].isoformat() if row[4] else None,
                        "alias": row[5],
                        "logo": row[6],
                        "site_url": row[7]
                    })
                
                return sources
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/user-rss-feeds", response_model=UserRSSFeedResponse)
async def create_user_rss_feed(feed_data: UserRSSFeedCreate):
    """Create user RSS feed for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    INSERT INTO user_rss_feeds (user_id, url, name, category_id, language, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, url, name, category_id, language, is_active, created_at, updated_at
                """
                params = (
                    feed_data.user_id,
                    feed_data.url,
                    feed_data.name,
                    feed_data.category_id,
                    feed_data.language,
                    True  # is_active
                )
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                return UserRSSFeedResponse(
                    id=row[0],
                    user_id=row[1],
                    url=row[2],
                    name=row[3],
                    category_id=row[4],
                    language=row[5],
                    is_active=row[6],
                    created_at=row[7].isoformat() if row[7] else None,
                    updated_at=row[8].isoformat() if row[8] else None,
                    category_name=None  # Would need additional query to get category name
                )
                
    except Exception as e:
        logger.error(f"Error creating user RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user-rss-feeds/{user_id}", response_model=List[UserRSSFeedResponse])
async def get_user_rss_feeds(user_id: int):
    """Get user RSS feeds for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT urf.id, urf.user_id, urf.url, urf.name, urf.category_id, urf.language, 
                           urf.is_active, urf.created_at, urf.updated_at, c.name as category_name
                    FROM user_rss_feeds urf
                    LEFT JOIN categories c ON urf.category_id = c.id
                    WHERE urf.user_id = %s
                    ORDER BY urf.created_at DESC
                """
                
                await cur.execute(query, (user_id,))
                rows = await cur.fetchall()
                
                feeds = []
                for row in rows:
                    feeds.append(UserRSSFeedResponse(
                        id=row[0],
                        user_id=row[1],
                        url=row[2],
                        name=row[3],
                        category_id=row[4],
                        language=row[5],
                        is_active=row[6],
                        created_at=row[7].isoformat() if row[7] else None,
                        updated_at=row[8].isoformat() if row[8] else None,
                        category_name=row[9]
                    ))
                
                return feeds
                
    except Exception as e:
        logger.error(f"Error getting user RSS feeds: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/user-rss-feeds/{user_id}/{feed_id}", response_model=UserRSSFeedResponse)
async def get_user_rss_feed_by_id(user_id: int, feed_id: int):
    """Get user RSS feed by ID for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT urf.id, urf.user_id, urf.url, urf.name, urf.category_id, urf.language, 
                           urf.is_active, urf.created_at, urf.updated_at, c.name as category_name
                    FROM user_rss_feeds urf
                    LEFT JOIN categories c ON urf.category_id = c.id
                    WHERE urf.user_id = %s AND urf.id = %s
                """
                
                await cur.execute(query, (user_id, feed_id))
                row = await cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="User RSS feed not found")
                
                return UserRSSFeedResponse(
                    id=row[0],
                    user_id=row[1],
                    url=row[2],
                    name=row[3],
                    category_id=row[4],
                    language=row[5],
                    is_active=row[6],
                    created_at=row[7].isoformat() if row[7] else None,
                    updated_at=row[8].isoformat() if row[8] else None,
                    category_name=row[9]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user RSS feed by ID: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/user-rss-feeds/{user_id}/{feed_id}", response_model=UserRSSFeedResponse)
async def update_user_rss_feed(user_id: int, feed_id: int, feed_update_data: UserRSSFeedCreate):
    """Update user RSS feed for internal services."""
    try:
        update_fields = []
        params = []
        
        if feed_update_data.url:
            update_fields.append("url = %s")
            params.append(feed_update_data.url)
        
        if feed_update_data.name is not None:
            update_fields.append("name = %s")
            params.append(feed_update_data.name)
        
        if feed_update_data.category_id is not None:
            update_fields.append("category_id = %s")
            params.append(feed_update_data.category_id)
        
        if feed_update_data.language:
            update_fields.append("language = %s")
            params.append(feed_update_data.language)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.extend([user_id, feed_id])
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = f"""
                    UPDATE user_rss_feeds 
                    SET {', '.join(update_fields)}, updated_at = NOW()
                    WHERE user_id = %s AND id = %s
                    RETURNING id, user_id, url, name, category_id, language, is_active, created_at, updated_at
                """
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="User RSS feed not found")
                
                return UserRSSFeedResponse(
                    id=row[0],
                    user_id=row[1],
                    url=row[2],
                    name=row[3],
                    category_id=row[4],
                    language=row[5],
                    is_active=row[6],
                    created_at=row[7].isoformat() if row[7] else None,
                    updated_at=row[8].isoformat() if row[8] else None,
                    category_name=None  # Would need additional query to get category name
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/user-rss-feeds/{user_id}/{feed_id}")
async def delete_user_rss_feed(user_id: int, feed_id: int):
    """Delete user RSS feed for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM user_rss_feeds WHERE user_id = %s AND id = %s", (user_id, feed_id))
                
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="User RSS feed not found")
                
                return {"message": "User RSS feed deleted successfully"}
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user RSS feed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/api-keys", response_model=UserAPIKeyResponse)
async def create_api_key(key_data: UserAPIKeyCreate):
    """Create API key for internal services."""
    try:
        import secrets
        
        # Generate key hash
        key_hash = secrets.token_urlsafe(32)
        limits = {"requests_per_day": 1000, "requests_per_hour": 100}
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    INSERT INTO user_api_keys (user_id, key_hash, limits, is_active)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, user_id, key_hash, limits, is_active, created_at, expires_at
                """
                params = (
                    key_data.user_id,
                    key_hash,
                    json.dumps(limits),
                    True  # is_active
                )
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                return UserAPIKeyResponse(
                    id=row[0],
                    user_id=row[1],
                    key_hash=row[2],
                    limits=row[3],
                    is_active=row[4],
                    created_at=row[5].isoformat() if row[5] else None,
                    expires_at=row[6].isoformat() if row[6] else None
                )
                
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/api-keys/{user_id}", response_model=List[UserAPIKeyResponse])
async def get_user_api_keys(user_id: int):
    """Get user API keys for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                query = """
                    SELECT id, user_id, key_hash, limits, is_active, created_at, expires_at
                    FROM user_api_keys
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """
                
                await cur.execute(query, (user_id,))
                rows = await cur.fetchall()
                
                keys = []
                for row in rows:
                    keys.append(UserAPIKeyResponse(
                        id=row[0],
                        user_id=row[1],
                        key_hash=row[2],
                        limits=row[3],
                        is_active=row[4],
                        created_at=row[5].isoformat() if row[5] else None,
                        expires_at=row[6].isoformat() if row[6] else None
                    ))
                
                return keys
                
    except Exception as e:
        logger.error(f"Error getting user API keys: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/api-keys/{user_id}/{key_id}")
async def delete_api_key(user_id: int, key_id: int):
    """Delete API key for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM user_api_keys WHERE user_id = %s AND id = %s", (user_id, key_id))
                
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="API key not found")
                
                return {"message": "API key deleted successfully"}
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/users/{user_id}/telegram-link", response_model=TelegramLinkResponse)
async def generate_telegram_link(user_id: int):
    """Generate Telegram link code for internal services."""
    try:
        import secrets
        
        # Generate link code
        link_code = secrets.token_urlsafe(16)
        
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                # Check if user exists
                await cur.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not await cur.fetchone():
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Save link code
                await cur.execute(
                    "INSERT INTO user_telegram_links (user_id, link_code, created_at) VALUES (%s, %s, NOW())",
                    (user_id, link_code)
                )
                
                return TelegramLinkResponse(
                    link_code=link_code,
                    instructions="Send this code to the Telegram bot with the command: /link <code>"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Telegram link: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/{user_id}/telegram-link/status", response_model=TelegramLinkStatusResponse)
async def get_telegram_link_status(user_id: int):
    """Get Telegram link status for internal services."""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT telegram_id, linked_at FROM user_telegram_links WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                    (user_id,)
                )
                row = await cur.fetchone()
                
                if not row:
                    return TelegramLinkStatusResponse(
                        is_linked=False,
                        telegram_id=None,
                        linked_at=None
                    )
                
                return TelegramLinkStatusResponse(
                    is_linked=row[0] is not None,
                    telegram_id=row[0],
                    linked_at=row[1].isoformat() if row[1] else None
                )
                
    except Exception as e:
        logger.error(f"Error getting Telegram link status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/translation/translate")
async def translate_text(translation_data: Dict[str, Any]):
    """Translate text for internal services."""
    try:
        # Validate translation data
        required_fields = ["text", "target_language"]
        for field in required_fields:
            if field not in translation_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Simplified translation response (would integrate with actual translation service)
        return {
            "original_text": translation_data["text"],
            "translated_text": f"Translated: {translation_data['text']}",
            "source_language": translation_data.get("source_language", "auto"),
            "target_language": translation_data["target_language"],
            "model_used": translation_data.get("model", "facebook/m2m100_418M"),
            "confidence": 0.95,
            "processing_time": 1.2
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")