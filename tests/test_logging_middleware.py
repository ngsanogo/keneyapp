"""
Tests for the structured logging middleware with correlation IDs.
"""

import uuid as uuid_module

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_correlation_id_added_to_response():
    """Test that correlation ID is added to response headers."""

    response = client.get("/")

    assert "X-Correlation-ID" in response.headers
    correlation_id = response.headers["X-Correlation-ID"]

    # Should be a valid UUID format
    try:
        uuid_module.UUID(correlation_id)
    except ValueError:
        pytest.fail(f"Invalid UUID format: {correlation_id}")


def test_custom_correlation_id_preserved():
    """Test that custom correlation ID from request is preserved."""
    custom_id = "test-correlation-id-12345"

    response = client.get("/", headers={"X-Correlation-ID": custom_id})

    assert response.headers["X-Correlation-ID"] == custom_id


def test_correlation_id_unique_per_request():
    """Test that each request gets a unique correlation ID."""
    response1 = client.get("/")
    response2 = client.get("/")

    id1 = response1.headers["X-Correlation-ID"]
    id2 = response2.headers["X-Correlation-ID"]

    assert id1 != id2


def test_correlation_id_in_health_endpoint():
    """Test that correlation ID is added to health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_correlation_id_persists_on_error():
    """Test that correlation ID is added even when request fails."""
    # Try to access authenticated endpoint without token
    response = client.get("/api/v1/patients")

    # Should return 401 but still have correlation ID
    assert response.status_code == 401
    assert "X-Correlation-ID" in response.headers


def test_multiple_requests_with_same_correlation_id():
    """Test that the same correlation ID can be used across requests."""
    custom_id = "shared-correlation-id"

    response1 = client.get("/health", headers={"X-Correlation-ID": custom_id})
    response2 = client.get("/", headers={"X-Correlation-ID": custom_id})

    assert response1.headers["X-Correlation-ID"] == custom_id
    assert response2.headers["X-Correlation-ID"] == custom_id
