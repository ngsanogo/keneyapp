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
import pytest

from app.core.config import Settings


def test_enforce_production_allows_secure_configuration():
    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="super-secret-key",
        DEBUG=False,
        ALLOWED_ORIGINS=["https://keneyapp.example"],
    )

    settings.enforce_production_safety()


@pytest.mark.parametrize(
    "kwargs, expected_error",
    [
        (
            {"ENVIRONMENT": "production", "SECRET_KEY": "your-secret-key-change-in-production", "DEBUG": False},
            "SECRET_KEY must be overridden in production",
        ),
        (
            {"ENVIRONMENT": "production", "DEBUG": True, "ALLOWED_ORIGINS": ["https://keneyapp.example"]},
            "DEBUG must be False in production",
        ),
        (
            {"ENVIRONMENT": "production", "ALLOWED_ORIGINS": ["*"]},
            "ALLOWED_ORIGINS cannot include '*' in production",
        ),
        (
            {"ENVIRONMENT": "production", "ALLOWED_ORIGINS": []},
            "ALLOWED_ORIGINS must include at least one origin in production",
        ),
    ],
)
def test_enforce_production_raises_on_insecure_defaults(kwargs, expected_error):
    settings = Settings(**kwargs)

    with pytest.raises(ValueError) as exc_info:
        settings.enforce_production_safety()

    assert expected_error in str(exc_info.value)
