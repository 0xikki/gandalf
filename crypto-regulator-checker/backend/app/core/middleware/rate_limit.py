from typing import Callable, Dict, Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_limit: int = 10,
        cleanup_interval: int = 60
    ):
        """Initialize rate limiter with configurable limits.
        
        Args:
            requests_per_minute: Number of requests allowed per minute
            burst_limit: Maximum burst of requests allowed
            cleanup_interval: Interval in seconds to clean up old entries
        """
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.cleanup_interval = cleanup_interval
        self.request_counts: Dict[str, Dict[float, int]] = defaultdict(lambda: defaultdict(int))
        self.locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self) -> None:
        """Start a background thread to clean up old entries."""
        def cleanup() -> None:
            while True:
                time.sleep(self.cleanup_interval)
                self._cleanup_old_entries()
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def _cleanup_old_entries(self) -> None:
        """Remove entries older than 1 minute."""
        current_time = time.time()
        for ip in list(self.request_counts.keys()):
            with self.locks[ip]:
                self.request_counts[ip] = {
                    ts: count 
                    for ts, count in self.request_counts[ip].items()
                    if current_time - ts < 60
                }
                if not self.request_counts[ip]:
                    del self.request_counts[ip]
                    del self.locks[ip]
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request headers or direct connection."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, ip: str) -> Tuple[bool, Dict[str, int]]:
        """Check if request should be rate limited.
        
        Returns:
            Tuple of (is_allowed, limit_info)
        """
        current_time = time.time()
        
        with self.locks[ip]:
            # Clean up old entries for this IP
            self.request_counts[ip] = {
                ts: count 
                for ts, count in self.request_counts[ip].items()
                if current_time - ts < 60
            }
            
            # Calculate current request count
            total_requests = sum(self.request_counts[ip].values())
            
            # Check if burst limit is exceeded
            if total_requests >= self.burst_limit:
                return False, {
                    "limit": self.requests_per_minute,
                    "remaining": 0,
                    "reset": int(min(self.request_counts[ip].keys()) + 60 - current_time)
                }
            
            # Add new request
            self.request_counts[ip][current_time] += 1
            
            # Calculate remaining requests
            remaining = max(0, self.requests_per_minute - total_requests - 1)
            
            return True, {
                "limit": self.requests_per_minute,
                "remaining": remaining,
                "reset": 60
            }

class RateLimitMiddleware:
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_limit: int = 10,
        exclude_paths: Optional[list[str]] = None
    ):
        """Initialize rate limit middleware.
        
        Args:
            requests_per_minute: Number of requests allowed per minute
            burst_limit: Maximum burst of requests allowed
            exclude_paths: List of paths to exclude from rate limiting
        """
        self.limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            burst_limit=burst_limit
        )
        self.exclude_paths = exclude_paths or []
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable
    ) -> JSONResponse:
        """Process request through rate limiter."""
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        client_ip = self.limiter._get_client_ip(request)
        is_allowed, limit_info = self.limiter._check_rate_limit(client_ip)
        
        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(limit_info["limit"]),
            "X-RateLimit-Remaining": str(limit_info["remaining"]),
            "X-RateLimit-Reset": str(limit_info["reset"])
        }
        
        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests",
                    "retry_after": limit_info["reset"]
                },
                headers=headers
            )
        
        response = await call_next(request)
        
        # Add headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response 