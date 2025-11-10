import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.skip(
    reason="Auth fixtures required; enable when test auth is configured"
)

client = TestClient(app)


@pytest.fixture
def auth_headers():
    # Replace with a valid token for your test environment
    return {"Authorization": "Bearer test-token"}


def test_fhir_bundle_batch_success(auth_headers):
    # Assumes patient with id 1 exists for test
    bundle = {
        "resourceType": "Bundle",
        "type": "batch",
        "entry": [{"request": {"method": "GET", "url": "Patient/1"}}],
    }
    response = client.post("/fhir/", json=bundle, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "batch-response"
    assert len(data["entry"]) == 1
    assert data["entry"][0]["response"]["status"] == "200 OK"
    assert data["entry"][0]["resource"]["resourceType"] == "Patient"


def test_fhir_bundle_batch_not_found(auth_headers):
    bundle = {
        "resourceType": "Bundle",
        "type": "batch",
        "entry": [{"request": {"method": "GET", "url": "Patient/999999"}}],
    }
    response = client.post("/fhir/", json=bundle, headers=auth_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["resourceType"] == "OperationOutcome"
    assert "not found" in data["issue"][0]["diagnostics"].lower()


def test_fhir_bundle_batch_invalid_type(auth_headers):
    bundle = {"resourceType": "Bundle", "type": "transaction", "entry": []}
    response = client.post("/fhir/", json=bundle, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert data["resourceType"] == "OperationOutcome"
    assert "only batch bundle supported" in data["issue"][0]["diagnostics"].lower()


def test_fhir_bundle_batch_unsupported_method(auth_headers):
    bundle = {
        "resourceType": "Bundle",
        "type": "batch",
        "entry": [{"request": {"method": "POST", "url": "Patient/1"}}],
    }
    response = client.post("/fhir/", json=bundle, headers=auth_headers)
    assert response.status_code == 400
    data = response.json()
    assert data["resourceType"] == "OperationOutcome"
    assert "only get batch supported" in data["issue"][0]["diagnostics"].lower()
