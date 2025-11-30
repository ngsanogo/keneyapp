import os
import pytest
from fastapi.testclient import TestClient

# Set testing flag to avoid external DB create_all during app startup
os.environ["TESTING"] = "true"

from app.main import app  # noqa: E402

client = TestClient(app)


def authenticate_headers():
    # For simplicity in unit test, bypass auth using bootstrap admin if enabled.
    # In real tests, you would obtain a JWT via the auth router.
    # Here we check environment setting; if not available, skip test.
    token = os.environ.get("TEST_JWT_TOKEN")
    if not token:
        pytest.skip("TEST_JWT_TOKEN not set; skipping auth-protected status test")
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.unit
def test_status_endpoint_requires_auth():
    res = client.get("/api/v1/status")
    assert res.status_code in (401, 403)


@pytest.mark.unit
def test_status_endpoint_ok_when_authenticated():
    headers = authenticate_headers()
    res = client.get("/api/v1/status", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
