from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(
        self,
        app: ASGIApp,
        *,
        content_security_policy: str | None = None,
        **kwargs
    ):
        """Initialize the middleware with optional custom CSP."""
        super().__init__(app)
        self.content_security_policy = content_security_policy or self._default_csp()
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.content_security_policy
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Clickjacking protection
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (only in production)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        
        return response
    
    def _default_csp(self) -> str:
        """
        Generate default Content Security Policy.
        Customize this based on your application's needs.
        """
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Adjust based on needs
            "style-src 'self' 'unsafe-inline'; "  # Adjust based on needs
            "img-src 'self' data: https:; "
            "font-src 'self' data: https:; "
            "connect-src 'self' wss:; "  # Allow WebSocket connections
            "media-src 'none'; "
            "object-src 'none'; "
            "frame-src 'none'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "upgrade-insecure-requests"
        ) 