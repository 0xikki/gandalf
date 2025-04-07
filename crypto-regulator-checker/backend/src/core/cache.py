"""Caching system with Redis and local fallback."""

import json
from typing import Any, Optional, TypeVar, Generic, Union
from datetime import datetime, timedelta
import pickle
from functools import wraps
import hashlib
import asyncio
import redis.asyncio as redis
from redis.exceptions import RedisError
from cachetools import TTLCache

from .config import get_settings
from .logging import get_logger
from .exceptions import CacheError

settings = get_settings()
logger = get_logger(__name__)

T = TypeVar('T')

class CacheKey:
    """Utility class for generating and managing cache keys."""
    
    PREFIX = "crc"  # Crypto Regulator Checker prefix
    
    @staticmethod
    def create(namespace: str, key: Union[str, int, bytes]) -> str:
        """Create a cache key with namespace.
        
        Args:
            namespace: Namespace for the key
            key: Base key value
            
        Returns:
            Formatted cache key
        """
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        return f"{CacheKey.PREFIX}:{namespace}:{str(key)}"
    
    @staticmethod
    def create_hash(*args: Any, **kwargs: Any) -> str:
        """Create a deterministic hash key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Hash-based cache key
        """
        # Create a string representation of args and kwargs
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = ":".join(key_parts)
        
        # Create hash
        return hashlib.sha256(key_str.encode()).hexdigest()

class Cache(Generic[T]):
    """Generic cache interface with Redis and local fallback."""
    
    def __init__(self):
        """Initialize cache with Redis connection and local fallback."""
        self.redis: Optional[redis.Redis] = None
        self.local_cache = TTLCache(
            maxsize=1000,
            ttl=settings.cache.default_ttl
        )
        self._connect_redis()
    
    def _connect_redis(self):
        """Establish Redis connection."""
        try:
            self.redis = redis.Redis.from_url(
                settings.cache.url,
                decode_responses=True
            )
        except Exception as e:
            logger.warning(
                "redis_connection_failed",
                error=str(e),
                fallback="Using local cache only"
            )
    
    async def get(self, key: str) -> Optional[T]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        # Try Redis first
        if self.redis:
            try:
                value = await self.redis.get(key)
                if value:
                    return self._deserialize(value)
            except RedisError as e:
                logger.error("redis_get_failed", key=key, error=str(e))
        
        # Fallback to local cache
        return self.local_cache.get(key)
    
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None
    ) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        ttl = ttl or settings.cache.default_ttl
        serialized = self._serialize(value)
        
        # Try Redis first
        if self.redis:
            try:
                await self.redis.set(key, serialized, ex=ttl)
            except RedisError as e:
                logger.error("redis_set_failed", key=key, error=str(e))
        
        # Also set in local cache
        self.local_cache[key] = value
    
    async def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key
        """
        # Try Redis first
        if self.redis:
            try:
                await self.redis.delete(key)
            except RedisError as e:
                logger.error("redis_delete_failed", key=key, error=str(e))
        
        # Also delete from local cache
        self.local_cache.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cached values."""
        # Try Redis first
        if self.redis:
            try:
                await self.redis.flushdb()
            except RedisError as e:
                logger.error("redis_clear_failed", error=str(e))
        
        # Also clear local cache
        self.local_cache.clear()
    
    def _serialize(self, value: T) -> str:
        """Serialize value for storage.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized value
        """
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            # Fallback to pickle for complex objects
            return pickle.dumps(value).hex()
    
    def _deserialize(self, value: str) -> T:
        """Deserialize value from storage.
        
        Args:
            value: Serialized value
            
        Returns:
            Deserialized value
        """
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            # Try pickle if JSON fails
            try:
                return pickle.loads(bytes.fromhex(value))
            except Exception as e:
                raise CacheError(f"Failed to deserialize cache value: {str(e)}")

def cached(
    namespace: str,
    ttl: Optional[int] = None,
    key_builder: Optional[callable] = None
):
    """Decorator for caching function results.
    
    Args:
        namespace: Cache namespace
        ttl: Optional TTL override
        key_builder: Optional function to build cache key
        
    Returns:
        Decorated function
    """
    cache = Cache()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                key = CacheKey.create_hash(*args, **kwargs)
            
            cache_key = CacheKey.create(namespace, key)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug("cache_hit", key=cache_key)
                return cached_value
            
            # Generate and cache value
            logger.debug("cache_miss", key=cache_key)
            value = await func(*args, **kwargs)
            await cache.set(cache_key, value, ttl=ttl)
            return value
            
        return wrapper
    return decorator

# Example usage:
# cache = Cache[Dict[str, Any]]()
# await cache.set("user:123", {"name": "John"})
# user = await cache.get("user:123")
#
# @cached("embeddings", ttl=3600)
# async def generate_embeddings(text: str) -> List[float]:
#     # Expensive embedding generation
#     return [0.1, 0.2, 0.3] 