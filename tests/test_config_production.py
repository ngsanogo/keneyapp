"""Production configuration safeguards."""

import pytest

from app.core.config import (
    Settings,
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
        settings,
        "DATABASE_URL",
        "postgresql://keneyapp:keneyapp@localhost:5432/keneyapp",
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
    monkeypatch.setattr(
        settings, "DATABASE_URL", "postgresql://prod_user:secret@prod-db:5432/keneyapp"
    )
    monkeypatch.setattr(settings, "APP_URL", "https://keneyapp.example.com")
    monkeypatch.setattr(
        settings, "ENCRYPTION_KEY", "a-very-long-encryption-key-for-production-32chars"
    )
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["https://keneyapp.example.com"])

    validate_production_settings()


def _create_production_settings_for_test(**overrides):
    """Helper to create a Settings instance that can be modified for production testing.

    Creates a development settings instance and then applies overrides using
    object.__setattr__ to bypass production validation during instantiation.

    Args:
        **overrides: Field values to set on the settings instance.

    Returns:
        A Settings instance with the specified overrides.
    """
    test_settings = Settings(ENVIRONMENT="development")
    object.__setattr__(test_settings, "ENVIRONMENT", "production")
    for key, value in overrides.items():
        object.__setattr__(test_settings, key, value)
    return test_settings


def test_enforce_production_allows_secure_configuration():
    """Test that enforce_production_safety passes with secure configuration."""
    test_settings = _create_production_settings_for_test(
        SECRET_KEY="this-is-a-secure-secret-key-for-production-use",
        DEBUG=False,
        ALLOWED_ORIGINS=["https://keneyapp.example"],
    )

    # This should not raise since we have valid config
    test_settings.enforce_production_safety()


def test_enforce_production_secret_key_check():
    """Test that enforce_production_safety raises for default SECRET_KEY."""
    test_settings = _create_production_settings_for_test(
        SECRET_KEY="your-secret-key-change-in-production",
        DEBUG=False,
    )

    with pytest.raises(ValueError) as exc_info:
        test_settings.enforce_production_safety()

    assert "SECRET_KEY must be overridden in production" in str(exc_info.value)


def test_enforce_production_debug_check():
    """Test that enforce_production_safety raises for DEBUG=True."""
    test_settings = _create_production_settings_for_test(
        SECRET_KEY="secure-production-secret-key-12345",
        DEBUG=True,
    )

    with pytest.raises(ValueError) as exc_info:
        test_settings.enforce_production_safety()

    assert "DEBUG must be False in production" in str(exc_info.value)


def test_enforce_production_allowed_origins_wildcard_check():
    """Test that enforce_production_safety raises for ALLOWED_ORIGINS with wildcard."""
    test_settings = _create_production_settings_for_test(
        SECRET_KEY="secure-production-secret-key-12345",
        DEBUG=False,
        ALLOWED_ORIGINS=["*"],
    )

    with pytest.raises(ValueError) as exc_info:
        test_settings.enforce_production_safety()

    assert "ALLOWED_ORIGINS cannot include '*' in production" in str(exc_info.value)


def test_enforce_production_allowed_origins_empty_check():
    """Test that enforce_production_safety raises for empty ALLOWED_ORIGINS."""
    test_settings = _create_production_settings_for_test(
        SECRET_KEY="secure-production-secret-key-12345",
        DEBUG=False,
        ALLOWED_ORIGINS=[],
    )

    with pytest.raises(ValueError) as exc_info:
        test_settings.enforce_production_safety()

    assert "ALLOWED_ORIGINS must include at least one origin in production" in str(exc_info.value)
