"""Tests for health and root endpoints."""

import pytest


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns index or API info."""
        response = client.get("/")
        assert response.status_code == 200
