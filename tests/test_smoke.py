"""
Smoke tests for critical API flows.

These tests are designed to run against a live Docker stack to verify
that the most critical user journeys work end-to-end.

Usage:
    # Start the docker stack first
    docker compose up -d

    # Run smoke tests
    pytest tests/test_smoke.py -v

    # Or use the BASE_URL environment variable for a different target
    BASE_URL=http://production.example.com pytest tests/test_smoke.py -v
"""

import os
import time

import pytest
import requests


# Configuration for smoke tests - can be overridden via environment variables
class Config:
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    API_BASE = f"{BASE_URL}/api/v1"
    HEALTH_CHECK_RETRIES = 30
    HEALTH_CHECK_INTERVAL = 1  # seconds


BASE_URL = Config.BASE_URL
API_BASE = Config.API_BASE


@pytest.fixture(scope="module")
def api_client():
    """Wait for API to be ready and return session."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    # Wait for API to be ready
    for attempt in range(Config.HEALTH_CHECK_RETRIES):
        try:
            response = session.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print(f"API is ready at {BASE_URL}")
                return session
        except requests.exceptions.RequestException:
            pass
        time.sleep(Config.HEALTH_CHECK_INTERVAL)

    pytest.fail(f"API at {BASE_URL} did not become ready in time")


@pytest.fixture(scope="module")
def admin_token(api_client: requests.Session) -> str:
    """Login as admin and return access token."""
    response = api_client.post(
        f"{API_BASE}/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def doctor_token(api_client: requests.Session) -> str:
    """Login as doctor and return access token."""
    response = api_client.post(
        f"{API_BASE}/auth/login",
        json={"username": "doctor", "password": "doctor123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access token in login response"
    return data["access_token"]


class TestHealthAndDocs:
    """Test basic health and documentation endpoints."""

    def test_health_endpoint(self, api_client: requests.Session):
        """Test that health endpoint returns 200."""
        response = api_client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_api_docs_accessible(self, api_client: requests.Session):
        """Test that API documentation is accessible."""
        response = api_client.get(f"{API_BASE}/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()

    def test_metrics_endpoint(self, api_client: requests.Session):
        """Test that Prometheus metrics endpoint is accessible."""
        response = api_client.get(f"{BASE_URL}/metrics")
        assert response.status_code == 200
        # Check for some expected metrics
        assert "http_requests_total" in response.text or "process_" in response.text


class TestAuthenticationFlow:
    """Test authentication flows."""

    def test_login_with_valid_credentials(self, api_client: requests.Session):
        """Test successful login with admin credentials."""
        response = api_client.post(
            f"{API_BASE}/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_with_invalid_credentials(self, api_client: requests.Session):
        """Test login failure with invalid credentials."""
        response = api_client.post(
            f"{API_BASE}/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
        )
        assert response.status_code in [401, 422]

    def test_get_current_user(self, api_client: requests.Session, admin_token: str):
        """Test retrieving current user profile."""
        response = api_client.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert data["username"] == "admin"
        assert "role" in data


class TestPatientManagement:
    """Test patient management flows."""

    def test_list_patients(self, api_client: requests.Session, doctor_token: str):
        """Test listing patients as a doctor."""
        response = api_client.get(
            f"{API_BASE}/patients/",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_and_get_patient(
        self, api_client: requests.Session, doctor_token: str
    ):
        """Test creating a patient and retrieving it."""
        # Create patient
        patient_data = {
            "first_name": "Smoke",
            "last_name": "Test",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "email": "smoke.test@example.com",
            "phone": "+1234567890",
            "address": "123 Test St",
        }
        response = api_client.post(
            f"{API_BASE}/patients/",
            json=patient_data,
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        # Expect 201 Created for successful patient creation
        assert (
            response.status_code == 201
        ), f"Expected 201 Created, got {response.status_code}: {response.text}"
        created_patient = response.json()
        assert "id" in created_patient
        patient_id = created_patient["id"]

        # Retrieve patient
        response = api_client.get(
            f"{API_BASE}/patients/{patient_id}",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        patient = response.json()
        assert patient["first_name"] == "Smoke"
        assert patient["last_name"] == "Test"


class TestAppointmentFlow:
    """Test appointment management flows."""

    def test_list_appointments(self, api_client: requests.Session, doctor_token: str):
        """Test listing appointments as a doctor."""
        response = api_client.get(
            f"{API_BASE}/appointments/",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDashboard:
    """Test dashboard and statistics."""

    def test_dashboard_stats(self, api_client: requests.Session, admin_token: str):
        """Test retrieving dashboard statistics."""
        response = api_client.get(
            f"{API_BASE}/dashboard/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Check for expected keys
        expected_keys = ["total_patients", "total_appointments"]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"


class TestAccessControl:
    """Test access control and authorization."""

    def test_unauthorized_access(self, api_client: requests.Session):
        """Test that protected endpoints require authentication."""
        response = api_client.get(f"{API_BASE}/patients/")
        assert response.status_code == 401

    def test_invalid_token(self, api_client: requests.Session):
        """Test that invalid tokens are rejected."""
        response = api_client.get(
            f"{API_BASE}/patients/",
            headers={"Authorization": "Bearer invalid_token_12345"},
        )
        assert response.status_code == 401
