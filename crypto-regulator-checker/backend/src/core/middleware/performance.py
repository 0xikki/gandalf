"""Performance monitoring middleware."""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

logger = structlog.get_logger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring request performance."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log performance metrics."""
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log performance metrics
        logger.info(
            "request_performance",
            method=request.method,
            path=request.url.path,
            process_time_ms=round(process_time * 1000, 2),
            status_code=response.status_code
        )
        
        return response 