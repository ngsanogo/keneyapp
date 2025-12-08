import pytest

from app.core.config import Settings


def _set_base_env(monkeypatch, **overrides):
    base_values = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "x" * 64,
        "ENCRYPTION_KEY": "y" * 32,
        "ALLOWED_ORIGINS": "https://example.com",
        "DATABASE_URL": "postgresql://user:pass@db:5432/prod",
        "ENABLE_BOOTSTRAP_ADMIN": "false",
        "DEBUG": "false",
    }
    base_values.update(overrides)

    for key, value in base_values.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, str(value))


def test_production_rejects_default_secret_key(monkeypatch):
    _set_base_env(monkeypatch, SECRET_KEY="your-secret-key-change-in-production")

    with pytest.raises(ValueError, match="SECRET_KEY must be set"):
        Settings()


def test_production_rejects_debug_mode(monkeypatch):
    _set_base_env(monkeypatch, DEBUG="true")

    with pytest.raises(ValueError, match="DEBUG must be disabled"):
        Settings()


def test_production_rejects_local_database(monkeypatch):
    _set_base_env(
        monkeypatch,
        DATABASE_URL="postgresql://keneyapp:keneyapp@localhost:5432/keneyapp",
    )

    with pytest.raises(ValueError, match="production database"):
        Settings()


def test_production_requires_bootstrap_hardening(monkeypatch):
    _set_base_env(monkeypatch, ENABLE_BOOTSTRAP_ADMIN="true")

    with pytest.raises(ValueError, match="bootstrap admin"):
        Settings()


def test_production_requires_non_localhost_origins(monkeypatch):
    _set_base_env(monkeypatch, ALLOWED_ORIGINS="http://localhost:3000")

    with pytest.raises(ValueError, match="localhost"):
        Settings()


def test_production_allows_hardened_configuration(monkeypatch):
    _set_base_env(
        monkeypatch,
        ALLOWED_ORIGINS="https://example.com,https://api.example.com",
        ENABLE_BOOTSTRAP_ADMIN="false",
    )

    settings = Settings()

    assert settings.SECRET_KEY == "x" * 64
    assert settings.ALLOWED_ORIGINS == [
        "https://example.com",
        "https://api.example.com",
    ]
    assert settings.ENABLE_BOOTSTRAP_ADMIN is False
