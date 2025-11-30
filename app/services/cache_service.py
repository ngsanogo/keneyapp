"""
Advanced caching service with Redis
Provides intelligent caching strategies and cache warming
"""

import hashlib
import json
import pickle
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar

import redis
from redis import Redis

from app.core.config import settings
from app.core.logging_middleware import logger

T = TypeVar("T")


class CacheService:
    """
    Advanced caching service with multiple strategies

    Features:
    - Multi-level caching (memory + Redis)
    - Cache warming and preloading
    - Automatic invalidation patterns
    - Cache statistics and monitoring
    - Distributed cache coordination
    """

    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self._memory_cache: Dict[str, tuple] = {}  # key -> (value, expiry)
        self._memory_cache_max_size = 1000
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "memory_hits": 0,
            "redis_hits": 0,
        }
        self._initialize_redis()

    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=False,  # Handle binary data
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
        except Exception as e:
            logger.warning(
                f"Redis connection failed: {e}. " "Falling back to memory cache only."
            )
            self.redis_client = None

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and parameters
        Uses consistent hashing for complex objects
        """
        parts = [prefix]

        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                parts.append(str(arg))
            else:
                # Hash complex objects
                parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

        # Add keyword arguments (sorted for consistency)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
            parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])

        return ":".join(parts)

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Public method to generate consistent cache keys

        Args:
            prefix: Key prefix (e.g., 'patients:list')
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Generated cache key
        """
        return self._generate_key(prefix, *args, **kwargs)

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        return pickle.dumps(value)

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage"""
        return pickle.loads(data)

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get value from cache
        Tries memory cache first, then Redis
        """
        # Try memory cache first
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]
            if expiry is None or datetime.now(timezone.utc) < expiry:
                self._stats["hits"] += 1
                self._stats["memory_hits"] += 1
                return value
            else:
                # Expired, remove from memory cache
                del self._memory_cache[key]

        # Try Redis
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    value = self._deserialize(data)
                    # Store in memory cache for faster access
                    self._add_to_memory_cache(key, value)
                    self._stats["hits"] += 1
                    self._stats["redis_hits"] += 1
                    return value
            except Exception as e:
                logger.error(f"Redis get error for key {key}: {e}")

        self._stats["misses"] += 1
        return default

    def set(
        self, key: str, value: Any, ttl: Optional[int] = None, memory_only: bool = False
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = no expiration)
            memory_only: Store only in memory cache
        """
        expiry = None
        if ttl:
                expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        # Add to memory cache
        self._add_to_memory_cache(key, value, expiry)
        self._stats["sets"] += 1

        # Add to Redis
        if not memory_only and self.redis_client:
            try:
                data = self._serialize(value)
                if ttl:
                    self.redis_client.setex(key, ttl, data)
                else:
                    self.redis_client.set(key, data)
                return True
            except Exception as e:
                logger.error(f"Redis set error for key {key}: {e}")
                return False

        return True

    def _add_to_memory_cache(
        self, key: str, value: Any, expiry: Optional[datetime] = None
    ):
        """Add item to memory cache with LRU eviction"""
        # Simple LRU: remove oldest if at capacity
        if len(self._memory_cache) >= self._memory_cache_max_size:
            # Remove first (oldest) item
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]

        self._memory_cache[key] = (value, expiry)

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        # Remove from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]
        
        self._stats["deletes"] += 1

        # Remove from Redis
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete error for key {key}: {e}")
                return False

        return True

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Redis pattern (e.g., "patients:*")

        Returns:
            Number of keys deleted
        """
        count = 0

        # Get matching keys from memory cache
        keys_to_delete = [
            k for k in self._memory_cache.keys() if self._matches_pattern(k, pattern)
        ]
        for key in keys_to_delete:
            del self._memory_cache[key]
            count += 1

        # Clear from Redis
        if self.redis_client:
            try:
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor, match=pattern, count=100
                    )
                    if keys:
                        self.redis_client.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.error(f"Redis delete pattern error for {pattern}: {e}")

        return count

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching for memory cache"""
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                return key.startswith(parts[0]) and key.endswith(parts[1])
        return key == pattern

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if key in self._memory_cache:
            _, expiry = self._memory_cache[key]
            if expiry is None or datetime.utcnow() < expiry:
                return True

        if self.redis_client:
            try:
                return self.redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis exists error for key {key}: {e}")

        return False

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value"""
        if self.redis_client:
            try:
                return self.redis_client.incr(key, amount)
            except Exception as e:
                logger.error(f"Redis increment error for key {key}: {e}")

        # Fallback to memory cache
        current = self.get(key, 0)
        new_value = current + amount
        self.set(key, new_value)
        return new_value

    def cached(
        self,
        key_prefix: str,
        ttl: Optional[int] = 300,
        key_builder: Optional[Callable] = None,
    ):
        """
        Decorator for caching function results

        Usage:
            @cache_service.cached("my_function", ttl=600)
            def my_function(arg1, arg2):
                return expensive_operation(arg1, arg2)
        """

        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Build cache key
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self._generate_key(key_prefix, *args, **kwargs)

                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Execute function
                result = func(*args, **kwargs)

                # Store in cache
                self.set(cache_key, result, ttl=ttl)

                return result

            return wrapper

        return decorator

    def warm_cache(self, keys_values: List[tuple], ttl: Optional[int] = None) -> int:
        """
        Warm cache with multiple key-value pairs
        Useful for preloading frequently accessed data

        Args:
            keys_values: List of (key, value) tuples
            ttl: Time to live in seconds

        Returns:
            Number of keys successfully cached
        """
        count = 0
        for key, value in keys_values:
            if self.set(key, value, ttl=ttl):
                count += 1

        logger.info(f"Cache warmed with {count}/{len(keys_values)} keys")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        stats = {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self._memory_cache),
            "redis_connected": self.redis_client is not None,
        }

        # Add Redis info if available
        if self.redis_client:
            try:
                info = self.redis_client.info("stats")
                stats["redis_keys"] = self.redis_client.dbsize()
                stats["redis_used_memory"] = info.get("used_memory_human", "N/A")
            except Exception:
                pass

        return stats

    def clear_all(self):
        """Clear all cache (use with caution!)"""
        self._memory_cache.clear()

        if self.redis_client:
            try:
                self.redis_client.flushdb()
                logger.info("All cache cleared")
            except Exception as e:
                logger.error(f"Redis flush error: {e}")


# Global cache service instance
cache_service = CacheService()
