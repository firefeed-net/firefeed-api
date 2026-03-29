# FireFeed API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-6+-red.svg)](https://redis.io/)

Microservices-based RSS feed management API with full backward compatibility support.

> **Note**: This service is part of the [FireFeed platform](https://github.com/firefeed-net/firefeed) microservices architecture. It can be run standalone or as part of the complete FireFeed ecosystem with [RSS Parser](https://github.com/firefeed-net/firefeed-rss-parser) and [Telegram Bot](https://github.com/firefeed-net/firefeed-telegram-bot).

## 🚀 Features

### Core Functionality
- **RSS Feed Management** - Complete CRUD operations for RSS feeds and items
- **User Management** - User registration, authentication, and profile management
- **Category Organization** - Organize content by categories and sources
- **Multi-language Support** - Built-in translation service with caching
- **Media Processing** - Image and video processing with caching
- **Email Service** - Transactional email support

### API Features
- **Backward Compatibility** - Full compatibility with monolithic version
- **Public API** - RESTful API for external consumers
- **Internal API** - Microservice communication endpoints
- **Authentication** - OAuth2 Password Flow with JWT tokens
- **Rate Limiting** - API protection and rate limiting
- **Health Checks** - Comprehensive health monitoring
- **Metrics** - Prometheus-compatible metrics collection

### Technical Features
- **Microservices Architecture** - Scalable and maintainable design
- **Async/await** - High performance with async operations
- **Dependency Injection** - Clean architecture with DI container
- **Database Migration** - Automated schema management
- **Caching** - Redis-based caching for performance
- **Background Tasks** - Asynchronous task processing
- **Error Handling** - Comprehensive error handling and logging

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Architecture](#architecture)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## 📦 Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+

### Quick Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/firefeed-net/firefeed-api.git
   cd firefeed-api
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies:**
   ```bash
   ./firefeed-api/.kilocode_wrapper.sh setup-dev
   ```

4. **Run migrations:**
   ```bash
   ./firefeed-api/.kilocode_wrapper.sh migrate
   ```

5. **Start the server:**
   ```bash
   ./firefeed-api/.kilocode_wrapper.sh start-dev
   ```

### Docker Setup

#### Standalone (Development)

```bash
# Build and start services
docker-compose up -d
```

#### As Part of FireFeed Platform

```bash
# From the root firefeed directory
cd ..
docker-compose up -d

# The API will be available at http://localhost:8001
```

## 🚀 Quick Start

### 1. User Registration

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "language": "en"
  }'
```

### 2. User Authentication

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "securepassword123"
  }'
```

### 3. Get RSS Items

```bash
curl -X GET "http://localhost:8000/api/v1/rss-items/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Add RSS Feed

```bash
curl -X POST "http://localhost:8000/api/v1/rss/feeds/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": 1,
    "category_id": 1,
    "title": "Tech News",
    "description": "Latest technology news",
    "url": "https://example.com/rss.xml"
  }'
```

## 📚 API Documentation

### Public API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/verify` - Email verification
- `POST /api/v1/auth/resend-verification` - Resend verification email
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/reset-password/request` - Request password reset
- `POST /api/v1/auth/reset-password/confirm` - Confirm password reset

#### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update user profile
- `DELETE /api/v1/users/me` - Delete user account
- `GET /api/v1/users/me/rss-items/` - Get user's RSS items
- `GET /api/v1/users/me/categories/` - Get user's categories
- `GET /api/v1/users/me/rss-feeds/` - Get user's RSS feeds
- `POST /api/v1/users/me/rss-feeds/` - Create RSS feed
- `GET /api/v1/users/me/api-keys/` - Get user's API keys
- `POST /api/v1/users/me/api-keys/` - Create API key
- `GET /api/v1/users/me/telegram/status` - Get Telegram status
- `POST /api/v1/users/me/telegram/generate-link` - Generate Telegram link

#### RSS
- `GET /api/v1/rss-items/` - Get RSS items
- `GET /api/v1/rss-items/{rss_item_id}` - Get specific RSS item
- `GET /api/v1/categories/` - Get categories
- `GET /api/v1/sources/` - Get sources
- `GET /api/v1/languages/` - Get supported languages
- `GET /api/v1/health` - Health check
- `GET /api/v1/rss/feeds/` - Get RSS feeds
- `GET /api/v1/rss/feeds/{feed_id}` - Get specific RSS feed
- `POST /api/v1/translation/translate` - Translate text

### Internal API Endpoints

Internal API endpoints are used for microservice communication and are not intended for external use. These endpoints require service-to-service authentication via API keys.

**Internal endpoints include:**
- User management for Telegram Bot
- RSS feed management for RSS Parser
- Translation services
- Media processing
- Category and source management

## 🏗️ Architecture

### Microservices Design

The FireFeed API follows a microservices architecture pattern with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Public API    │    │  Internal API   │    │   Background    │
│                 │    │                 │    │     Tasks       │
│ • Authentication│    │ • User Service  │    │ • Maintenance   │
│ • User Mgmt     │◄──►│ • RSS Service   │◄──►│ • Translation   │
│ • RSS Service   │    │ • Category Svc  │    │ • Media Proc.   │
│ • Translation   │    │ • Source Service│    │ • Email Svc     │
│ • Media         │    │ • Translation   │    │ • Text Analysis │
│ • Email         │    │ • Media         │    │ • DB Mgmt       │
└─────────────────┘    │ • Email         │    └─────────────────┘
                       │ • Maintenance   │
                       │ • DB Service    │
                       │ • Text Analysis │
                       │ • API Key Svc   │
                       │ • Telegram Svc  │
                       └─────────────────┘
```

### Integration with Other Services

The API service integrates with:
- **[FireFeed RSS Parser](https://github.com/firefeed-net/firefeed-rss-parser)** - Receives parsed RSS items
- **[FireFeed Telegram Bot](https://github.com/firefeed-net/firefeed-telegram-bot)** - Provides user data and RSS items for notifications

### Database Schema

The database uses PostgreSQL with the following key tables:

- **users** - User accounts and authentication
- **rss_data** - RSS items
- **categories** - Content categories
- **sources** - RSS feed sources
- **rss_feeds** - RSS feed subscriptions
- **api_keys** - API key management
- **translations** - Translation cache
- **media_files** - Media file storage

### Caching Strategy

Redis is used for multiple caching purposes:

- **Session storage** - User sessions and authentication
- **Translation cache** - Translated content caching
- **Media cache** - Processed media files
- **Rate limiting** - API rate limit storage
- **Temporary data** - Short-lived data storage

## 🛠️ Development

### Project Structure

```
firefeed-api/
├── firefeed-api/               # Main application package
│   ├── routers/               # API endpoint routers
│   ├── services/              # Business logic services
│   ├── models/                # Data models
│   ├── middleware/            # FastAPI middleware
│   ├── database/              # Database utilities
│   ├── config/                # Configuration
│   ├── cache/                 # Caching utilities
│   ├── background_tasks/      # Background task management
├── tests/                     # Test suite
├── scripts/                   # Development scripts
├── .github/                   # GitHub Actions workflows
└── docker/                    # Docker configuration
```

### Development Commands

```bash
# Setup development environment
./firefeed-api/.kilocode_wrapper.sh setup-dev

# Run tests
./firefeed-api/.kilocode_wrapper.sh run-tests

# Run linting
./firefeed-api/.kilocode_wrapper.sh run-lint

# Start development server
./firefeed-api/.kilocode_wrapper.sh start-dev

# Run database migrations
./firefeed-api/.kilocode_wrapper.sh migrate

# Seed database
./firefeed-api/.kilocode_wrapper.sh seed

# View logs
./firefeed-api/.kilocode_wrapper.sh logs

# Clean up
./firefeed-api/.kilocode_wrapper.sh cleanup
```

### Code Style

The project uses `ruff` for linting and formatting:

```bash
# Check code style
ruff check .

# Format code
ruff format .

# Type checking
mypy firefeed-api/
```

## 🧪 Testing

### Test Structure

```bash
tests/
├── test_backward_compatibility.py  # Backward compatibility tests
├── test_performance.py             # Performance tests
└── test_*.py                       # Other test files
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=firefeed-api --cov-report=html

# Run specific test file
pytest tests/test_backward_compatibility.py

# Run with parallel execution
pytest -n auto
```

### Test Coverage

The project maintains high test coverage with:

- **Unit tests** for all services and utilities
- **Integration tests** for API endpoints
- **Backward compatibility tests** for API contracts
- **Performance tests** for critical paths
- **Database migration tests** for schema changes

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Contributing Steps

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

### Development Guidelines

- Follow the existing code style
- Write clear, descriptive commit messages
- Add appropriate tests for new functionality
- Update documentation when needed
- Ensure backward compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation

- [API Documentation](https://docs.firefeed.net)
- [Migration Guide](MIGRATION_GUIDE.md)
- [FireFeed Platform Documentation](https://github.com/firefeed-net/firefeed)

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/firefeed-net/firefeed-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/firefeed-net/firefeed-api/discussions)
- **Documentation**: [docs.firefeed.net](https://docs.firefeed.net)
- **Email**: mail@firefeed.net

### Reporting Issues

When reporting issues, please include:

- Clear description of the problem
- Steps to reproduce
- Expected behavior vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and stack traces

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit and ORM
- [Redis](https://redis.io/) - In-memory data structure store
- [PostgreSQL](https://www.postgresql.org/) - Advanced open source database

## 📊 Metrics

- **Lines of Code**: ~10,000+
- **Test Coverage**: >90%
- **API Endpoints**: 50+
- **Supported Languages**: 10+
- **Database Tables**: 20+
- **Cache Types**: 5+

---

**FireFeed API** - Powering the future of RSS feed management with modern microservices architecture and full backward compatibility.
