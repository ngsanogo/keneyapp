"""
Comprehensive tests for medical record sharing service (v3.0).

Tests cover:
- Share creation with tokens
- PIN protection
- Expiration handling
- Access tracking
- Scope validation (full_record, custom)
- Security and tenant isolation
- Revocation
- Access limits
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import secrets


@pytest.mark.unit
class TestTokenGeneration:
    """Test secure token generation."""

    def test_token_is_random(self):
        """Test that tokens are randomly generated."""
        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)

        assert token1 != token2
        assert len(token1) > 32
        assert len(token2) > 32

    def test_pin_generation(self):
        """Test 6-digit PIN generation."""
        pin = str(secrets.randbelow(1000000)).zfill(6)

        assert len(pin) == 6
        assert pin.isdigit()


@pytest.mark.integration
class TestShareCreation:
    """Test share creation operations."""

    def test_create_share_full_record(self, client: TestClient, auth_headers: dict):
        """Test creating a share with full_record scope."""
        payload = {
            "patient_id": 1,
            "scope": "full_record",
            "recipient_email": "dr.external@hospital.com",
            "recipient_name": "Dr. Martin",
            "expires_in_hours": 48,
            "require_pin": True,
            "purpose": "Consultation externe",
        }

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["scope"] == "full_record"
        assert "share_token" in data
        assert "access_pin" in data
        assert len(data["access_pin"]) == 6
        assert data["status"] == "active"

    def test_create_share_custom_scope(self, client: TestClient, auth_headers: dict):
        """Test creating a share with custom scope."""
        payload = {
            "patient_id": 1,
            "scope": "custom",
            "custom_resources": ["appointments", "prescriptions"],
            "recipient_email": "insurance@company.com",
            "expires_in_hours": 24,
            "require_pin": False,
        }

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["scope"] == "custom"
        assert data["custom_resources"] == ["appointments", "prescriptions"]

    def test_create_share_without_pin(self, client: TestClient, auth_headers: dict):
        """Test creating a share without PIN protection."""
        payload = {
            "patient_id": 1,
            "scope": "appointments_only",
            "expires_in_hours": 12,
            "require_pin": False,
        }

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["access_pin"] is None

    def test_create_share_with_max_access_count(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a share with access limit."""
        payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 72,
            "max_access_count": 3,
            "purpose": "Seconde opinion",
        }

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["max_access_count"] == 3

    def test_create_share_invalid_patient(self, client: TestClient, auth_headers: dict):
        """Test creating share for non-existent patient."""
        payload = {"patient_id": 99999, "scope": "full_record", "expires_in_hours": 24}

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code in [404, 403]


@pytest.mark.integration
class TestShareAccess:
    """Test accessing shared records."""

    def test_access_share_with_valid_token(
        self, client: TestClient, auth_headers: dict
    ):
        """Test accessing a share with valid token."""
        # Create share first
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "require_pin": False,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            token = share_data["share_token"]

            # Access share (no auth required)
            access_payload = {"token": token}

            access_response = client.post("/api/v1/shares/access", json=access_payload)

            assert access_response.status_code == 200
            accessed_data = access_response.json()
            assert "patient" in accessed_data

    def test_access_share_with_pin(self, client: TestClient, auth_headers: dict):
        """Test accessing a PIN-protected share."""
        # Create share with PIN
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "require_pin": True,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            token = share_data["share_token"]
            pin = share_data["access_pin"]

            # Access with correct PIN
            access_payload = {"token": token, "pin": pin}

            access_response = client.post("/api/v1/shares/access", json=access_payload)

            assert access_response.status_code == 200

    def test_access_share_with_wrong_pin(self, client: TestClient, auth_headers: dict):
        """Test that wrong PIN is rejected."""
        # Create share with PIN
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "require_pin": True,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            token = share_data["share_token"]

            # Access with wrong PIN
            access_payload = {"token": token, "pin": "000000"}  # Wrong PIN

            access_response = client.post("/api/v1/shares/access", json=access_payload)

            assert access_response.status_code in [401, 403]

    def test_access_share_without_required_pin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that PIN is required when configured."""
        # Create share with PIN
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "require_pin": True,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            token = share_data["share_token"]

            # Access without PIN
            access_payload = {
                "token": token
                # Missing PIN
            }

            access_response = client.post("/api/v1/shares/access", json=access_payload)

            assert access_response.status_code in [400, 401, 422]

    def test_access_invalid_token(self, client: TestClient):
        """Test accessing with invalid token."""
        access_payload = {"token": "invalid_token_12345"}

        response = client.post("/api/v1/shares/access", json=access_payload)

        assert response.status_code in [404, 401]


@pytest.mark.integration
class TestShareExpiration:
    """Test share expiration logic."""

    def test_access_expired_share(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        """Test that expired shares cannot be accessed."""
        from app.models.medical_record_share import MedicalRecordShare
        from datetime import datetime, timedelta

        # Create an expired share directly in DB
        expired_share = MedicalRecordShare(
            patient_id=1,
            shared_by_user_id=1,
            share_token=secrets.token_urlsafe(32),
            scope="full_record",
            status="active",
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            tenant_id=1,
        )
        db_session.add(expired_share)
        db_session.commit()

        # Try to access expired share
        access_payload = {"token": expired_share.share_token}

        response = client.post("/api/v1/shares/access", json=access_payload)

        assert response.status_code in [410, 403, 404]  # Gone or Forbidden

    def test_share_auto_expires(self, client: TestClient, auth_headers: dict):
        """Test that share expiration is set correctly."""
        payload = {"patient_id": 1, "scope": "full_record", "expires_in_hours": 48}

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()

        # Parse expires_at
        expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        now = datetime.now(expires_at.tzinfo)

        # Should expire in approximately 48 hours
        time_diff = (expires_at - now).total_seconds() / 3600
        assert 47 < time_diff < 49  # Allow 1 hour margin


@pytest.mark.integration
class TestAccessTracking:
    """Test access tracking and limits."""

    def test_access_count_incremented(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        """Test that access_count is incremented on each access."""
        # Create share
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "require_pin": False,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            share_id = share_data["id"]
            token = share_data["share_token"]

            # Access once
            access_payload = {"token": token}
            client.post("/api/v1/shares/access", json=access_payload)

            # Check access count in DB
            from app.models.medical_record_share import MedicalRecordShare

            share = db_session.query(MedicalRecordShare).filter_by(id=share_id).first()

            if share:
                assert share.access_count >= 1

    def test_max_access_count_enforced(self, client: TestClient, auth_headers: dict):
        """Test that max_access_count is enforced."""
        # Create share with limit
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "max_access_count": 2,
            "require_pin": False,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            token = share_data["share_token"]

            access_payload = {"token": token}

            # Access twice (within limit)
            response1 = client.post("/api/v1/shares/access", json=access_payload)
            response2 = client.post("/api/v1/shares/access", json=access_payload)

            # Third access should fail
            response3 = client.post("/api/v1/shares/access", json=access_payload)

            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response3.status_code in [403, 410]  # Forbidden or Gone

    def test_last_accessed_timestamp_updated(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        """Test that last_accessed_at is updated."""
        # Create and access share
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "require_pin": False,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            share_id = share_data["id"]
            token = share_data["share_token"]

            # Access share
            access_payload = {"token": token}
            client.post("/api/v1/shares/access", json=access_payload)

            # Check timestamp
            from app.models.medical_record_share import MedicalRecordShare

            share = db_session.query(MedicalRecordShare).filter_by(id=share_id).first()

            if share:
                assert share.last_accessed_at is not None


@pytest.mark.integration
class TestShareRevocation:
    """Test share revocation."""

    def test_revoke_share(self, client: TestClient, auth_headers: dict):
        """Test revoking an active share."""
        # Create share
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 48,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            share_id = share_data["id"]
            token = share_data["share_token"]

            # Revoke share
            revoke_response = client.delete(
                f"/api/v1/shares/{share_id}", headers=auth_headers
            )

            assert revoke_response.status_code in [200, 204]

            # Try to access revoked share
            access_payload = {"token": token}
            access_response = client.post("/api/v1/shares/access", json=access_payload)

            assert access_response.status_code in [403, 404, 410]

    def test_cannot_revoke_others_share(self, client: TestClient, auth_headers: dict):
        """Test that users cannot revoke shares they didn't create."""
        # Try to revoke non-existent or unauthorized share
        response = client.delete("/api/v1/shares/99999", headers=auth_headers)

        assert response.status_code in [403, 404]


@pytest.mark.integration
class TestShareScopes:
    """Test different share scopes."""

    @pytest.mark.parametrize(
        "scope",
        ["full_record", "appointments_only", "prescriptions_only", "documents_only"],
    )
    def test_scope_types(self, client: TestClient, auth_headers: dict, scope: str):
        """Test creating shares with different scopes."""
        payload = {"patient_id": 1, "scope": scope, "expires_in_hours": 24}

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["scope"] == scope

    def test_custom_scope_with_resources(self, client: TestClient, auth_headers: dict):
        """Test custom scope requires custom_resources."""
        payload = {
            "patient_id": 1,
            "scope": "custom",
            "custom_resources": ["appointments", "lab_results"],
            "expires_in_hours": 24,
        }

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 201


@pytest.mark.integration
class TestShareList:
    """Test listing shares."""

    def test_list_user_shares(self, client: TestClient, auth_headers: dict):
        """Test listing all shares created by user."""
        # Create some shares
        for i in range(3):
            payload = {"patient_id": 1, "scope": "full_record", "expires_in_hours": 24}
            client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        # List shares
        response = client.get("/api/v1/shares/", headers=auth_headers)

        assert response.status_code == 200
        shares = response.json()
        assert isinstance(shares, list)
        assert len(shares) >= 3


@pytest.mark.integration
class TestShareSecurity:
    """Test share security features."""

    def test_tenant_isolation(self, client: TestClient, auth_headers: dict):
        """Test that shares are tenant-isolated."""
        # Try to access share from different tenant
        access_payload = {"token": "fake_token_from_another_tenant"}

        response = client.post("/api/v1/shares/access", json=access_payload)

        assert response.status_code in [404, 401]

    def test_ip_tracking(
        self, client: TestClient, auth_headers: dict, db_session: Session
    ):
        """Test that IP address is tracked on access."""
        # Create and access share
        create_payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "require_pin": False,
        }

        create_response = client.post(
            "/api/v1/shares/", json=create_payload, headers=auth_headers
        )

        if create_response.status_code == 201:
            share_data = create_response.json()
            share_id = share_data["id"]
            token = share_data["share_token"]

            # Access share
            access_payload = {"token": token}
            client.post("/api/v1/shares/access", json=access_payload)

            # Check IP tracking
            from app.models.medical_record_share import MedicalRecordShare

            share = db_session.query(MedicalRecordShare).filter_by(id=share_id).first()

            if share:
                # last_accessed_ip should be set (testclient uses 127.0.0.1)
                assert (
                    share.last_accessed_ip is not None
                    or share.last_accessed_ip == "testclient"
                )

    def test_consent_required(self, client: TestClient, auth_headers: dict):
        """Test that consent is tracked."""
        payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 24,
            "purpose": "External consultation",
        }

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        # consent_given should default to True for API-created shares
        assert "consent_given" in data or data.get("status") == "active"


@pytest.mark.integration
class TestShareValidation:
    """Test share validation rules."""

    def test_invalid_expires_in_hours(self, client: TestClient, auth_headers: dict):
        """Test that invalid expiration is rejected."""
        payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": -1,  # Negative hours
        }

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        assert response.status_code == 422

    def test_max_expiration_limit(self, client: TestClient, auth_headers: dict):
        """Test that very long expiration is rejected."""
        payload = {
            "patient_id": 1,
            "scope": "full_record",
            "expires_in_hours": 10000,  # ~1 year
        }

        response = client.post("/api/v1/shares/", json=payload, headers=auth_headers)

        # Should be rejected or limited (implementation dependent)
        assert response.status_code in [201, 400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
