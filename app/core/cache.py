"""
Redis caching utilities for performance optimization.
"""

import json
from typing import Optional, Any
from datetime import timedelta
import redis
from app.core.config import settings


# Redis connection pool (lazy initialization)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client.

    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        client = get_redis_client()
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except (redis.RedisError, json.JSONDecodeError):
        return None


def cache_set(
    key: str,
    value: Any,
    expire: Optional[int] = None
) -> bool:
    """
    Set value in cache.

    Args:
        key: Cache key
        value: Value to cache
        expire: Expiration time in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        serialized = json.dumps(value)
        if expire:
            client.setex(key, expire, serialized)
        else:
            client.set(key, serialized)
        return True
    except (redis.RedisError, TypeError):
        return False


def cache_delete(key: str) -> bool:
    """
    Delete value from cache.

    Args:
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        client.delete(key)
        return True
    except redis.RedisError:
        return False


def cache_clear_pattern(pattern: str) -> bool:
    """
    Delete all keys matching a pattern.

    Args:
        pattern: Redis pattern (e.g., "patient:*")

    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
        return True
    except redis.RedisError:
        return False
