"""Internal API router for FireFeed RSS management."""

import logging
import hmac
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import aiopg
import json
import bcrypt
import jwt as pyjwt
from datetime import datetime
from config.environment import settings

logger = logging.getLogger(__name__)

# ---- Inline service token verification for use in main app ----
# Since the internal router runs in the main app context (not the separate
# internal app), we inline a simplified token verification that doesn't
# depend on the internal/ package.


def verify_service_token(token: str) -> Dict[str, Any]:
    """Verify a service authentication token (simplified for main app context)."""
    try:
        payload = pyjwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp"]}
        )
        service_name = payload.get("sub") or payload.get("service_name", "unknown")
        # Support both 'scopes' and 'scope' claim names
        scopes = payload.get("scopes") or payload.get("scope", [])
        return {
            "service_name": service_name,
            "scopes": scopes,
            "token_valid": True
        }
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except pyjwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


_security = HTTPBearer(auto_error=True)  # Require Bearer token


async def get_service_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_security)
) -> Dict[str, Any]:
    """Extract and verify service auth from request. Requires valid Bearer token."""
    return verify_service_token(credentials.credentials)


router = APIRouter(
    prefix="/api/v1/internal",
    tags=["internal"],
    dependencies=[Depends(get_service_auth)]  # Require service authentication for all internal endpoints
)

# Database connection pool (managed via lifespan context manager in main app)
_db_pool: Optional[aiopg.Pool] = None


async def get_db_pool() -> aiopg.Pool:
    """Get the database connection pool."""
    global _db_pool
    if _db_pool is None:
        from config.database_config import DatabaseConfig
        database_config = DatabaseConfig.from_env()
        _db_pool = await aiopg.create_pool(
            host=database_config.host,
            port=database_config.port,
            database=database_config.name,
            user=database_config.user,
            password=database_config.password,
            minsize=database_config.minsize,
            maxsize=database_config.maxsize,
        )
    return _db_pool


async def close_db_pool():
    """Close the database connection pool."""
    global _db_pool
    if _db_pool:
        _db_pool.close()
        await _db_pool.wait_closed()
        _db_pool = None


async def get_db_connection():
    """
    Get database connection from pool as an async context manager.
    Usage: async with get_db_connection() as conn: ...
    This ensures connections are always released back to the pool.
    """
    pool = await get_db_pool()
    return _ConnectionContextManager(pool)


class _ConnectionContextManager:
    """Async context manager that ensures connection is released."""
    def __init__(self, pool):
        self.pool = pool
        self.conn = None

    async def __aenter__(self):
        self.conn = await self.pool.acquire()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.pool.release(self.conn)
        return False

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
    news_id: str
    original_title: str
    original_content: str
    source_url: str
    pub_date: str  # ISO date-time format
    rss_feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    original_language: str = "en"
    image_filename: Optional[str] = None
    video_filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RSSItemResponse(BaseModel):
    news_id: str
    original_title: str
    original_content: str
    source_url: str
    pub_date: str  # ISO date-time format
    rss_feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    original_language: str
    image_filename: Optional[str] = None
    video_filename: Optional[str] = None
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

class ServiceTokenRequest(BaseModel):
    """Request model for service token generation."""
    service_id: str
    service_name: str
    scopes: List[str]
    expires_in: int = 1800  # 30 minutes default

class UserCreateRequest(BaseModel):
    """Request model for user creation with password validation."""
    email: str
    password: str = Field(..., min_length=8, max_length=128)
    language: str = "en"

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for internal services."""
    try:
        # Import configurations
        from config.database_config import DatabaseConfig
        from firefeed_core.config.redis_config import RedisConfig

        # Check database connection using shared pool
        pool = await get_db_pool()
        conn = await pool.acquire()
        try:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()
            db_status = "ok"
        finally:
            pool.release(conn)

        # Test Redis connection
        import redis
        redis_config = RedisConfig.from_env()
        redis_client = redis.Redis(
            host=redis_config.host,
            port=redis_config.port,
            password=redis_config.password,
            db=redis_config.db,
            decode_responses=True
        )

        try:
            redis_client.ping()
            redis_status = "ok"
        finally:
            redis_client.close()

        # Get pool stats
        pool_size = pool.size
        pool_free = pool.freesize

        # Get actual Redis connection info
        try:
            redis_info = redis_client.info()
            redis_connected_clients = redis_info.get("connected_clients", 0)
            redis_pool = {"total_connections": redis_connected_clients, "free_connections": max(0, redis_connected_clients)}
        except Exception:
            # Fallback to None if Redis info unavailable
            redis_pool = None

        return {
            "status": "ok",
            "database": db_status,
            "redis": redis_status,
            "db_pool": {"total_connections": pool_size, "free_connections": pool_free},
            "redis_pool": redis_pool
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
    try:
        pool = await get_db_pool()
        pool_size = pool.size
        pool_free = pool.freesize

        # Whitelist of allowed tables to prevent SQL injection
        ALLOWED_TABLES = {
            "rss_feeds": "rf",
            "rss_data": "rd",
            "categories": "c",
            "sources": "s"
        }

        # Get actual counts from database
        conn = await pool.acquire()
        try:
            async with conn.cursor() as cur:
                counts = {}
                for table, alias in ALLOWED_TABLES.items():
                    # Use validated table name (whitelist ensures safety)
                    await cur.execute(f"SELECT COUNT(*) FROM {table} {alias}")
                    row = await cur.fetchone()
                    counts[f"{table}_total"] = row[0] if row else 0

                # Get translation requests count - add to whitelist for safety
                ALLOWED_COUNT_TABLES = {
                    "news_translations": "nt"
                }
                try:
                    for table, alias in ALLOWED_COUNT_TABLES.items():
                        await cur.execute(f"SELECT COUNT(*) FROM {table} {alias}")
                        row = await cur.fetchone()
                        counts["translation_requests_total"] = row[0] if row else 0
                except Exception:
                    counts["translation_requests_total"] = 0
        finally:
            pool.release(conn)

        # Get metrics from middleware if available
        from internal.middleware import metrics_middleware
        mw_metrics = metrics_middleware.get_metrics()

        return {
            "service_id": "firefeed-api",
            "timestamp": datetime.utcnow().isoformat(),
            "requests_total": mw_metrics.get("requests_total", 0),
            "requests_per_minute": 0.0,  # Would need time-windowed tracking
            "error_rate": mw_metrics.get("errors_total", 0) / max(mw_metrics.get("requests_total", 1), 1),
            "avg_response_time": mw_metrics.get("processing_time_avg", 0.0),
            "active_users": 0,  # Would need session tracking
            "rss_feeds_total": counts.get("rss_feeds_total", 0),
            "rss_items_total": counts.get("rss_data_total", 0),
            "categories_total": counts.get("categories_total", 0),
            "sources_total": counts.get("sources_total", 0),
            "translation_requests_total": counts.get("translation_requests_total", 0),
            "cache_hit_rate": 0.0,  # Would need Redis stats
            "db_connections_active": pool_size - pool_free,
            "redis_connections_active": 0  # Would need Redis pool stats
        }
    except Exception as e:
        logger.error(f"Error collecting metrics: {e}")
        return {
            "service_id": "firefeed-api",
            "timestamp": datetime.utcnow().isoformat(),
            "requests_total": 0,
            "requests_per_minute": 0.0,
            "error_rate": 0.0,
            "avg_response_time": 0.0,
            "active_users": 0,
            "rss_feeds_total": 0,
            "rss_items_total": 0,
            "categories_total": 0,
            "sources_total": 0,
            "translation_requests_total": 0,
            "cache_hit_rate": 0.0,
            "db_connections_active": 0,
            "redis_connections_active": 0
        }

@router.post("/auth/token")
async def generate_service_token(
    token_data: ServiceTokenRequest,
    auth_result: Dict[str, Any] = Depends(get_service_auth)
):
    """Generate service token for internal API access. Requires admin service authentication."""
    try:
        # Verify that the requesting service has admin scope
        if "admin" not in auth_result.get("scopes", []) and auth_result.get("service_name") != "internal-api":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to generate service tokens"
            )

        # Generate JWT token
        import jwt
        import time

        payload = {
            "service_id": token_data.service_id,
            "service_name": token_data.service_name,
            "scopes": token_data.scopes,
            "exp": time.time() + token_data.expires_in,
            "iat": time.time(),
            "iss": "firefeed-api"
        }

        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": token_data.expires_in,
            "scopes": token_data.scopes,
            "service_id": token_data.service_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating service token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int):
    """Get user by ID for internal services."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
async def create_user(user_data: UserCreateRequest):
    """Create user for internal services."""
    try:
        # Validate email format
        if "@" not in user_data.email:
            raise HTTPException(status_code=400, detail="Invalid email address")

        # Validate password strength
        if len(user_data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        if user_data.password.isdigit() or user_data.password.isalpha():
            raise HTTPException(status_code=400, detail="Password must contain both letters and numbers")

        # Hash password with bcrypt
        password_bytes = user_data.password.encode('utf-8')
        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO users (email, password_hash, language, is_active, is_verified, is_deleted, created_at, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW()) "
                    "RETURNING id, email, language, is_active, created_at, updated_at, is_verified, is_deleted",
                    (
                        user_data.email,
                        password_hash,
                        user_data.language,
                        False,  # is_active
                        False,  # is_verified
                        False,  # is_deleted
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
        # Whitelist of allowed updatable columns to prevent SQL injection
        ALLOWED_UPDATE_FIELDS = {"email", "language"}

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

        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Build query with whitelisted field names only
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Check if news_id already exists
                await cur.execute(
                    "SELECT news_id FROM rss_data WHERE news_id = %s",
                    (item_data.news_id,)
                )
                existing = await cur.fetchone()
                
                if existing:
                    # Return existing item instead of creating duplicate
                    await cur.execute(
                        """SELECT news_id, original_title, original_content, original_language, 
                                  category_id, image_filename, created_at, updated_at, rss_feed_id, source_url, video_filename
                           FROM rss_data WHERE news_id = %s""",
                        (item_data.news_id,)
                    )
                    row = await cur.fetchone()
                    
                    return RSSItemResponse(
                        news_id=row[0],
                        original_title=row[1],
                        original_content=row[2],
                        source_url=row[9] or "",
                        pub_date=item_data.pub_date,
                        rss_feed_id=row[8],
                        category_id=item_data.category_id,
                        source_id=item_data.source_id,
                        original_language=item_data.original_language,
                        image_filename=row[5],
                        video_filename=row[10],
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
                    item_data.news_id,
                    item_data.original_title,
                    item_data.original_content,
                    item_data.original_language,
                    item_data.category_id,
                    item_data.image_filename,
                    item_data.rss_feed_id,
                    item_data.source_url,
                    item_data.video_filename
                )
                
                await cur.execute(query, params)
                row = await cur.fetchone()
                
                return RSSItemResponse(
                    news_id=row[0],
                    original_title=row[1],
                    original_content=row[2],
                    source_url=row[9] or "",
                    pub_date=item_data.pub_date,
                    rss_feed_id=item_data.rss_feed_id,
                    category_id=item_data.category_id,
                    source_id=item_data.source_id,
                    original_language=item_data.original_language,
                    image_filename=item_data.image_filename,
                    video_filename=item_data.video_filename,
                    created_at=row[6].isoformat() if row[6] else None,
                    updated_at=row[7].isoformat() if row[7] else None,
                    is_published=False,
                    published_at=None,
                    metadata=item_data.metadata
                )
                
    except Exception as e:
        logger.error(f"Error creating RSS item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/rss/items/{news_id}", response_model=RSSItemResponse)
async def update_rss_item(news_id: str, item_data: RSSItemCreate):
    """Update RSS item for internal services."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Check if item exists
                await cur.execute(
                    "SELECT news_id FROM rss_data WHERE news_id = %s",
                    (news_id,)
                )
                existing = await cur.fetchone()

                if not existing:
                    raise HTTPException(status_code=404, detail="RSS item not found")

                # Update item
                query = """
                    UPDATE rss_data 
                    SET original_title = %s,
                        original_content = %s,
                        original_language = %s,
                        category_id = %s,
                        image_filename = %s,
                        video_filename = %s,
                        updated_at = NOW()
                    WHERE news_id = %s
                    RETURNING news_id, original_title, original_content, original_language,
                              category_id, image_filename, created_at, updated_at, rss_feed_id, source_url, video_filename
                """
                params = (
                    item_data.original_title,
                    item_data.original_content,
                    item_data.original_language,
                    item_data.category_id,
                    item_data.image_filename,
                    item_data.video_filename,
                    news_id
                )

                await cur.execute(query, params)
                row = await cur.fetchone()

                if not row:
                    raise HTTPException(status_code=500, detail="Failed to update RSS item")

                return RSSItemResponse(
                    news_id=row[0],
                    original_title=row[1],
                    original_content=row[2],
                    source_url=row[9] or "",
                    pub_date=item_data.pub_date,
                    rss_feed_id=row[8],
                    category_id=item_data.category_id,
                    source_id=item_data.source_id,
                    original_language=item_data.original_language,
                    image_filename=row[5],
                    video_filename=row[10],
                    created_at=row[6].isoformat() if row[6] else None,
                    updated_at=row[7].isoformat() if row[7] else None,
                    is_published=False,
                    published_at=None,
                    metadata=item_data.metadata
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RSS item {news_id}: {e}")
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
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
                        original_title=row[1],
                        original_content=row[2],
                        source_url=row[9] or "",
                        pub_date=row[6].isoformat() if row[6] else None,
                        rss_feed_id=row[8],
                        category_id=row[4],
                        source_id=row[11],
                        original_language=row[3],
                        image_filename=row[5],
                        video_filename=row[10],
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
                    original_title=row[1],
                    original_content=row[2],
                    source_url=row[9] or "",
                    pub_date=row[6].isoformat() if row[6] else None,
                    rss_feed_id=row[8],
                    category_id=row[4],
                    source_id=row[11],
                    original_language=row[3],
                    image_filename=row[5],
                    video_filename=row[10],
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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
        pool = await get_db_pool()
        async with pool.acquire() as conn:
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