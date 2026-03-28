#!/usr/bin/env python3
"""
Test script to verify firefeed_core import works correctly.

This script tests that the firefeed_core package can be imported
and that the editable installation is working properly.
"""

import sys
import os

def test_firefeed_core_import():
    """Test importing firefeed_core and its components."""
    try:
        # Test basic import
        print("Testing firefeed_core import...")
        import firefeed_core
        print(f"✓ Successfully imported firefeed_core from: {firefeed_core.__file__}")
        
        # Test importing specific modules
        print("\nTesting specific module imports...")
        
        # Test config import
        from firefeed_core.config import services_config
        print("✓ Successfully imported firefeed_core.config.services_config")
        
        # Test models import
        from firefeed_core.models import base_models
        print("✓ Successfully imported firefeed_core.models.base_models")
        
        # Test interfaces import
        from firefeed_core.interfaces import base_interfaces
        print("✓ Successfully imported firefeed_core.interfaces.base_interfaces")
        
        # Test exceptions import
        from firefeed_core.exceptions import base_exceptions
        print("✓ Successfully imported firefeed_core.exceptions.base_exceptions")
        
        # Test utils import
        from firefeed_core.utils import api
        print("✓ Successfully imported firefeed_core.utils.api")
        
        print("\n🎉 All imports successful! firefeed_core is properly installed in editable mode.")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print(f"Python path: {sys.path}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_package_location():
    """Test that the package is installed in editable mode."""
    try:
        import firefeed_core
        package_path = firefeed_core.__file__
        print(f"\nPackage location: {package_path}")
        
        # Check if it's pointing to the source directory (editable install)
        if "firefeed-core" in package_path:
            print("✓ Package appears to be installed in editable mode")
            return True
        else:
            print("⚠ Package may not be in editable mode")
            return False
            
    except Exception as e:
        print(f"❌ Error checking package location: {e}")
        return False

if __name__ == "__main__":
    print("FireFeed Core Import Test")
    print("=" * 40)
    
    success = test_firefeed_core_import()
    if success:
        test_package_location()
    
    sys.exit(0 if success else 1)