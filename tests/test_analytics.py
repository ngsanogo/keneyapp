"""
Tests for analytics router endpoints
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import UserRole


@pytest.fixture
def analytics_headers(auth_headers):
    """Use standard auth headers for analytics tests"""
    return auth_headers


def test_get_dashboard_metrics(client: TestClient, analytics_headers):
    """Test dashboard metrics endpoint"""
    response = client.get(
        "/api/v1/analytics/metrics",
        headers=analytics_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "total_patients" in data
    assert "patients_change" in data
    assert "appointments_today" in data
    assert "active_doctors" in data
    assert "monthly_revenue" in data

    assert isinstance(data["total_patients"], int)
    assert isinstance(data["patients_change"], (int, float))
    assert isinstance(data["appointments_today"], int)


def test_get_patient_trend_default_period(client: TestClient, analytics_headers):
    """Test patient trend with default 30-day period"""
    response = client.get(
        "/api/v1/analytics/patient-trend",
        headers=analytics_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "labels" in data
    assert "values" in data
    assert isinstance(data["labels"], list)
    assert isinstance(data["values"], list)
    assert len(data["labels"]) == len(data["values"])

    # Should have 31 data points for 30-day period (inclusive)
    assert len(data["labels"]) == 31


def test_get_patient_trend_custom_period(client: TestClient, analytics_headers):
    """Test patient trend with custom 7-day period"""
    response = client.get(
        "/api/v1/analytics/patient-trend?period=7d",
        headers=analytics_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Should have 8 data points for 7-day period
    assert len(data["labels"]) == 8

    # Validate date format
    for label in data["labels"]:
        datetime.strptime(label, "%Y-%m-%d")


def test_get_appointment_stats(client: TestClient, analytics_headers):
    """Test appointment statistics endpoint"""
    response = client.get(
        "/api/v1/analytics/appointments?period=7d",
        headers=analytics_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "labels" in data
    assert "completed" in data
    assert "pending" in data
    assert "cancelled" in data

    assert isinstance(data["completed"], list)
    assert isinstance(data["pending"], list)
    assert isinstance(data["cancelled"], list)

    # All arrays should have same length
    assert len(data["labels"]) == len(data["completed"])
    assert len(data["labels"]) == len(data["pending"])
    assert len(data["labels"]) == len(data["cancelled"])


def test_get_gender_distribution(client: TestClient, analytics_headers):
    """Test gender distribution endpoint"""
    response = client.get(
        "/api/v1/analytics/gender-distribution",
        headers=analytics_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "labels" in data
    assert "values" in data
    assert isinstance(data["labels"], list)
    assert isinstance(data["values"], list)
    assert len(data["labels"]) == len(data["values"])

    # Values should be non-negative integers
    for value in data["values"]:
        assert isinstance(value, int)
        assert value >= 0


def test_analytics_endpoints_require_authentication(client: TestClient):
    """Test that analytics endpoints require authentication"""
    endpoints = [
        "/api/v1/analytics/metrics",
        "/api/v1/analytics/patient-trend",
        "/api/v1/analytics/appointments",
        "/api/v1/analytics/gender-distribution",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401


def test_analytics_rate_limiting(client: TestClient, analytics_headers):
    """Test that rate limiting is applied to analytics endpoints"""
    # Make multiple rapid requests to trigger rate limit
    responses = []
    for _ in range(105):  # Exceeds 100/minute limit
        response = client.get(
            "/api/v1/analytics/metrics",
            headers=analytics_headers,
        )
        responses.append(response.status_code)

    # At least one request should be rate limited
    assert 429 in responses


def test_analytics_rbac_permissions(client: TestClient, db_session):
    """Test that only authorized roles can access analytics"""
    from app.models.user import User
    from app.core.security import get_password_hash

    # Create a user with PATIENT role (should not have access)
    unauthorized_user = User(
        email="patient@test.com",
        username="patient_user",
        hashed_password=get_password_hash("testpassword"),
        role=UserRole.PATIENT,
        tenant_id=1,
        is_active=True,
    )
    db_session.add(unauthorized_user)
    db_session.commit()

    # Attempt to get token and access analytics
    login_response = client.post(
        "/api/v1/auth/token",
        data={"username": "patient@test.com", "password": "testpassword"},
    )

    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/v1/analytics/metrics",
            headers=headers,
        )

        # Should be forbidden (403) for unauthorized role
        assert response.status_code in [403, 401]


def test_patient_trend_empty_data(client: TestClient, analytics_headers, db_session):
    """Test patient trend when no data exists"""
    # This test assumes a clean database or mocked scenario
    response = client.get(
        "/api/v1/analytics/patient-trend?period=7d",
        headers=analytics_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Should still return properly formatted response with zeros
    assert len(data["labels"]) == 8
    assert all(isinstance(v, int) for v in data["values"])


def test_analytics_audit_logging(client: TestClient, analytics_headers, db_session):
    """Test that analytics access is logged in audit trail"""
    from app.models.audit_log import AuditLog

    # Clear existing audit logs for this test
    db_session.query(AuditLog).filter(AuditLog.resource_type == "analytics_metrics").delete()
    db_session.commit()

    # Make request
    response = client.get(
        "/api/v1/analytics/metrics",
        headers=analytics_headers,
    )

    assert response.status_code == 200

    # Verify audit log was created
    audit_log = (
        db_session.query(AuditLog).filter(AuditLog.resource_type == "analytics_metrics").first()
    )

    assert audit_log is not None
    assert audit_log.action == "READ"
    assert "metric_type" in audit_log.details
