"""
Database package for FireFeed API

This package contains database utilities and models for the application.
"""

# Import database modules
from .models import Base
from .migrations import (
    migration_manager,
    run_migrations,
    create_tables,
    drop_tables,
    check_health
)
from .init import (
    database_initializer,
    initialize_database,
    check_database_health,
    get_database_migration_status,
    create_database_migration,
    setup_database,
    seed_database,
    setup_and_seed_database
)

# Export commonly used database components
__all__ = [
    'Base',
    'migration_manager',
    'run_migrations',
    'create_tables',
    'drop_tables',
    'check_health',
    'database_initializer',
    'initialize_database',
    'check_database_health',
    'get_database_migration_status',
    'create_database_migration',
    'setup_database',
    'seed_database',
    'setup_and_seed_database'
]