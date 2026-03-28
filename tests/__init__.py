"""
Tests package for FireFeed API

This package contains all the tests for the application.
"""

# Import test modules
from .test_backward_compatibility import *
from .test_performance import *

# Export commonly used test components
__all__ = [
    # Backward compatibility tests
    'test_api_compatibility',
    'test_model_compatibility',
    'test_database_compatibility',
    'test_authentication_compatibility',
    'test_error_handling_compatibility',
    
    # Performance tests
    'test_api_performance',
    'test_database_performance',
    'test_cache_performance',
    'test_translation_performance',
    'test_media_performance'
]