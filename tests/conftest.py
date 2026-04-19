"""Pytest configuration for firefeed-api tests."""
import pytest
import sys
import warnings
from pathlib import Path

# Add /app to the path so tests can import modules correctly
app_path = Path("/app")
if str(app_path) not in sys.path:
    sys.path.insert(0, str(app_path))


@pytest.fixture(autouse=True)
def suppress_gzip_warnings():
    """Suppress GZip warnings during test cleanup."""
    # Temporarily suppress warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        warnings.filterwarnings("ignore", message=".*I/O operation on closed file.*")
        yield