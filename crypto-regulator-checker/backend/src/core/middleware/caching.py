"""Response caching middleware."""

import hashlib
import json
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.core.config import settings
import structlog

# Initialize logger
logger = structlog.get_logger(__name__)

class CachingMiddleware(BaseHTTPMiddleware):
    """Middleware for caching API responses."""
    
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] = None,
        ttl_override: Optional[int] = None
    ):
        """
        Initialize the caching middleware.
        
        Args:
            app: The ASGI application
            exclude_paths: List of paths to exclude from caching
            ttl_override: Override the default TTL from settings
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/api/health",
            "/api/metrics",
            "/api/analytics/vitals",
            "/api/auth/login",  # Don't cache auth endpoints
            "/api/auth/register"
        ]
        self.ttl = ttl_override or 300  # Default 5 minutes
        self.enabled = True
        self._cache = {}  # Simple in-memory cache

    def _generate_cache_key(self, request: Request) -> str:
        """
        Generate a unique cache key for the request.
        
        Args:
            request: The incoming request
            
        Returns:
            A unique cache key string
        """
        # Get request details
        method = request.method
        url = str(request.url)
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() in ['accept', 'accept-encoding']
        }
        
        # For GET requests, include query params
        params = dict(request.query_params) if method == "GET" else {}
        
        # Create key components
        key_parts = {
            'method': method,
            'url': url,
            'headers': headers,
            'params': params
        }
        
        # Generate hash
        key_string = json.dumps(key_parts, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process the request with caching.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint in the chain
            
        Returns:
            The cached response or a new response from the next middleware/endpoint
        """
        # Skip caching if disabled or path excluded
        if not self.enabled or any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Skip caching for non-GET methods
        if request.method != "GET":
            return await call_next(request)

        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            
            # Try to get from cache
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                logger.info("cache_hit", path=request.url.path)
                return cached_response

            # Get fresh response
            response = await call_next(request)
            
            # Cache successful responses
            if response.status_code == 200:
                self._cache_response(cache_key, response)
                logger.info("cache_store", path=request.url.path)

            return response

        except Exception as e:
            logger.exception("caching_error", error=str(e))
            return await call_next(request)

    def _get_cached_response(self, key: str) -> Optional[Response]:
        """Get a cached response if it exists."""
        return self._cache.get(key)

    def _cache_response(self, key: str, response: Response):
        """Cache a response."""
        self._cache[key] = response 