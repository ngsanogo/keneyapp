"""
Authentication edge-case tests to improve coverage on negative branches.

Covers:
- Inactive user login forbidden
- Inactive tenant login forbidden
- Account lockout after consecutive failures
- MFA disable with invalid code
- MFA activation without prior setup
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User


def _get_admin(db: Session) -> User:
    """Fetch the bootstrap/admin user created by tests."""
    return db.query(User).filter(User.username == "admin").first()


def test_login_inactive_user_forbidden(client: TestClient, db: Session):
    # Ensure admin exists via bootstrap during login attempt
    user = _get_admin(db)
    if not user:
        # Trigger bootstrap creation by calling login once
        client.post(
            "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
        )
        user = _get_admin(db)
    assert user is not None

    # Deactivate user and attempt login
    user.is_active = False
    db.commit()

    resp = client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "User account is inactive"


def test_login_inactive_tenant_forbidden(client: TestClient, db: Session):
    user = _get_admin(db)
    if not user:
        client.post(
            "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
        )
        user = _get_admin(db)
    assert user is not None

    # Deactivate tenant and attempt login
    user.tenant.is_active = False
    db.commit()

    resp = client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Tenant is inactive"


def test_login_lockout_after_failed_attempts(client: TestClient, db: Session):
    user = _get_admin(db)
    if not user:
        client.post(
            "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
        )
        user = _get_admin(db)
    assert user is not None

    # Pre-position user at threshold - 1 failed attempts
    user.failed_login_attempts = max(0, settings.MAX_FAILED_LOGIN_ATTEMPTS - 1)
    user.is_locked = False
    db.commit()

    # One more bad password should lock the account
    bad = client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "wrongpass"}
    )
    assert bad.status_code == 401

    # Refresh from DB and verify lock
    db.refresh(user)
    assert user.is_locked is True

    # Now even the right password should be forbidden due to lock
    locked = client.post(
        "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
    )
    assert locked.status_code == 403
    assert locked.json()["detail"] == "Account locked due to failed login attempts"


def test_mfa_disable_invalid_code(client: TestClient, db: Session, test_doctor: User):
    """Test disabling MFA with invalid code fails"""
    user = test_doctor  # Use the user that client fixture will return
    
    # Enable MFA with a known secret
    user.mfa_enabled = True
    user.mfa_secret = "JBSWY3DPEHPK3PXP"  # base32 for "Hello!" style secret
    db.commit()
    db.refresh(user)

    # Send an invalid code (no need for JWT - client fixture handles auth)
    resp = client.post(
        "/api/v1/auth/mfa/disable",
        json={"code": "000000"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid MFA code"


def test_mfa_activate_without_setup(client: TestClient, db: Session):
    user = _get_admin(db)
    if not user:
        client.post(
            "/api/v1/auth/login", data={"username": "admin", "password": "admin123"}
        )
        user = _get_admin(db)
    assert user is not None

    # Ensure no secret has been set
    user.mfa_secret = None
    user.mfa_enabled = False
    db.commit()

    token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
        }
    )

    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/v1/auth/mfa/activate",
        headers=headers,
        json={"code": "123456"},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "MFA has not been initiated"
