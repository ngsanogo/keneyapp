"""Multi-factor authentication utilities using TOTP."""

from __future__ import annotations

from typing import Optional

import pyotp

from app.core.config import settings


def generate_mfa_secret() -> str:
    """Create a new base32 secret suitable for TOTP."""

    return pyotp.random_base32(length=32)


def get_totp(secret: str) -> pyotp.TOTP:
    """Return a TOTP object configured with the application issuer."""

    return pyotp.TOTP(secret, issuer=settings.MFA_ISSUER, name=settings.APP_NAME)


def generate_provisioning_uri(secret: str, username: str) -> str:
    """Return the provisioning URI for authenticator applications."""

    totp = get_totp(secret)
    return totp.provisioning_uri(name=username, issuer_name=settings.MFA_ISSUER)


def verify_totp(secret: Optional[str], code: Optional[str]) -> bool:
    """Validate the provided TOTP code against the stored secret."""

    if not secret or not code:
        return False

    totp = get_totp(secret)
    try:
        return totp.verify(code, valid_window=1)
    except (ValueError, TypeError):
        # Catch validation errors from pyotp (invalid secret or code format)
        return False
