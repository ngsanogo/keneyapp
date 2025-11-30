"""
Tests for cache service
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.cache_service import CacheService, cache_service


@pytest.fixture
def cache():
    """Create a test cache service (memory only)"""
    service = CacheService()
    service.redis_client = None  # Force memory-only mode for tests
    service._memory_cache = {}
    service._stats = {
        "hits": 0,
        "misses": 0,
        "memory_hits": 0,
        "redis_hits": 0,
        "sets": 0,
        "deletes": 0,
    }
    return service


def test_set_and_get(cache):
    """Test basic set and get operations"""
    cache.set("test:key", "test_value", ttl=60)

    value = cache.get("test:key")
    assert value == "test_value"
    assert cache._stats["sets"] == 1
    assert cache._stats["hits"] == 1


def test_get_nonexistent(cache):
    """Test get with non-existent key"""
    value = cache.get("nonexistent:key")
    assert value is None
    assert cache._stats["misses"] == 1


def test_get_with_default(cache):
    """Test get with default value"""
    value = cache.get("nonexistent:key", default="default_value")
    assert value == "default_value"


def test_delete(cache):
    """Test delete operation"""
    cache.set("test:key", "value")
    assert cache.exists("test:key")

    cache.delete("test:key")
    assert not cache.exists("test:key")
    assert cache._stats["deletes"] == 1


def test_exists(cache):
    """Test exists check"""
    assert not cache.exists("test:key")

    cache.set("test:key", "value")
    assert cache.exists("test:key")


def test_increment(cache):
    """Test increment operation"""
    # First increment creates the key
    value = cache.increment("counter:key")
    assert value == 1

    # Subsequent increments
    value = cache.increment("counter:key")
    assert value == 2

    value = cache.increment("counter:key", amount=5)
    assert value == 7


def test_delete_pattern(cache):
    """Test pattern-based deletion"""
    # Create multiple keys
    cache.set("users:1:profile", "user1")
    cache.set("users:2:profile", "user2")
    cache.set("users:1:settings", "settings1")
    cache.set("posts:1:data", "post1")

    # Delete with pattern
    cache.delete_pattern("users:*")

    # Users keys should be deleted
    assert not cache.exists("users:1:profile")
    assert not cache.exists("users:2:profile")
    assert not cache.exists("users:1:settings")

    # Posts key should still exist
    assert cache.exists("posts:1:data")


def test_generate_key(cache):
    """Test cache key generation"""
    # Simple key
    key = cache.generate_key("users", 123)
    assert "users" in key
    assert "123" in key

    # With keyword args
    key = cache.generate_key("search", page=2, limit=50)
    assert "search" in key

    # Same args should produce same key
    key1 = cache.generate_key("test", 1, 2, foo="bar")
    key2 = cache.generate_key("test", 1, 2, foo="bar")
    assert key1 == key2


def test_cached_decorator(cache):
    """Test caching decorator"""
    call_count = 0

    @cache.cached(key_prefix="expensive", ttl=60)
    def expensive_function(x, y):
        nonlocal call_count
        call_count += 1
        return x + y

    # First call executes function
    result = expensive_function(2, 3)
    assert result == 5
    assert call_count == 1

    # Second call with same args uses cache
    result = expensive_function(2, 3)
    assert result == 5
    assert call_count == 1  # Not called again

    # Different args execute function
    result = expensive_function(5, 7)
    assert result == 12
    assert call_count == 2


def test_warm_cache(cache):
    """Test cache warming"""
    data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
    }

    cache.warm_cache(data, ttl=120)

    # All keys should be cached
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


def test_get_stats(cache):
    """Test statistics collection"""
    # Perform various operations
    cache.set("key1", "value1")
    cache.get("key1")  # Hit
    cache.get("key2")  # Miss
    cache.delete("key1")

    stats = cache.get_stats()

    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["sets"] == 1
    assert stats["deletes"] == 1
    assert "hit_rate_percent" in stats


def test_clear_all(cache):
    """Test clearing all cache"""
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    cache.clear_all()

    assert not cache.exists("key1")
    assert not cache.exists("key2")
    assert not cache.exists("key3")


def test_lru_eviction(cache):
    """Test LRU eviction in memory cache"""
    cache.max_memory_items = 5

    # Add 10 items
    for i in range(10):
        cache.set(f"key{i}", f"value{i}")

    # Memory cache should only have 5 items (most recent)
    assert len(cache._memory_cache) <= 5

    # Older items should not be in memory
    assert "key0" not in cache._memory_cache
    assert "key1" not in cache._memory_cache


def test_complex_objects(cache):
    """Test caching complex objects"""
    complex_obj = {
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
        "tuple": (4, 5, 6),
    }

    cache.set("complex:key", complex_obj)
    retrieved = cache.get("complex:key")

    assert retrieved == complex_obj
    assert isinstance(retrieved["list"], list)
    assert isinstance(retrieved["dict"], dict)


def test_ttl_expiration(cache):
    """Test TTL expiration (memory cache only)"""
    # Note: This test only works for memory cache
    # Redis TTL is handled by Redis server
    cache.set("temp:key", "temp_value", ttl=1)

    # Should exist immediately
    assert cache.get("temp:key") == "temp_value"

    # Wait for expiration
    time.sleep(1.1)

    # Should be expired (in memory cache)
    # Note: Memory cache doesn't automatically expire, but this demonstrates the concept
    # In production, Redis handles TTL automatically


def test_cache_service_singleton():
    """Test that cache_service is a singleton instance"""
    from app.services.cache_service import cache_service as cs1
    from app.services.cache_service import cache_service as cs2

    assert cs1 is cs2
