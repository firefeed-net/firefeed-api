# FireFeed API Reference

This document provides comprehensive documentation for the FireFeed API, including all endpoints, request/response formats, authentication, and examples.

## Table of Contents

1. [Authentication](#authentication)
2. [Public API Endpoints](#public-api-endpoints)
   - [Auth Endpoints](#auth-endpoints)
   - [User Endpoints](#user-endpoints)
   - [RSS Endpoints](#rss-endpoints)
3. [Internal API Endpoints](#internal-api-endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Examples](#examples)

## Authentication

### User Authentication (OAuth2 Password Flow)

The API uses JWT tokens for authentication. Users must first authenticate to receive an access token.

**Token Format:**
```
Authorization: Bearer <jwt_token>
```

**Token Expiration:** 30 minutes

**Token Refresh:** Not implemented in current version

### Service Authentication

Internal services use service tokens for authentication.

**Service Token Format:**
```
X-Service-Token: <service_token>
```

## Public API Endpoints

### Auth Endpoints

#### Register User
```http
POST /api/v1/auth/register
```

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "language": "en"
}
```

**Response (201 Created):**
```json
{
  "message": "Registration successful. Please check your email for verification instructions.",
  "user_id": "user-uuid"
}
```

#### Verify Email
```http
POST /api/v1/auth/verify
```

**Request:**
```json
{
  "email": "user@example.com",
  "verification_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully"
}
```

#### Resend Verification
```http
POST /api/v1/auth/resend-verification
```

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Verification email sent"
}
```

#### Login
```http
POST /api/v1/auth/login
```

**Request:**
```json
{
  "username": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Request Password Reset
```http
POST /api/v1/auth/reset-password/request
```

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset instructions sent to your email"
}
```

#### Confirm Password Reset
```http
POST /api/v1/auth/reset-password/confirm
```

**Request:**
```json
{
  "email": "user@example.com",
  "reset_code": "123456",
  "new_password": "newsecurepassword123"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset successful"
}
```

### User Endpoints

#### Get Current User
```http
GET /api/v1/users/me
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "language": "en",
  "is_active": true,
  "is_verified": true,
  "is_deleted": false,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

#### Update User
```http
PUT /api/v1/users/me
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request:**
```json
{
  "language": "de"
}
```

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "language": "de",
  "is_active": true,
  "is_verified": true,
  "is_deleted": false,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:30:00Z"
}
```

#### Delete User
```http
DELETE /api/v1/users/me
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "message": "User account deleted successfully"
}
```

#### Get User RSS Items
```http
GET /api/v1/users/me/rss-items/
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `limit` (integer, optional): Number of items to return (default: 20, max: 100)
- `offset` (integer, optional): Number of items to skip (default: 0)
- `original_language` (string, optional): Filter by original language
- `category_id` (array, optional): Filter by category IDs
- `source_id` (array, optional): Filter by source IDs
- `telegram_published` (boolean, optional): Filter by Telegram publication status
- `from_date` (string, optional): Filter items from this date (ISO 8601 format)
- `search_phrase` (string, optional): Search in title and content

**Response (200 OK):**
```json
{
  "count": 100,
  "results": [
    {
      "news_id": "item-uuid",
      "original_title": "News Title",
      "original_content": "News content...",
      "original_language": "en",
      "category_id": "category-uuid",
      "image_filename": "image.jpg",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z",
      "rss_feed_id": "feed-uuid",
      "embedding": [0.1, 0.2, ...],
      "source_url": "https://example.com/news",
      "video_filename": "video.mp4"
    }
  ]
}
```

#### Get User Categories
```http
GET /api/v1/users/me/categories/
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": "category-uuid",
      "name": "Technology",
      "description": "Technology news and updates",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    }
  ]
}
```

#### Get User RSS Feeds
```http
GET /api/v1/users/me/rss-feeds/
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "count": 3,
  "results": [
    {
      "id": "feed-uuid",
      "name": "Tech News",
      "url": "https://tech.example.com/rss",
      "category_id": "category-uuid",
      "user_id": "user-uuid",
      "is_active": true,
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    }
  ]
}
```

#### Create RSS Feed
```http
POST /api/v1/users/me/rss-feeds/
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request:**
```json
{
  "name": "Tech News",
  "url": "https://tech.example.com/rss",
  "category_id": "category-uuid"
}
```

**Response (201 Created):**
```json
{
  "id": "feed-uuid",
  "name": "Tech News",
  "url": "https://tech.example.com/rss",
  "category_id": "category-uuid",
  "user_id": "user-uuid",
  "is_active": true,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

#### Get User API Keys
```http
GET /api/v1/users/me/api-keys/
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "count": 2,
  "results": [
    {
      "id": "key-uuid",
      "name": "Mobile App",
      "key": "ak_live_...",
      "is_active": true,
      "created_at": "2023-01-01T12:00:00Z",
      "last_used_at": "2023-01-01T12:00:00Z"
    }
  ]
}
```

#### Create API Key
```http
POST /api/v1/users/me/api-keys/
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request:**
```json
{
  "name": "Mobile App"
}
```

**Response (201 Created):**
```json
{
  "id": "key-uuid",
  "name": "Mobile App",
  "key": "ak_live_...",
  "is_active": true,
  "created_at": "2023-01-01T12:00:00Z",
  "last_used_at": null
}
```

#### Get Telegram Status
```http
GET /api/v1/users/me/telegram/status
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "is_linked": true,
  "telegram_id": 123456789,
  "username": "username",
  "chat_id": 987654321
}
```

#### Generate Telegram Link
```http
POST /api/v1/users/me/telegram/generate-link
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "link_code": "abc123",
  "expires_at": "2023-01-01T12:30:00Z"
}
```

### RSS Endpoints

#### Get RSS Items
```http
GET /api/v1/rss-items/
```

**Query Parameters:**
- `limit` (integer, optional): Number of items to return (default: 20, max: 100)
- `offset` (integer, optional): Number of items to skip (default: 0)
- `original_language` (string, optional): Filter by original language
- `category_id` (array, optional): Filter by category IDs
- `source_id` (array, optional): Filter by source IDs
- `telegram_published` (boolean, optional): Filter by Telegram publication status
- `from_date` (string, optional): Filter items from this date (ISO 8601 format)
- `search_phrase` (string, optional): Search in title and content

**Response (200 OK):**
```json
{
  "count": 100,
  "results": [
    {
      "news_id": "item-uuid",
      "original_title": "News Title",
      "original_content": "News content...",
      "original_language": "en",
      "category_id": "category-uuid",
      "image_filename": "image.jpg",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z",
      "rss_feed_id": "feed-uuid",
      "embedding": [0.1, 0.2, ...],
      "source_url": "https://example.com/news",
      "video_filename": "video.mp4"
    }
  ]
}
```

#### Get RSS Item by ID
```http
GET /api/v1/rss-items/{rss_item_id}
```

**Response (200 OK):**
```json
{
  "news_id": "item-uuid",
  "original_title": "News Title",
  "original_content": "News content...",
  "original_language": "en",
  "category_id": "category-uuid",
  "image_filename": "image.jpg",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z",
  "rss_feed_id": "feed-uuid",
  "embedding": [0.1, 0.2, ...],
  "source_url": "https://example.com/news",
  "video_filename": "video.mp4"
}
```

#### Get Categories
```http
GET /api/v1/categories/
```

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": "category-uuid",
      "name": "Technology",
      "description": "Technology news and updates",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    }
  ]
}
```

#### Get Sources
```http
GET /api/v1/sources/
```

**Response (200 OK):**
```json
{
  "count": 10,
  "results": [
    {
      "id": "source-uuid",
      "name": "TechCrunch",
      "url": "https://techcrunch.com",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    }
  ]
}
```

#### Get Supported Languages
```http
GET /api/v1/languages/
```

**Response (200 OK):**
```json
{
  "languages": [
    {
      "code": "en",
      "name": "English",
      "native_name": "English"
    },
    {
      "code": "de",
      "name": "German",
      "native_name": "Deutsch"
    },
    {
      "code": "ru",
      "name": "Russian",
      "native_name": "Русский"
    }
  ]
}
```

#### Health Check
```http
GET /api/v1/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T12:00:00Z",
  "version": "1.0.0"
}
```

#### Get RSS Feeds
```http
GET /api/v1/rss/feeds/
```

**Response (200 OK):**
```json
{
  "count": 3,
  "results": [
    {
      "id": "feed-uuid",
      "name": "Tech News",
      "url": "https://tech.example.com/rss",
      "category_id": "category-uuid",
      "user_id": "user-uuid",
      "is_active": true,
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z"
    }
  ]
}
```

#### Get RSS Feed by ID
```http
GET /api/v1/rss/feeds/{feed_id}
```

**Response (200 OK):**
```json
{
  "id": "feed-uuid",
  "name": "Tech News",
  "url": "https://tech.example.com/rss",
  "category_id": "category-uuid",
  "user_id": "user-uuid",
  "is_active": true,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

#### Translate Text
```http
POST /api/v1/translation/translate
```

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request:**
```json
{
  "text": "Hello, world!",
  "source_language": "en",
  "target_language": "de"
}
```

**Response (200 OK):**
```json
{
  "original_text": "Hello, world!",
  "translated_text": "Hallo, Welt!",
  "source_language": "en",
  "target_language": "de",
  "confidence": 0.95
}
```

## Internal API Endpoints

### Auth Endpoints

#### Get Service Token
```http
POST /api/v1/internal/auth/token
```

**Headers:**
```
X-Service-Token: <service_token>
```

**Response (200 OK):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### User Endpoints

#### Get User by ID
```http
GET /api/v1/internal/users/{user_id}
```

**Headers:**
```
X-Service-Token: <service_token>
```

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "language": "en",
  "is_active": true,
  "is_verified": true,
  "is_deleted": false,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

### RSS Endpoints

#### Get RSS Item by ID
```http
GET /api/v1/internal/rss/items/{rss_item_id}
```

**Headers:**
```
X-Service-Token: <service_token>
```

**Response (200 OK):**
```json
{
  "news_id": "item-uuid",
  "original_title": "News Title",
  "original_content": "News content...",
  "original_language": "en",
  "category_id": "category-uuid",
  "image_filename": "image.jpg",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z",
  "rss_feed_id": "feed-uuid",
  "embedding": [0.1, 0.2, ...],
  "source_url": "https://example.com/news",
  "video_filename": "video.mp4"
}
```

#### Create RSS Item
```http
POST /api/v1/internal/rss/items/
```

**Headers:**
```
X-Service-Token: <service_token>
```

**Request:**
```json
{
  "original_title": "News Title",
  "original_content": "News content...",
  "original_language": "en",
  "category_id": "category-uuid",
  "rss_feed_id": "feed-uuid",
  "source_url": "https://example.com/news"
}
```

**Response (201 Created):**
```json
{
  "news_id": "item-uuid",
  "original_title": "News Title",
  "original_content": "News content...",
  "original_language": "en",
  "category_id": "category-uuid",
  "image_filename": null,
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z",
  "rss_feed_id": "feed-uuid",
  "embedding": null,
  "source_url": "https://example.com/news",
  "video_filename": null
}
```

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `validation_error` | 422 | Request validation failed |
| `authentication_error` | 401 | Authentication required or failed |
| `authorization_error` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `conflict` | 409 | Resource conflict (e.g., duplicate email) |
| `rate_limit_exceeded` | 429 | Rate limit exceeded |
| `internal_error` | 500 | Internal server error |

### Examples

#### Validation Error
```json
{
  "error": "validation_error",
  "message": "Invalid email format",
  "details": {
    "email": "Email must be a valid email address"
  }
}
```

#### Authentication Error
```json
{
  "error": "authentication_error",
  "message": "Invalid or expired token"
}
```

#### Not Found Error
```json
{
  "error": "not_found",
  "message": "User not found",
  "details": {
    "user_id": "user-uuid"
  }
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Public API**: 300 requests per minute per IP address
- **Internal API**: 1000 requests per minute per service

### Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded Response

When rate limit is exceeded:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please try again later.",
  "details": {
    "retry_after": 60
  }
}
```

## Examples

### Complete Authentication Flow

1. **Register User:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "language": "en"
  }'
```

2. **Verify Email:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "verification_code": "123456"
  }'
```

3. **Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "securepassword123"
  }'
```

4. **Use Token for Authenticated Requests:**
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Getting RSS Items

```bash
curl -X GET "http://localhost:8000/api/v1/rss-items/?limit=10&original_language=en" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Creating RSS Feed

```bash
curl -X POST http://localhost:8000/api/v1/users/me/rss-feeds/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -d '{
    "name": "Tech News",
    "url": "https://tech.example.com/rss",
    "category_id": "category-uuid"
  }'
```

## SDKs and Client Libraries

### Python Client

```python
import requests

class FireFeedClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
    
    def register(self, email, password, language="en"):
        response = self.session.post(f"{self.base_url}/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "language": language
        })
        return response.json()
    
    def login(self, email, password):
        response = self.session.post(f"{self.base_url}/api/v1/auth/login", data={
            "username": email,
            "password": password
        })
        data = response.json()
        self.session.headers.update({
            "Authorization": f"Bearer {data['access_token']}"
        })
        return data
    
    def get_rss_items(self, **params):
        response = self.session.get(f"{self.base_url}/api/v1/rss-items/", params=params)
        return response.json()
```

## Support

For API support and questions:

- **Documentation**: [https://docs.firefeed.net](https://docs.firefeed.net)
- **Support Email**: [mail@firefeed.net](mailto:mail@firefeed.net)
- **GitHub Issues**: [https://github.com/firefeed-net/firefeed-api/issues](https://github.com/firefeed-net/firefeed-api/issues)

## Changelog

### v1.0.0 (2023-01-01)
- Initial release
- Complete backward compatibility with monolithic version
- Public and internal API endpoints
- OAuth2 authentication
- Rate limiting and error handling