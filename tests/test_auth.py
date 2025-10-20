"""
Tests for authentication endpoints
"""
import pytest
from fastapi import status


class TestAuth:
    """Test authentication functionality"""
    
    def test_login_success(self, client, admin_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user information"""
        response = client.get("/api/users/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "admin"
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/users/me")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/users/me", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
