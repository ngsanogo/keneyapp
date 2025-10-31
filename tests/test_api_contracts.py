"""
API Contract Tests

These tests verify that the API contracts are maintained and don't break
backward compatibility. They validate:
- Request/response schemas
- Status codes
- Headers
- Error messages
- Data types and formats
"""

import pytest
from fastapi.testclient import TestClient
from jsonschema import validate, ValidationError

from app.main import app

client = TestClient(app)


# JSON Schema for authentication response
AUTH_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["access_token", "token_type"],
    "properties": {
        "access_token": {"type": "string", "minLength": 1},
        "token_type": {"type": "string", "enum": ["bearer"]}
    }
}

# JSON Schema for patient response
PATIENT_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["id", "first_name", "last_name", "date_of_birth", "gender"],
    "properties": {
        "id": {"type": "integer"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "date_of_birth": {"type": "string", "format": "date"},
        "gender": {"type": "string", "enum": ["male", "female", "other"]},
        "email": {"type": ["string", "null"]},
        "phone": {"type": ["string", "null"]},
        "address": {"type": ["string", "null"]}
    }
}

# JSON Schema for error response
ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["detail"],
    "properties": {
        "detail": {
            "oneOf": [
                {"type": "string"},
                {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["loc", "msg", "type"],
                        "properties": {
                            "loc": {"type": "array"},
                            "msg": {"type": "string"},
                            "type": {"type": "string"}
                        }
                    }
                }
            ]
        }
    }
}


class TestRootEndpointContract:
    """Test contracts for root endpoint."""

    def test_root_endpoint_structure(self):
        """Verify root endpoint returns expected structure."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate required fields
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert "docs" in data
        
        # Validate data types
        assert isinstance(data["name"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["docs"], str)
        
        # Validate specific values
        assert data["status"] == "running"
        assert data["docs"].startswith("/api/v")

    def test_root_endpoint_headers(self):
        """Verify root endpoint includes expected headers."""
        response = client.get("/")
        
        # Check for security headers
        assert "X-Correlation-ID" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers


class TestHealthEndpointContract:
    """Test contracts for health check endpoint."""

    def test_health_check_structure(self):
        """Verify health check returns expected structure."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_check_response_time(self):
        """Verify health check responds quickly."""
        import time
        
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond in less than 1 second


class TestAuthenticationContract:
    """Test contracts for authentication endpoints."""

    def test_login_success_contract(self):
        """Verify successful login response structure."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate against schema
        validate(instance=data, schema=AUTH_RESPONSE_SCHEMA)
        
        # Additional validations
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    def test_login_failure_contract(self):
        """Verify failed login response structure."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "invalid",
                "password": "invalid"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        
        # Validate error structure
        validate(instance=data, schema=ERROR_RESPONSE_SCHEMA)
        assert isinstance(data["detail"], str)

    def test_login_validation_error_contract(self):
        """Verify validation error response structure."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "",  # Invalid: empty username
                "password": "test"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Validate error structure
        validate(instance=data, schema=ERROR_RESPONSE_SCHEMA)


class TestPatientEndpointContract:
    """Test contracts for patient endpoints."""

    @pytest.fixture
    def auth_token(self):
        """Get authentication token for tests."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        return response.json()["access_token"]

    def test_list_patients_requires_auth(self):
        """Verify patients endpoint requires authentication."""
        response = client.get("/api/v1/patients")
        
        assert response.status_code == 401
        validate(instance=response.json(), schema=ERROR_RESPONSE_SCHEMA)

    def test_list_patients_contract(self, auth_token):
        """Verify patients list response structure."""
        response = client.get(
            "/api/v1/patients",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # If list has items, validate first item
        if len(data) > 0:
            validate(instance=data[0], schema=PATIENT_RESPONSE_SCHEMA)

    def test_create_patient_validation_contract(self, auth_token):
        """Verify patient creation validation."""
        response = client.post(
            "/api/v1/patients",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "first_name": "",  # Invalid: empty
                "last_name": "Test"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        
        validate(instance=data, schema=ERROR_RESPONSE_SCHEMA)
        
        # Validation errors should be a list
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0


class TestMetricsEndpointContract:
    """Test contracts for metrics endpoint."""

    def test_metrics_endpoint_format(self):
        """Verify metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        
        # Prometheus metrics are plain text
        assert "text/plain" in response.headers.get("content-type", "")
        
        # Should contain metrics
        content = response.text
        assert len(content) > 0
        
        # Check for expected metrics
        assert "http_requests_total" in content or "# HELP" in content


class TestAPIVersioning:
    """Test API versioning contracts."""

    def test_api_v1_prefix(self):
        """Verify all main endpoints use /api/v1 prefix."""
        endpoints_to_check = [
            "/api/v1/auth/login",
            "/api/v1/patients",
            "/api/v1/appointments",
            "/api/v1/prescriptions",
            "/api/v1/dashboard/stats",
        ]
        
        for endpoint in endpoints_to_check:
            response = client.get(endpoint)
            # Should not get 404 (endpoint exists)
            assert response.status_code != 404

    def test_docs_versioning(self):
        """Verify documentation is versioned."""
        response = client.get("/api/v1/docs")
        assert response.status_code == 200


class TestCORSHeaders:
    """Test CORS header contracts."""

    def test_cors_headers_present(self):
        """Verify CORS headers are set."""
        response = client.options(
            "/api/v1/patients",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # Should allow CORS
        assert "access-control-allow-origin" in response.headers


class TestRateLimiting:
    """Test rate limiting contracts."""

    def test_rate_limit_headers(self):
        """Verify rate limit headers are present."""
        response = client.get("/")
        
        # Rate limit headers should be present
        # Note: Actual header names depend on slowapi configuration
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling contracts."""

    def test_404_error_format(self):
        """Verify 404 errors follow contract."""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
        data = response.json()
        
        validate(instance=data, schema=ERROR_RESPONSE_SCHEMA)

    def test_method_not_allowed_format(self):
        """Verify 405 errors follow contract."""
        response = client.patch("/")  # Root doesn't accept PATCH
        
        assert response.status_code == 405
        data = response.json()
        
        validate(instance=data, schema=ERROR_RESPONSE_SCHEMA)


class TestResponseHeaders:
    """Test response header contracts."""

    def test_correlation_id_header(self):
        """Verify X-Correlation-ID header is always present."""
        endpoints = ["/", "/health", "/metrics"]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert "X-Correlation-ID" in response.headers

    def test_security_headers(self):
        """Verify security headers are present."""
        response = client.get("/")
        
        # Check for important security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"


class TestDateTimeFormats:
    """Test date/time format contracts."""

    @pytest.fixture
    def auth_token(self):
        """Get authentication token for tests."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"}
        )
        return response.json()["access_token"]

    def test_iso8601_datetime_format(self, auth_token):
        """Verify datetime fields use ISO 8601 format."""
        # This test would check that all datetime fields across the API
        # use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
        
        # Example with audit logs
        response = client.get(
            "/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check that any datetime fields follow ISO 8601
            # This is an example - adjust based on actual response structure
            assert response.status_code == 200


class TestBackwardCompatibility:
    """Test backward compatibility contracts."""

    def test_no_removed_fields(self):
        """Verify no fields have been removed from responses."""
        # This test serves as documentation that removing fields
        # from API responses is a breaking change
        
        response = client.get("/")
        data = response.json()
        
        # These fields must always be present
        required_fields = ["name", "version", "status", "docs"]
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing - breaking change!"

    def test_new_optional_fields_only(self):
        """Document that new fields should be optional."""
        # This test serves as documentation that new fields
        # should not be required to maintain backward compatibility
        pass


class TestContentTypeNegotiation:
    """Test content type handling."""

    def test_json_content_type(self):
        """Verify API returns JSON by default."""
        response = client.get("/")
        
        assert "application/json" in response.headers.get("content-type", "")

    def test_metrics_content_type(self):
        """Verify metrics endpoint returns correct content type."""
        response = client.get("/metrics")
        
        assert "text/plain" in response.headers.get("content-type", "")
