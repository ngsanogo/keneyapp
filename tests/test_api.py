"""Basic API tests for KeneyApp."""

import uuid
from datetime import datetime, timezone

import pyotp
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole
from app.models.tenant import Tenant

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)


def _ensure_default_tenant() -> Tenant:
    """Create or fetch a default tenant for testing."""
    db = TestingSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.slug == "test-tenant").first()
    if not tenant:
        tenant = Tenant(
            name="Test Tenant",
            slug="test-tenant",
            is_active=True,
            configuration={},
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    db.close()
    return tenant


DEFAULT_TENANT_ID = _ensure_default_tenant().id

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_override_and_tenant():
    """Ensure DB override and default tenant are in place for each test."""
    app.dependency_overrides[get_db] = override_get_db
    _ensure_default_tenant()
    yield


def _create_user(role: UserRole = UserRole.ADMIN, password: str = "StrongPass123!"):
    """Helper to create a user in the test database."""
    db = TestingSessionLocal()
    username = f"{role.value}_{uuid.uuid4().hex[:8]}"
    user = User(
        tenant_id=DEFAULT_TENANT_ID,
        email=f"{username}@example.com",
        username=username,
        full_name="Test User",
        role=role,
        hashed_password=get_password_hash(password),
        is_active=True,
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user, password


def _authenticate_user(role: UserRole = UserRole.ADMIN):
    """Create and authenticate a user, returning the auth header."""
    user, password = _create_user(role=role)
    token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
        },
    )
    return {"Authorization": f"Bearer {token}"}, user


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


def test_patients_requires_auth():
    """Ensure patient endpoints enforce authentication."""
    response = client.get("/api/v1/patients/")
    assert response.status_code == 401


def test_authenticated_patient_workflow():
    """Exercise patient CRUD flow with authenticated admin."""
    headers, _ = _authenticate_user(role=UserRole.ADMIN)

    patient_payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "gender": "female",
        "email": "jane.doe@example.com",
        "phone": "+15551234567",
        "address": "123 Test Street",
        "medical_history": "none",
        "allergies": "penicillin",
        "blood_type": "O+",
        "emergency_contact": "John Doe",
        "emergency_phone": "+15557654321",
    }

    create_response = client.post(
        "/api/v1/patients/",
        json=patient_payload,
        headers=headers,
    )
    assert create_response.status_code == 201
    data = create_response.json()
    assert data["email"] == patient_payload["email"]
    patient_id = data["id"]

    list_response = client.get(
        "/api/v1/patients/",
        headers=headers,
    )
    assert list_response.status_code == 200
    patients = list_response.json()
    assert any(p["id"] == patient_id for p in patients)


def test_auth_me_endpoint():
    """Verify /auth/me returns the current user's profile."""
    headers, user = _authenticate_user(role=UserRole.DOCTOR)
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == user.username
    assert payload["role"] == user.role.value
    assert payload["mfa_enabled"] is False
    assert payload["is_locked"] is False


def test_admin_user_status_update():
    """Admins can lock and unlock user accounts."""
    admin_headers, admin_user = _authenticate_user(role=UserRole.ADMIN)
    target_user, _ = _create_user(role=UserRole.NURSE)

    lock_response = client.patch(
        f"/api/v1/users/{target_user.id}/status",
        headers=admin_headers,
        json={"is_locked": True},
    )
    assert lock_response.status_code == 200
    assert lock_response.json()["is_locked"] is True

    unlock_response = client.patch(
        f"/api/v1/users/{target_user.id}/status",
        headers=admin_headers,
        json={"is_locked": False, "is_active": True},
    )
    assert unlock_response.status_code == 200
    body = unlock_response.json()
    assert body["is_locked"] is False
    assert body["is_active"] is True


def test_change_password_flow():
    """Users can change their password and login with the new one."""
    headers, user = _authenticate_user(role=UserRole.DOCTOR)

    # Wrong current password
    bad_change = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "wrong", "new_password": "NewStrongPass!1"},
    )
    assert bad_change.status_code == 400

    good_change = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "StrongPass123!", "new_password": "NewStrongPass!1"},
    )
    assert good_change.status_code == 204

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": user.username, "password": "NewStrongPass!1"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_mfa_login_flow():
    """Enable MFA and ensure login requires the OTP."""
    headers, user = _authenticate_user(role=UserRole.NURSE)

    setup = client.post("/api/v1/auth/mfa/setup", headers=headers)
    assert setup.status_code == 200
    secret = setup.json()["secret"]

    activate = client.post(
        "/api/v1/auth/mfa/activate",
        headers=headers,
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert activate.status_code == 204

    # Login without OTP should fail
    missing_otp = client.post(
        "/api/v1/auth/login",
        data={"username": user.username, "password": "StrongPass123!"},
    )
    assert missing_otp.status_code == 401

    otp = pyotp.TOTP(secret).now()
    login_with_otp = client.post(
        "/api/v1/auth/login",
        data={"username": user.username, "password": "StrongPass123!", "otp": otp},
    )
    assert login_with_otp.status_code == 200
    assert "access_token" in login_with_otp.json()


def test_super_admin_tenant_crud_and_module_management():
    """Super admin can manage tenants and their modules."""
    headers, _ = _authenticate_user(role=UserRole.SUPER_ADMIN)

    tenant_payload = {
        "name": f"Tenant {uuid.uuid4().hex[:6]}",
        "slug": f"tenant-{uuid.uuid4().hex[:6]}",
        "contact_email": "ops@example.com",
        "region": "US",
        "default_timezone": "UTC",
        "is_active": True,
        "configuration": {"theme": "light"},
    }

    create_resp = client.post(
        "/api/v1/tenants/",
        json=tenant_payload,
        headers=headers,
    )
    assert create_resp.status_code == 201
    tenant_data = create_resp.json()
    tenant_id = tenant_data["id"]
    assert tenant_data["slug"] == tenant_payload["slug"]

    list_resp = client.get("/api/v1/tenants/", headers=headers)
    assert list_resp.status_code == 200
    tenant_ids = [tenant["id"] for tenant in list_resp.json()]
    assert tenant_id in tenant_ids

    update_resp = client.patch(
        f"/api/v1/tenants/{tenant_id}",
        json={"is_active": False, "region": "EU"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_active"] is False
    assert update_resp.json()["region"] == "EU"

    module_payload = {
        "is_enabled": True,
        "configuration": {"features": ["patients", "appointments"]},
    }
    module_resp = client.put(
        f"/api/v1/tenants/{tenant_id}/modules/patients",
        json=module_payload,
        headers=headers,
    )
    assert module_resp.status_code == 200
    module_data = module_resp.json()
    assert module_data["module_key"] == "patients"
    assert module_data["tenant_id"] == tenant_id
    assert module_data["is_enabled"] is True

    modules_list = client.get(
        f"/api/v1/tenants/{tenant_id}/modules",
        headers=headers,
    )
    assert modules_list.status_code == 200
    assert len(modules_list.json()) >= 1

    delete_resp = client.delete(
        f"/api/v1/tenants/{tenant_id}/modules/patients",
        headers=headers,
    )
    assert delete_resp.status_code == 204


def test_admin_cannot_manage_tenants():
    """Tenant-level admins should be forbidden from global tenant management."""
    headers, _ = _authenticate_user(role=UserRole.ADMIN)
    response = client.get("/api/v1/tenants/", headers=headers)
    assert response.status_code == 403
