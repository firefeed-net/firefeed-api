# Scripts Directory

This directory contains utility scripts for the FireFeed API microservice.

## Scripts

### reorganize_tests.py

Automatically reorganizes the test structure to match the main project structure.

**Usage:**
```bash
# Dry run (show what would be done)
python scripts/reorganize_tests.py --dry-run

# Perform reorganization
python scripts/reorganize_tests.py

# Create backup before reorganization
python scripts/reorganize_tests.py --backup

# Rollback from backup
python scripts/reorganize_tests.py --rollback /path/to/backup
```

**Features:**
- Creates directory structure matching the main project
- Moves test files to appropriate directories
- Updates import statements automatically
- Creates backup before making changes
- Provides detailed summary of changes

**Target Structure:**
```
tests/
├── repositories/
├── utils/
├── exceptions/
├── services/
│   ├── translation/
│   ├── text_analysis/
│   ├── user/
│   ├── email/
│   └── maintenance/
├── apps/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   ├── test_auth.py
│   │   ├── test_models.py
│   │   ├── test_middleware.py
│   │   ├── test_websocket.py
│   │   └── routers/
│   │       ├── test_api_keys.py
│   │       ├── test_categories.py
│   │       ├── test_rss_feeds.py
│   │       ├── test_rss_items_router.py
│   │       ├── test_rss_router.py
│   │       ├── test_telegram.py
│   │       └── test_users.py
│   └── rss_parser/
│       ├── __init__.py
│       ├── test_rss_fetcher.py
│       ├── test_rss_manager.py
│       ├── test_rss_storage.py
│       ├── test_rss_validator.py
│       └── services/
│           └── test_services.py
└── integration/
    ├── test_di_integration.py
    ├── test_database.py
    ├── test_database_pool_adapter.py
    ├── test_app.py
    └── test_main.py
```

## Development

Scripts are written in Python 3.11+ and follow the same coding standards as the main project.