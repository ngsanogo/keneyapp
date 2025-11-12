"""
Rate limiting for API endpoints.

Provides a context-aware key function that can effectively disable rate
limits when the application sets `app.state.disable_rate_limit = True`.
This is used in tests to avoid hitting decorator-enforced limits across
the suite without changing route code.
"""

from typing import Any

from slowapi import Limiter
from slowapi.util import get_remote_address


def _context_aware_key_func(request: Any) -> str:
    """Key function that honors an app state flag to disable limits.

    When `request.app.state.disable_rate_limit` is True, return a unique key
    per request so counters never accumulate and limits won't be hit.
    Otherwise, fall back to the remote address-based key.
    """
    try:
        if getattr(request.app.state, "disable_rate_limit", False):  # type: ignore[attr-defined]
            # Unique key per request effectively disables rate-limiting
            import uuid

            return uuid.uuid4().hex
    except Exception:
        # On any error, default to remote address
        pass

    return get_remote_address(request)


# Initialize rate limiter with context-aware key
limiter = Limiter(key_func=_context_aware_key_func)


def get_limiter() -> Limiter:
    """Get the rate limiter instance."""
    return limiter
