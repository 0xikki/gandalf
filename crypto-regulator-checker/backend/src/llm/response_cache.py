import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime
import aioredis
from ..providers.base_provider import LLMResponse

class ResponseCache:
    """Cache for LLM responses using Redis."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the response cache.
        
        Args:
            redis_url (str): Redis connection URL
        """
        self.redis = aioredis.from_url(redis_url)
    
    def _generate_cache_key(self, prompt: str, provider: str, **kwargs) -> str:
        """Generate a cache key for the request.
        
        Args:
            prompt (str): The input prompt
            provider (str): The LLM provider name
            **kwargs: Additional parameters that affect the response
        
        Returns:
            str: Cache key
        """
        # Create a dictionary of all parameters that affect the response
        cache_dict = {
            "prompt": prompt,
            "provider": provider,
            **kwargs
        }
        
        # Convert to a stable string representation and hash it
        cache_str = json.dumps(cache_dict, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    async def get(self, prompt: str, provider: str, ttl: int, **kwargs) -> Optional[LLMResponse]:
        """Get a cached response if available and not expired.
        
        Args:
            prompt (str): The input prompt
            provider (str): The LLM provider name
            ttl (int): Time-to-live in seconds
            **kwargs: Additional parameters that affect the response
        
        Returns:
            Optional[LLMResponse]: Cached response if available, None otherwise
        """
        cache_key = self._generate_cache_key(prompt, provider, **kwargs)
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            try:
                data = json.loads(cached_data)
                # Convert the cached dictionary back to an LLMResponse
                return LLMResponse(
                    text=data["text"],
                    metadata=data["metadata"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    provider=data["provider"],
                    tokens_used=data.get("tokens_used"),
                    cost=data.get("cost")
                )
            except (json.JSONDecodeError, KeyError):
                # If there's any error reading the cache, invalidate it
                await self.redis.delete(cache_key)
                return None
        
        return None
    
    async def set(self, prompt: str, response: LLMResponse, ttl: int, **kwargs) -> None:
        """Cache an LLM response.
        
        Args:
            prompt (str): The input prompt
            response (LLMResponse): The response to cache
            ttl (int): Time-to-live in seconds
            **kwargs: Additional parameters that affect the response
        """
        cache_key = self._generate_cache_key(prompt, response.provider, **kwargs)
        
        # Convert LLMResponse to a dictionary for caching
        cache_data = {
            "text": response.text,
            "metadata": response.metadata,
            "timestamp": response.timestamp.isoformat(),
            "provider": response.provider,
            "tokens_used": response.tokens_used,
            "cost": response.cost
        }
        
        await self.redis.setex(
            cache_key,
            ttl,
            json.dumps(cache_data)
        )
    
    async def invalidate(self, prompt: str, provider: str, **kwargs) -> None:
        """Invalidate a cached response.
        
        Args:
            prompt (str): The input prompt
            provider (str): The LLM provider name
            **kwargs: Additional parameters that affect the response
        """
        cache_key = self._generate_cache_key(prompt, provider, **kwargs)
        await self.redis.delete(cache_key)
    
    async def clear_all(self) -> None:
        """Clear all cached responses."""
        await self.redis.flushdb()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics including:
                - total_keys: Total number of cached items
                - memory_used: Memory used by cache in bytes
                - hit_rate: Cache hit rate if available
        """
        info = await self.redis.info()
        return {
            "total_keys": await self.redis.dbsize(),
            "memory_used": info.get("used_memory", 0),
            "hit_rate": None  # Redis doesn't provide hit rate out of the box
        }
    
    async def close(self) -> None:
        """Close the Redis connection."""
        await self.redis.close() 