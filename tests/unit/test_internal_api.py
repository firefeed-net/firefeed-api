"""Test internal API for firefeed-api."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from firefeed_api.internal_main import app
from firefeed_core.models.user_models import UserCreate, UserResponse


class TestInternalAPI:
    """Test internal API endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_health_check(self, mock_di_container):
        """Test internal health check endpoint."""
        response = self.client.get("/internal/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_creation(self, mock_di_container):
        """Test internal user creation endpoint."""
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

        response = self.client.post("/internal/users", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_retrieval(self, mock_di_container):
        """Test internal user retrieval endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.get_user_by_id.return_value = UserResponse(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        mock_di_container.get_service.return_value = mock_user_service

        response = self.client.get("/internal/users/1")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_update(self, mock_di_container):
        """Test internal user update endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.update_user.return_value = UserResponse(
            id=1,
            username="updateduser",
            email="updated@example.com",
            is_active=True
        )
        mock_di_container.get_service.return_value = mock_user_service

        update_data = {
            "username": "updateduser",
            "email": "updated@example.com"
        }

        response = self.client.put("/internal/users/1", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == "updated@example.com"

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_deletion(self, mock_di_container):
        """Test internal user deletion endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.delete_user.return_value = True
        mock_di_container.get_service.return_value = mock_user_service

        response = self.client.delete("/internal/users/1")
        assert response.status_code == 200
        assert response.json() == {"message": "User deleted successfully"}

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_list(self, mock_di_container):
        """Test internal user list endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.get_all_users.return_value = [
            UserResponse(id=1, username="user1", email="user1@example.com", is_active=True),
            UserResponse(id=2, username="user2", email="user2@example.com", is_active=True)
        ]
        mock_di_container.get_service.return_value = mock_user_service

        response = self.client.get("/internal/users")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["username"] == "user1"
        assert data[1]["username"] == "user2"

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_search(self, mock_di_container):
        """Test internal user search endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.search_users.return_value = [
            UserResponse(id=1, username="testuser", email="test@example.com", is_active=True)
        ]
        mock_di_container.get_service.return_value = mock_user_service

        response = self.client.get("/internal/users/search?username=testuser")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "testuser"

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_count(self, mock_di_container):
        """Test internal user count endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.get_user_count.return_value = 10
        mock_di_container.get_service.return_value = mock_user_service

        response = self.client.get("/internal/users/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 10

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_bulk_creation(self, mock_di_container):
        """Test internal user bulk creation endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.create_users.return_value = [
            UserResponse(id=1, username="user1", email="user1@example.com", is_active=True),
            UserResponse(id=2, username="user2", email="user2@example.com", is_active=True)
        ]
        mock_di_container.get_service.return_value = mock_user_service

        users_data = [
            {"username": "user1", "email": "user1@example.com", "password": "password1"},
            {"username": "user2", "email": "user2@example.com", "password": "password2"}
        ]

        response = self.client.post("/internal/users/bulk", json=users_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["username"] == "user1"
        assert data[1]["username"] == "user2"

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_user_bulk_deletion(self, mock_di_container):
        """Test internal user bulk deletion endpoint."""
        # Mock the user service
        mock_user_service = MagicMock()
        mock_user_service.delete_users.return_value = 2
        mock_di_container.get_service.return_value = mock_user_service

        user_ids = [1, 2]

        response = self.client.delete("/internal/users/bulk", json=user_ids)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 2

    @patch('firefeed_api.internal_main.di_container')
    def test_internal_error_handling(self, mock_di_container):
        """Test internal error handling."""
        # Mock the user service to raise an exception
        mock_user_service = MagicMock()
        mock_user_service.create_user.side_effect = Exception("Test error")
        mock_di_container.get_service.return_value = mock_user_service

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword"
        }

        response = self.client.post("/internal/users", json=user_data)
        assert response.status_code == 500
        data = response.json()
        assert "error" in data