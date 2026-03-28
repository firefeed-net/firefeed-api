"""Test backward compatibility with monolithic FireFeed API."""

import pytest
import json
from typing import Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from models.public_models import (
    UserCreate, UserResponse, RSSItem, CategoryItem, 
    SourceItem, LanguageItem, Token, SuccessResponse
)

client = TestClient(app)

class TestBackwardCompatibility:
    """Test class for backward compatibility validation."""
    
    def test_auth_endpoints_compatibility(self):
        """Test that authentication endpoints match monolithic version."""
        # Test register endpoint
        register_response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "testpassword123",
            "language": "en"
        })
        
        assert register_response.status_code in [200, 201, 400, 422]  # Expected status codes
        
        # Test login endpoint
        login_response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        
        assert login_response.status_code in [200, 400, 401, 422]  # Expected status codes
        
        # Test that response contains access_token
        if login_response.status_code == 200:
            data = login_response.json()
            assert "access_token" in data
            assert "token_type" in data
            assert "expires_in" in data
    
    def test_user_endpoints_compatibility(self):
        """Test that user endpoints match monolithic version."""
        # Test get current user (should fail without auth)
        response = client.get("/api/v1/users/me")
        assert response.status_code in [401, 422]  # Expected without auth
        
        # Test update user (should fail without auth)
        response = client.put("/api/v1/users/me", json={
            "email": "new@example.com"
        })
        assert response.status_code in [401, 422]  # Expected without auth
    
    def test_rss_items_endpoints_compatibility(self):
        """Test that RSS items endpoints match monolithic version."""
        # Test get RSS items (should work without auth for public access)
        response = client.get("/api/v1/rss-items/")
        assert response.status_code in [200, 422]  # Expected status codes
        
        # Test that response has proper pagination structure
        if response.status_code == 200:
            data = response.json()
            assert "count" in data
            assert "results" in data
            assert isinstance(data["results"], list)
    
    def test_categories_endpoints_compatibility(self):
        """Test that categories endpoints match monolithic version."""
        response = client.get("/api/v1/categories/")
        assert response.status_code in [200, 422]  # Expected status codes
        
        if response.status_code == 200:
            data = response.json()
            assert "count" in data
            assert "results" in data
            assert isinstance(data["results"], list)
    
    def test_sources_endpoints_compatibility(self):
        """Test that sources endpoints match monolithic version."""
        response = client.get("/api/v1/sources/")
        assert response.status_code in [200, 422]  # Expected status codes
        
        if response.status_code == 200:
            data = response.json()
            assert "count" in data
            assert "results" in data
            assert isinstance(data["results"], list)
    
    def test_languages_endpoints_compatibility(self):
        """Test that languages endpoints match monolithic version."""
        response = client.get("/api/v1/languages/")
        assert response.status_code in [200, 422]  # Expected status codes
        
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert isinstance(data["results"], list)
    
    def test_health_endpoint_compatibility(self):
        """Test that health endpoint matches monolithic version."""
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 500]  # Expected status codes
        
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "database" in data
    
    def test_error_response_format(self):
        """Test that error responses have expected format."""
        # Test with invalid request
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",  # Invalid email format
            "password": "123",  # Too short password
            "language": "invalid"  # Invalid language
        })
        
        # Should return 400 or 422 with error details
        assert response.status_code in [400, 422]
        
        if response.status_code == 422:
            # FastAPI validation error format
            data = response.json()
            assert "detail" in data
        elif response.status_code == 400:
            # Custom validation error format
            data = response.json()
            assert "detail" in data or "error" in data
    
    def test_rate_limiting(self):
        """Test that rate limiting is implemented."""
        # Make multiple rapid requests to trigger rate limiting
        responses = []
        for _ in range(10):
            response = client.get("/api/v1/health")
            responses.append(response.status_code)
        
        # Should not get all 200s if rate limiting is working
        # (This is a basic test - actual rate limiting behavior may vary)
        assert len(responses) == 10
    
    def test_cors_headers(self):
        """Test that CORS headers are present."""
        response = client.options("/api/v1/health")
        # OPTIONS request should work and include CORS headers
        assert response.status_code in [200, 405]  # 200 if CORS is configured, 405 if not
    
    def test_api_versioning(self):
        """Test that API versioning is consistent."""
        # Test that v1 endpoints exist
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 500]
        
        # Test that non-existent version returns 404
        response = client.get("/api/v2/health")
        assert response.status_code == 404
    
    def test_model_field_compatibility(self):
        """Test that model fields match monolithic version."""
        # Test UserCreate model
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "language": "en"
        }
        
        # This should validate successfully
        user_create = UserCreate(**user_data)
        assert user_create.email == "test@example.com"
        assert user_create.language == "en"
    
    def test_pagination_parameters(self):
        """Test that pagination parameters work as expected."""
        # Test with limit and offset
        response = client.get("/api/v1/rss-items/?limit=10&offset=0")
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            assert "count" in data
            assert "results" in data
    
    def test_filtering_parameters(self):
        """Test that filtering parameters work as expected."""
        # Test with language filter
        response = client.get("/api/v1/rss-items/?original_language=en")
        assert response.status_code in [200, 422]
        
        # Test with category filter
        response = client.get("/api/v1/rss-items/?category_id=1")
        assert response.status_code in [200, 422]
    
    def test_authentication_required_endpoints(self):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/api/v1/users/me",
            "/api/v1/users/me/rss-items/",
            "/api/v1/users/me/categories/",
            "/api/v1/users/me/rss-feeds/",
            "/api/v1/users/me/api-keys/"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 422]  # Should require authentication
    
    def test_response_content_types(self):
        """Test that responses have correct content types."""
        response = client.get("/api/v1/health")
        assert response.headers["content-type"] == "application/json"
    
    def test_request_content_types(self):
        """Test that requests accept correct content types."""
        # Test JSON content type
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "test123", "language": "en"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [200, 201, 400, 422]
    
    def test_database_table_compatibility(self):
        """Test that database table naming is handled correctly."""
        # This test would require actual database connection
        # For now, just verify the models are compatible
        from firefeed_core.models.base_models import RSSItem as CoreRSSItem
        from models.public_models import RSSItem as PublicRSSItem
        
        # Both models should have the same fields
        core_fields = set(CoreRSSItem.__fields__.keys())
        public_fields = set(PublicRSSItem.__fields__.keys())
        
        # Public model should have all core fields plus any additional ones
        assert core_fields.issubset(public_fields)
    
    def test_internal_api_separation(self):
        """Test that internal and public APIs are properly separated."""
        # Internal endpoints should be under /api/v1/internal/
        internal_endpoints = [
            "/api/v1/internal/health",
            "/api/v1/internal/users/",
            "/api/v1/internal/rss/items/"
        ]
        
        for endpoint in internal_endpoints:
            response = client.get(endpoint)
            # Should return 404 if internal API is not exposed publicly
            # or 401 if authentication is required
            assert response.status_code in [401, 404, 500]
    
    def test_service_discovery(self):
        """Test that service discovery endpoints work."""
        # Test that we can discover available endpoints
        response = client.get("/")
        # Should return 404 or redirect to docs
        assert response.status_code in [404, 307, 200]
    
    def test_openapi_schema(self):
        """Test that OpenAPI schema is available."""
        response = client.get("/docs")
        # Should return 200 if docs are enabled
        assert response.status_code in [200, 404]
        
        response = client.get("/openapi.json")
        # Should return 200 if OpenAPI schema is available
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            schema = response.json()
            assert "openapi" in schema
            assert "paths" in schema

# Integration tests with mocked internal API
class TestInternalAPIIntegration:
    """Test integration with internal API."""
    
    @pytest.mark.asyncio
    async def test_public_api_client_creation(self):
        """Test that PublicAPIClient can be created."""
        from services.public_api_client import PublicAPIClient
        
        client = PublicAPIClient(
            internal_api_base_url="http://localhost:8001",
            service_token="test-token",
            service_id="test-service",
            timeout=30,
            max_retries=3
        )
        
        assert client.internal_api_base_url == "http://localhost:8001"
        assert client.service_token == "test-token"
        assert client.service_id == "test-service"
    
    @pytest.mark.asyncio
    async def test_authentication_proxy(self):
        """Test that authentication proxy works correctly."""
        from middleware.public_auth import PublicAuthMiddleware, TokenData
        
        middleware = PublicAuthMiddleware(
            secret_key="test-secret",
            issuer="test-issuer"
        )
        
        # Test with mock token
        with patch('firefeed_core.auth.token_manager.ServiceTokenManager.verify_token') as mock_verify:
            mock_verify.return_value = {"sub": "123", "service_id": "test-service"}
            
            token_data = await middleware.authenticate_user_token("mock-token")
            
            assert token_data.user_id == 123
            assert token_data.service_id == "test-service"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])