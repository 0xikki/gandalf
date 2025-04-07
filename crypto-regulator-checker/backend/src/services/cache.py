"""Cache service for response caching and general application caching."""

import json
import logging
from typing import Any, Optional, Union
import aioredis
from src.core.config import settings

# Initialize logger
logger = logging.getLogger(__name__)

class CacheService:
    """Service for handling caching operations."""
    
    def __init__(self):
        """Initialize the cache service."""
        self._redis: Optional[aioredis.Redis] = None
        self._prefix = "cache:"
        
    async def init(self):
        """Initialize Redis connection."""
        if not self._redis:
            try:
                self._redis = await aioredis.create_redis_pool(
                    settings.REDIS_URL,
                    minsize=5,
                    maxsize=settings.performance.db_pool_size,
                    timeout=settings.performance.db_pool_timeout
                )
                logger.info("Cache service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize cache service: {str(e)}")
                raise

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            self._redis.close()
            await self._redis.wait_closed()
            self._redis = None
            logger.info("Cache service closed")

    def _get_key(self, key: str) -> str:
        """
        Get the full cache key with prefix.
        
        Args:
            key: The base key
            
        Returns:
            The full cache key
        """
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value or None if not found
        """
        try:
            if not self._redis:
                await self.init()
            
            full_key = self._get_key(key)
            value = await self._redis.get(full_key)
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: The cache key
            value: The value to cache
            expire: Optional expiration time in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._redis:
                await self.init()
            
            full_key = self._get_key(key)
            serialized = json.dumps(value)
            
            if expire:
                await self._redis.setex(full_key, expire, serialized)
            else:
                await self._redis.set(full_key, serialized)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._redis:
                await self.init()
            
            full_key = self._get_key(key)
            await self._redis.delete(full_key)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False

    async def clear(self, pattern: str = "*") -> bool:
        """
        Clear cache entries matching pattern.
        
        Args:
            pattern: Pattern to match keys
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._redis:
                await self.init()
            
            full_pattern = self._get_key(pattern)
            keys = await self._redis.keys(full_pattern)
            
            if keys:
                await self._redis.delete(*keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False

# Initialize global cache service
cache_service = CacheService() 