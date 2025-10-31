"""Unit tests for shared dependency helpers."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.dependencies import require_roles
from app.models.user import UserRole


def _make_request() -> Request:
    """Create a minimal Starlette request for dependency invocation."""
    return Request({"type": "http"})


def test_require_roles_accepts_list_input() -> None:
    """Guard should accept list-based configuration and allow matching roles."""
    dependency = require_roles([UserRole.ADMIN, UserRole.DOCTOR])
    user = SimpleNamespace(role=UserRole.ADMIN)

    result = dependency(_make_request(), current_user=user)  # type: ignore[arg-type]
    assert result is user


def test_require_roles_denies_unlisted_role() -> None:
    """Non-authorized roles trigger a 403 HTTPException."""
    dependency = require_roles(UserRole.ADMIN)
    user = SimpleNamespace(role=UserRole.NURSE)

    with pytest.raises(HTTPException) as exc:
        dependency(_make_request(), current_user=user)  # type: ignore[arg-type]

    assert exc.value.status_code == 403
    assert "Insufficient permissions" in exc.value.detail


def test_require_roles_allows_super_admin_bypass() -> None:
    """Super admins bypass per-route role restrictions."""
    dependency = require_roles(UserRole.DOCTOR, UserRole.NURSE)
    user = SimpleNamespace(role=UserRole.SUPER_ADMIN)

    result = dependency(_make_request(), current_user=user)  # type: ignore[arg-type]
    assert result is user
