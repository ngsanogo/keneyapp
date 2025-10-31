"""
Bootstrap helpers for development and test environments.

This module provides utilities that ensure a minimal set of data exists
when the application boots, such as a default tenant and administrative user.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import User, UserRole


def ensure_bootstrap_admin(db: Session, requested_username: str) -> Optional[User]:
    """
    Ensure that a default tenant and administrative user exist.

    This helper is primarily used in development, testing, or demo environments
    to guarantee that contract tests and smoke tests have credentials available.

    Args:
        db: Active SQLAlchemy session.
        requested_username: Username provided during the login attempt.

    Returns:
        The existing or newly created administrative User instance, or None if
        bootstrap creation is disabled or the username does not match the
        configured bootstrap account.
    """
    if not settings.ENABLE_BOOTSTRAP_ADMIN:
        return None

    if requested_username != settings.BOOTSTRAP_ADMIN_USERNAME:
        return None

    if not settings.BOOTSTRAP_ADMIN_PASSWORD:
        return None

    # Reuse an existing admin user if it is already present.
    existing_user = (
        db.query(User)
        .filter(User.username == settings.BOOTSTRAP_ADMIN_USERNAME)
        .first()
    )
    if existing_user:
        return existing_user

    # Ensure there is an active tenant to attach the bootstrap user to.
    tenant = (
        db.query(Tenant).filter(Tenant.slug == settings.BOOTSTRAP_TENANT_SLUG).first()
    )

    if not tenant:
        tenant = Tenant(
            name=settings.BOOTSTRAP_TENANT_NAME,
            slug=settings.BOOTSTRAP_TENANT_SLUG,
            is_active=True,
            configuration={},
        )
        db.add(tenant)
        db.flush()  # Obtain tenant.id without committing yet.

    bootstrap_user = User(
        tenant_id=tenant.id,
        email=settings.BOOTSTRAP_ADMIN_EMAIL,
        username=settings.BOOTSTRAP_ADMIN_USERNAME,
        full_name=settings.BOOTSTRAP_ADMIN_FULL_NAME,
        role=UserRole.SUPER_ADMIN,
        hashed_password=get_password_hash(settings.BOOTSTRAP_ADMIN_PASSWORD),
        is_active=True,
        password_changed_at=datetime.now(timezone.utc),
    )

    db.add(bootstrap_user)
    db.commit()
    db.refresh(bootstrap_user)
    return bootstrap_user
