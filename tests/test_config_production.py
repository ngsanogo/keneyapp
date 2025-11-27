"""Production configuration safeguards."""

import pytest

from app.core.config import (
    is_production_environment,
    settings,
    validate_production_settings,
)


def test_is_production_environment_matches_common_aliases():
    assert is_production_environment("production") is True
    assert is_production_environment("prod") is True
    assert is_production_environment("staging") is False


def test_validate_production_settings_noop_in_non_production(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "ENABLE_BOOTSTRAP_ADMIN", True)

    # Should not raise because the environment is not production.
    validate_production_settings()


def test_validate_production_settings_flags_insecure_defaults(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEBUG", True)
    monkeypatch.setattr(settings, "SECRET_KEY", "your-secret-key-change-in-production")
    monkeypatch.setattr(settings, "ENABLE_BOOTSTRAP_ADMIN", True)
    monkeypatch.setattr(
        settings, "DATABASE_URL", "postgresql://keneyapp:keneyapp@localhost:5432/keneyapp"
    )
    monkeypatch.setattr(settings, "APP_URL", "http://localhost:8000")

    with pytest.raises(RuntimeError) as exc_info:
        validate_production_settings()

    error_message = str(exc_info.value)
    assert "DEBUG must be False" in error_message
    assert "SECRET_KEY" in error_message
    assert "ENABLE_BOOTSTRAP_ADMIN" in error_message
    assert "DATABASE_URL" in error_message
    assert "APP_URL" in error_message


def test_validate_production_settings_allows_hardened_configuration(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEBUG", False)
    monkeypatch.setattr(settings, "SECRET_KEY", "sufficiently-long-and-random-secret-key-value")
    monkeypatch.setattr(settings, "ENABLE_BOOTSTRAP_ADMIN", False)
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql://prod_user:secret@prod-db:5432/keneyapp")
    monkeypatch.setattr(settings, "APP_URL", "https://keneyapp.example.com")

    validate_production_settings()
