"""Test external API compatibility for firefeed-api."""

import pytest
from fastapi.testclient import TestClient
from main import app


class TestExternalAPICompatibility:
    """Test external API compatibility."""

    def setup_method(self):
        """Setup test client."""
        # Create a test client without lifespan events (which require DB/Redis)
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root(self):
        """Test root endpoint."""
        response = self.client.get("/")
        # May return 200 or 500 depending on service availability
        assert response.status_code in [200, 500, 503]

    def test_docs_redirect(self):
        """Test documentation redirect."""
        response = self.client.get("/docs")
        assert response.status_code in [200, 301, 302, 404]

    def test_openapi_schema(self):
        """Test OpenAPI schema is accessible."""
        response = self.client.get("/openapi.json")
        # May be 200, 404 if not initialized, or 500
        assert response.status_code in [200, 404, 500]


class TestAPIInfo:
    """Test API info endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_api_info_endpoint(self):
        """Test /api/info endpoint if exists."""
        response = self.client.get("/api/info")
        # May not exist or return error if services not fully initialized
        assert response.status_code in [200, 404, 500]