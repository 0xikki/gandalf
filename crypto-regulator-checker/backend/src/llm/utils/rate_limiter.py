import time
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int
    requests_per_hour: int
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize the rate limiter.
        
        Args:
            config (RateLimitConfig): Rate limit configuration
        """
        self.config = config
        self._minute_requests = 0
        self._hour_requests = 0
        self._last_minute_reset = datetime.now()
        self._last_hour_reset = datetime.now()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request.
        
        Returns:
            bool: True if request is allowed, False otherwise
        """
        async with self._lock:
            now = datetime.now()
            
            # Reset counters if time windows have passed
            if now - self._last_minute_reset > timedelta(minutes=1):
                self._minute_requests = 0
                self._last_minute_reset = now
            
            if now - self._last_hour_reset > timedelta(hours=1):
                self._hour_requests = 0
                self._last_hour_reset = now
            
            # Check if we're within limits
            if (self._minute_requests < self.config.requests_per_minute and
                self._hour_requests < self.config.requests_per_hour):
                self._minute_requests += 1
                self._hour_requests += 1
                return True
            
            return False
    
    async def wait_and_retry(self) -> bool:
        """Wait and retry acquiring permission.
        
        Returns:
            bool: True if request is eventually allowed, False if max retries exceeded
        """
        for attempt in range(self.config.max_retries):
            if await self.acquire():
                return True
            
            # Wait before retrying
            await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return False
    
    def get_current_usage(self) -> Dict[str, int]:
        """Get current rate limit usage.
        
        Returns:
            Dict[str, int]: Current usage statistics
        """
        return {
            "minute_requests": self._minute_requests,
            "hour_requests": self._hour_requests,
            "minute_remaining": self.config.requests_per_minute - self._minute_requests,
            "hour_remaining": self.config.requests_per_hour - self._hour_requests
        }
    
    def get_reset_times(self) -> Dict[str, datetime]:
        """Get when rate limits will reset.
        
        Returns:
            Dict[str, datetime]: Reset times for different windows
        """
        return {
            "minute_reset": self._last_minute_reset + timedelta(minutes=1),
            "hour_reset": self._last_hour_reset + timedelta(hours=1)
        }
    
    async def __aenter__(self) -> bool:
        """Async context manager entry.
        
        Returns:
            bool: True if request is allowed
        """
        return await self.wait_and_retry()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        pass 