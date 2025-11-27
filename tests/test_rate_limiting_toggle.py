"""Tests for runtime rate limiting toggle parsing."""

import importlib
from types import ModuleType

from app.core import config


def _reload_config() -> ModuleType:
    """Reload the config module to pick up environment changes."""

    return importlib.reload(config)


def test_rate_limiting_enabled_by_default(monkeypatch):
    """Default configuration should enable rate limiting."""

    monkeypatch.delenv("ENABLE_RATE_LIMITING", raising=False)
    reloaded = _reload_config()
    assert reloaded.is_rate_limiting_enabled() is True


def test_rate_limiting_can_be_disabled_via_env(monkeypatch):
    """Explicitly disabling via env should be respected."""

    monkeypatch.setenv("ENABLE_RATE_LIMITING", "false")
    reloaded = _reload_config()
    assert reloaded.is_rate_limiting_enabled() is False


def test_rate_limiting_handles_invalid_env_value(monkeypatch):
    """Invalid env values should fall back to the configured default."""

    monkeypatch.setenv("ENABLE_RATE_LIMITING", "not-a-bool")
    reloaded = _reload_config()
    assert reloaded.is_rate_limiting_enabled() is True


def test_rate_limiting_accepts_truthy_variants(monkeypatch):
    """Common truthy values should enable rate limiting."""

    for truthy_value in ["1", "true", "yes", "on", "TRUE", "On"]:
        monkeypatch.setenv("ENABLE_RATE_LIMITING", truthy_value)
        reloaded = _reload_config()
        assert reloaded.is_rate_limiting_enabled() is True


def test_rate_limiting_accepts_falsy_variants(monkeypatch):
    """Common falsy values should disable rate limiting."""

    for falsy_value in ["0", "false", "no", "off", "FALSE", "Off"]:
        monkeypatch.setenv("ENABLE_RATE_LIMITING", falsy_value)
        reloaded = _reload_config()
        assert reloaded.is_rate_limiting_enabled() is False
