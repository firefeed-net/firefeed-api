"""Test external API compatibility for firefeed-api."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from firefeed_api.main import app
from firefeed_core.api_client.client import APIClient
from firefeed_core.models.user_models import UserCreate, UserResponse


class TestExternalAPICompatibility:
    """Test external API compatibility."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    @patch('firefeed_api.main.di_container')
    def test_health_check(self, mock_di_container):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @patch('firefeed_api.main.di_container')
    def test_api_info(self, mock_di_container):
        """Test API info endpoint."""
        response = self.client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "description" in data
        assert "endpoints" in data

    @patch('firefeed_api.main.di_container')
    def test_user_registration(self, mock_di_container):
        """Test user registration endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.create_user.return_value = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        mock_di_container.get_service.return_value = mock_user_service

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword"
        }

        response = self.client.post("/api/users/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    @patch('firefeed_api.main.di_container')
    def test_user_login(self, mock_di_container):
        """Test user login endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.authenticate_user.return_value = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        mock_di_container.get_service.return_value = mock_user_service

        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }

        response = self.client.post("/api/users/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data

    @patch('firefeed_api.main.di_container')
    def test_user_profile(self, mock_di_container):
        """Test user profile endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id.return_value = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        mock_di_container.get_service.return_value = mock_user_service

        # Mock token validation
        with patch('firefeed_api.main.validate_token') as mock_validate:
            mock_validate.return_value = {"user_id": 1}
            
            response = self.client.get("/api/users/profile")
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "testuser"
            assert data["email"] == "test@example.com"

    @patch('firefeed_api.main.di_container')
    def test_user_update(self, mock_di_container):
        """Test user update endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.update_user.return_value = UserResponse(
            id=1,
            username="updateduser",
            email="updated@example.com",
            is_active=True
        )
        mock_di_container.get_service.return_value = mock_user_service

        # Mock token validation
        with patch('firefeed_api.main.validate_token') as mock_validate:
            mock_validate.return_value = {"user_id": 1}
            
            update_data = {
                "username": "updateduser",
                "email": "updated@example.com"
            }

            response = self.client.put("/api/users/profile", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "updateduser"
            assert data["email"] == "updated@example.com"

    @patch('firefeed_api.main.di_container')
    def test_user_deletion(self, mock_di_container):
        """Test user deletion endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.delete_user.return_value = True
        mock_di_container.get_service.return_value = mock_user_service

        # Mock token validation
        with patch('firefeed_api.main.validate_token') as mock_validate:
            mock_validate.return_value = {"user_id": 1}
            
            response = self.client.delete("/api/users/profile")
            assert response.status_code == 200
            assert response.json() == {"message": "User deleted successfully"}

    @patch('firefeed_api.main.di_container')
    def test_api_key_generation(self, mock_di_container):
        """Test API key generation endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.generate_api_key.return_value = "test-api-key-123"
        mock_di_container.get_service.return_value = mock_user_service

        # Mock token validation
        with patch('firefeed_api.main.validate_token') as mock_validate:
            mock_validate.return_value = {"user_id": 1}
            
            response = self.client.post("/api/users/api-key")
            assert response.status_code == 200
            data = response.json()
            assert data["api_key"] == "test-api-key-123"

    @patch('firefeed_api.main.di_container')
    def test_api_key_revocation(self, mock_di_container):
        """Test API key revocation endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.revoke_api_key.return_value = True
        mock_di_container.get_service.return_value = mock_user_service

        # Mock token validation
        with patch('firefeed_api.main.validate_token') as mock_validate:
            mock_validate.return_value = {"user_id": 1}
            
            response = self.client.delete("/api/users/api-key")
            assert response.status_code == 200
            assert response.json() == {"message": "API key revoked successfully"}

    @patch('firefeed_api.main.di_container')
    def test_error_handling(self, mock_di_container):
        """Test error handling."""
        # Mock the user service to raise an exception
        mock_user_service = MagicMock()
        mock_user_service.create_user.side_effect = Exception("Test error")
        mock_di_container.get_service.return_value = mock_user_service

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword"
        }

        response = self.client.post("/api/users/register", json=user_data)
        assert response.status_code == 500
        data = response.json()
        assert "error" in data