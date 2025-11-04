import os

# Ensure TESTING mode to avoid real DB initialization in app lifespan
os.environ["TESTING"] = "true"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data and isinstance(data["name"], str)
    assert data.get("status") == "running"


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_metrics_endpoint():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    # Prometheus content type
    assert "text/plain" in resp.headers.get("content-type", "")
    # Metrics payload should not be empty
    assert resp.content and len(resp.content) > 0


def test_fhir_http_exception_operation_outcome():
    # Hitting a FHIR-protected path without auth should yield OperationOutcome 401
    resp = client.get("/api/v1/fhir/Patient/123")
    assert resp.status_code == 401
    payload = resp.json()
    assert payload.get("resourceType") == "OperationOutcome"
    assert isinstance(payload.get("issue"), list)
    assert payload["issue"][0]["code"] == "unauthorized"
