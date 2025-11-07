"""Tests for correlation ID middleware headers."""

# flake8: noqa: E402
import os

os.environ["TESTING"] = "true"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_correlation_id_in_response_headers():
    """Ensure correlation ID is injected in response headers."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "x-correlation-id" in resp.headers
    # Correlation ID should be a non-empty string
    assert len(resp.headers["x-correlation-id"]) > 0


def test_correlation_id_consistent_in_request_lifecycle():
    """Ensure the same correlation ID flows through request/response."""
    custom_id = "test-correlation-12345"
    resp = client.get("/health", headers={"x-correlation-id": custom_id})
    assert resp.status_code == 200
    # Should echo back the provided correlation ID
    assert resp.headers["x-correlation-id"] == custom_id
