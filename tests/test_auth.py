"""Tests for authentication endpoints."""

import pytest


class TestAuthentication:
    """Test authentication functionality."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/auth/token",
            data={"username": "testadmin", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post(
            "/api/auth/token",
            data={"username": "testadmin", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_invalid_username(self, client):
        """Test login with non-existent username."""
        response = client.post(
            "/api/auth/token",
            data={"username": "nonexistent", "password": "testpass123"}
        )
        assert response.status_code == 401
    
    def test_get_me_authenticated(self, client, auth_headers, test_user):
        """Test getting current user info when authenticated."""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testadmin"
    
    def test_get_me_unauthenticated(self, client):
        """Test getting current user info without authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_get_me_invalid_token(self, client):
        """Test getting current user info with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401
    
    def test_register_new_user(self, client, auth_headers, test_user):
        """Test registering a new user (admin only)."""
        response = client.post(
            "/api/auth/register",
            headers=auth_headers,
            json={"username": "newuser", "password": "newpass123"}
        )
        assert response.status_code == 200
        assert "newuser" in response.json()["message"]
    
    def test_register_duplicate_user(self, client, auth_headers, test_user):
        """Test registering a user that already exists."""
        # First registration
        client.post(
            "/api/auth/register",
            headers=auth_headers,
            json={"username": "duplicate", "password": "pass123"}
        )
        
        # Second registration should fail
        response = client.post(
            "/api/auth/register",
            headers=auth_headers,
            json={"username": "duplicate", "password": "pass123"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_unauthenticated(self, client):
        """Test registering without authentication."""
        response = client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "newpass123"}
        )
        assert response.status_code == 401
