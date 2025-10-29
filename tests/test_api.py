"""
Basic API tests for KeneyApp.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "KeneyApp"
    assert response.json()["status"] == "running"


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_docs_accessible():
    """Test that API documentation is accessible."""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
