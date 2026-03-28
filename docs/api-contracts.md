# FireFeed API Contracts

## Overview

This document describes the API contracts for the FireFeed microservices architecture, maintaining full backward compatibility with the original monolithic version.

## API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/register
Register a new user account.

**Request Body:**
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
  "id": 123,
  "email": "user@example.com",
  "language": "en",
  "is_active": false,
  "is_verified": false,
  "is_deleted": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": null
}
```

**Error Responses:**
- 400 Bad Request: Email already registered or invalid data
- 422 Unprocessable Entity: Validation errors

#### POST /api/v1/auth/verify
Verify user email address.

**Request Body:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "User successfully verified"
}
```

**Error Responses:**
- 400 Bad Request: Invalid verification code or email
- 422 Unprocessable Entity: Validation errors

#### POST /api/v1/auth/login
Authenticate user and get JWT token.

**Request Body (Form Data):**
```
username=user@example.com
password=securepassword123
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses:**
- 401 Unauthorized: Invalid credentials or account not verified
- 422 Unprocessable Entity: Validation errors

### User Management Endpoints

#### GET /api/v1/users/me
Get current user profile.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "language": "en",
  "is_active": true,
  "is_verified": true,
  "is_deleted": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-02T10:30:00Z"
}
```

**Error Responses:**
- 401 Unauthorized: Authentication required
- 422 Unprocessable Entity: Validation errors

#### PUT /api/v1/users/me
Update user profile.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "language": "ru"
}
```

**Response (200 OK):**
```json
{
  "id": 123,
  "email": "newemail@example.com",
  "language": "ru",
  "is_active": true,
  "is_verified": true,
  "is_deleted": false,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-02T10:30:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid email format or email already taken
- 401 Unauthorized: Authentication required
- 422 Unprocessable Entity: Validation errors

### RSS Items Endpoints

#### GET /api/v1/rss-items/
Get paginated list of RSS items.

**Query Parameters:**
- `original_language` (optional): Filter by language (en, ru, de, fr)
- `category_id` (optional): Filter by category ID (comma-separated or multiple params)
- `source_id` (optional): Filter by source ID (comma-separated or multiple params)
- `telegram_published` (optional): Filter by Telegram publication status
- `from_date` (optional): Filter by timestamp (Unix timestamp)
- `search_phrase` (optional): Full-text search
- `limit` (optional): Number of items per page (1-100, default: 50)
- `offset` (optional): Number of items to skip (default: 0)

**Response (200 OK):**
```json
{
  "count": 100,
  "results": [
    {
      "news_id": "abc123-def456",
      "original_title": "Breaking News Headline",
      "original_content": "Full article content here...",
      "original_language": "en",
      "image_url": "https://firefeed.net/data/images/2024/01/01/abc123.jpg",
      "category": "Technology",
      "source": "Tech News",
      "source_alias": "technews",
      "source_url": "https://technews.com/article123",
      "created_at": "2024-01-01T12:00:00Z",
      "translations": {
        "ru": {
          "title": "Заголовок новости",
          "content": "Полный текст статьи..."
        },
        "de": {
          "title": "Nachrichtenüberschrift",
          "content": "Vollständiger Artikeltext..."
        }
      }
    }
  ]
}
```

**Error Responses:**
- 422 Unprocessable Entity: Validation errors

#### GET /api/v1/rss-items/{news_id}
Get specific RSS item by ID.

**Path Parameters:**
- `news_id`: Unique identifier of the RSS item

**Response (200 OK):**
```json
{
  "news_id": "abc123-def456",
  "original_title": "Breaking News Headline",
  "original_content": "Full article content here...",
  "original_language": "en",
  "image_url": "https://firefeed.net/data/images/2024/01/01/abc123.jpg",
  "category": "Technology",
  "source": "Tech News",
  "source_alias": "technews",
  "source_url": "https://technews.com/article123",
  "created_at": "2024-01-01T12:00:00Z",
  "translations": {
    "ru": {
      "title": "Заголовок новости",
      "content": "Полный текст статьи..."
    }
  }
}
```

**Error Responses:**
- 404 Not Found: RSS item not found
- 422 Unprocessable Entity: Validation errors

### Categories Endpoints

#### GET /api/v1/categories/
Get list of available categories.

**Query Parameters:**
- `limit` (optional): Number of categories per page (1-1000, default: 100)
- `offset` (optional): Number of categories to skip (default: 0)
- `source_ids` (optional): Filter by source IDs (comma-separated or multiple params)

**Response (200 OK):**
```json
{
  "count": 8,
  "results": [
    {
      "id": 1,
      "name": "Technology",
      "display_name": "Technology",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": null
    },
    {
      "id": 2,
      "name": "Politics",
      "display_name": "Politics",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": null
    }
  ]
}
```

**Error Responses:**
- 422 Unprocessable Entity: Validation errors

### Sources Endpoints

#### GET /api/v1/sources/
Get list of available news sources.

**Query Parameters:**
- `limit` (optional): Number of sources per page (1-1000, default: 100)
- `offset` (optional): Number of sources to skip (default: 0)
- `category_id` (optional): Filter by category IDs (comma-separated or multiple params)

**Response (200 OK):**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "name": "BBC News",
      "description": "British Broadcasting Corporation",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": null,
      "alias": "bbc",
      "logo": "bbc-logo.png",
      "site_url": "https://bbc.com"
    }
  ]
}
```

**Error Responses:**
- 422 Unprocessable Entity: Validation errors

### Languages Endpoints

#### GET /api/v1/languages/
Get supported languages.

**Response (200 OK):**
```json
{
  "results": [
    {"language": "en"},
    {"language": "ru"},
    {"language": "de"},
    {"language": "fr"}
  ]
}
```

**Error Responses:**
- 422 Unprocessable Entity: Validation errors

### Health Check Endpoint

#### GET /api/v1/health
Check system health status.

**Response (200 OK):**
```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "db_pool": {
    "total_connections": 20,
    "free_connections": 15
  }
}
```

**Error Responses:**
- 500 Internal Server Error: System unhealthy

## Error Response Format

### Standard Error Format
```json
{
  "detail": "Error description message"
}
```

### Validation Error Format
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Authentication

### JWT Token Format
All authenticated endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Structure
```json
{
  "sub": "123",           // User ID
  "exp": 1704067200,      // Expiration time
  "iat": 1704065400,      // Issued at
  "iss": "firefeed-api"   // Issuer
}
```

### Token Expiration
- Default expiration: 30 minutes
- Refresh mechanism: Not implemented (client should re-authenticate)

## Rate Limiting

### Limits by Endpoint
- Authentication endpoints: 5 requests per minute
- User endpoints: 300 requests per minute
- RSS endpoints: 1000 requests per minute
- Health check: 300 requests per minute

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1704067200
```

### Rate Limit Error
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests",
  "retry_after": 60
}
```

## Pagination

### Offset-Based Pagination
```json
{
  "count": 1000,
  "results": [...]
}
```

### Parameters
- `limit`: Number of items per page (1-1000)
- `offset`: Number of items to skip

### Example
```
GET /api/v1/rss-items/?limit=50&offset=100
```

## Filtering

### Language Filtering
```
GET /api/v1/rss-items/?original_language=en
```

### Category Filtering
```
GET /api/v1/rss-items/?category_id=1,2,3
GET /api/v1/rss-items/?category_id=1&category_id=2&category_id=3
```

### Date Filtering
```
GET /api/v1/rss-items/?from_date=1704067200
```

### Search Filtering
```
GET /api/v1/rss-items/?search_phrase=breaking+news
```

## Data Models

### RSS Item Model
```typescript
interface RSSItem {
  news_id: string;
  original_title: string;
  original_content: string;
  original_language: string;
  image_url?: string;
  category?: string;
  source?: string;
  source_alias?: string;
  source_url?: string;
  created_at?: string;
  translations?: {
    [language: string]: {
      title?: string;
      content?: string;
    };
  };
}
```

### User Model
```typescript
interface User {
  id: number;
  email: string;
  language: string;
  is_active: boolean;
  is_verified: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at?: string;
}
```

### Category Model
```typescript
interface Category {
  id: number;
  name: string;
  display_name?: string;
  created_at: string;
  updated_at?: string;
}
```

### Source Model
```typescript
interface Source {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  alias?: string;
  logo?: string;
  site_url?: string;
}
```

## Internal API Endpoints

### GET /api/v1/internal/health
Internal health check for service monitoring.

### GET /api/v1/internal/users/{id}
Get user by ID (internal use).

### GET /api/v1/internal/rss/items
Get RSS items (internal use).

### POST /api/v1/internal/rss/items
Create RSS item (internal use).

### Authentication for Internal Endpoints
Internal endpoints require service tokens:

```
Authorization: Bearer internal-service-token
X-Service-ID: firefeed-rss-parser
```

## Versioning

### Current Version
- API Version: v1
- Base URL: `/api/v1/`

### Future Versioning
Future versions will be implemented as:
- `/api/v2/` - New major version
- `/api/v1/` - Legacy version (backward compatible)

## Compatibility

### Backward Compatibility
All endpoints maintain full backward compatibility with the monolithic version:
- Same URL paths
- Same request/response formats
- Same authentication mechanisms
- Same error handling

### Breaking Changes
No breaking changes for public API consumers. Internal API changes are isolated to microservice communication.