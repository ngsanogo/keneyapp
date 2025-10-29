"""
Rate limiting for API endpoints.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


def get_limiter():
    """Get the rate limiter instance."""
    return limiter
