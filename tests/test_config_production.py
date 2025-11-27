"""Production configuration hardening tests."""

import pytest

from app.core.config import Settings, validate_production_settings


def test_validate_production_settings_accepts_hardened_configuration():
    """A fully configured production setup should not raise errors."""

    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="super-secure-key",
        ALLOWED_ORIGINS=["https://keneyapp.example.com"],
        DATABASE_URL="postgresql://user:pass@db:5432/keneyapp",
        DEBUG=False,
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
    )

    validate_production_settings(settings)


def test_validate_production_settings_rejects_insecure_defaults():
    """Misconfigurations should abort production startup with helpful details."""

    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="your-secret-key-change-in-production",
        ALLOWED_ORIGINS=["http://localhost:3000"],
        DATABASE_URL="postgresql://keneyapp:keneyapp@localhost:5432/keneyapp",
        DEBUG=True,
        ACCESS_TOKEN_EXPIRE_MINUTES=0,
    )

    with pytest.raises(RuntimeError) as excinfo:
        validate_production_settings(settings)

    message = str(excinfo.value)
    assert "SECRET_KEY" in message
    assert "DEBUG" in message
    assert "ALLOWED_ORIGINS" in message
    assert "DATABASE_URL" in message
    assert "ACCESS_TOKEN_EXPIRE_MINUTES" in message


def test_validation_skipped_when_not_production():
    """Non-production environments are not blocked by strict checks."""

    settings = Settings(
        ENVIRONMENT="staging",
        SECRET_KEY="your-secret-key-change-in-production",
        ALLOWED_ORIGINS=["http://localhost:3000"],
        DATABASE_URL="postgresql://keneyapp:keneyapp@localhost:5432/keneyapp",
        DEBUG=True,
        ACCESS_TOKEN_EXPIRE_MINUTES=0,
    )

    validate_production_settings(settings)
