"""Structured logging configuration and utilities."""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
import structlog
from pythonjsonlogger import jsonlogger

from .config import get_settings

settings = get_settings()

def setup_logging():
    """Configure structured logging for the application."""
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.logging.level.upper()),
        format="%(message)s",
        stream=sys.stdout,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set up JSON formatter if configured
    if settings.logging.format.lower() == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        for handler in logging.getLogger().handlers:
            handler.setFormatter(formatter)

def get_logger(name: str):
    """Get a structured logger instance.
    
    Args:
        name: Name for the logger, typically __name__
        
    Returns:
        A structured logger instance
    """
    return structlog.get_logger(name)

class RequestLogger:
    """Utility class for logging HTTP requests and responses."""
    
    def __init__(self, logger=None):
        self.logger = logger or get_logger(__name__)
    
    def log_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None
    ):
        """Log an HTTP request.
        
        Args:
            method: HTTP method
            path: Request path
            params: Query parameters
            headers: Request headers
            body: Request body
        """
        if not settings.logging.log_requests:
            return
            
        self.logger.info(
            "http_request",
            method=method,
            path=path,
            params=params,
            headers=self._sanitize_headers(headers),
            body=self._sanitize_body(body)
        )
    
    def log_response(
        self,
        status_code: int,
        path: str,
        response_time: float,
        body: Optional[Any] = None,
        error: Optional[Exception] = None
    ):
        """Log an HTTP response.
        
        Args:
            status_code: HTTP status code
            path: Request path
            response_time: Response time in seconds
            body: Response body
            error: Exception if any occurred
        """
        if not settings.logging.log_responses:
            return
            
        self.logger.info(
            "http_response",
            status_code=status_code,
            path=path,
            response_time=response_time,
            body=self._sanitize_body(body),
            error=str(error) if error else None
        )
    
    def _sanitize_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Remove sensitive information from headers."""
        if not headers:
            return {}
            
        sanitized = headers.copy()
        sensitive_headers = {"authorization", "cookie", "x-api-key"}
        
        for header in sensitive_headers:
            if header in sanitized:
                sanitized[header] = "[REDACTED]"
                
        return sanitized
    
    def _sanitize_body(self, body: Any) -> Any:
        """Remove sensitive information from request/response body."""
        if not body:
            return None
            
        if isinstance(body, (str, bytes)):
            try:
                body = json.loads(body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                return "[NON-JSON BODY]"
        
        if isinstance(body, dict):
            sanitized = body.copy()
            sensitive_fields = {"password", "token", "api_key", "secret"}
            
            for key in sensitive_fields:
                if key in sanitized:
                    sanitized[key] = "[REDACTED]"
                    
            return sanitized
            
        return body

class ServiceLogger:
    """Utility class for logging service operations."""
    
    def __init__(self, service_name: str, logger=None):
        self.service_name = service_name
        self.logger = logger or get_logger(service_name)
    
    def log_operation(
        self,
        operation: str,
        status: str = "success",
        duration: Optional[float] = None,
        error: Optional[Exception] = None,
        **kwargs
    ):
        """Log a service operation.
        
        Args:
            operation: Name of the operation
            status: Operation status (success/error)
            duration: Operation duration in seconds
            error: Exception if any occurred
            **kwargs: Additional context parameters
        """
        self.logger.info(
            f"{self.service_name}_{operation}",
            status=status,
            duration=duration,
            error=str(error) if error else None,
            **kwargs
        )

# Example usage:
# logger = get_logger(__name__)
# logger.info("processing_document", document_id="123", size_bytes=1024)
#
# request_logger = RequestLogger()
# request_logger.log_request("POST", "/api/v1/documents", body={"title": "test"})
#
# service_logger = ServiceLogger("embedding_service")
# service_logger.log_operation("generate_embeddings", duration=1.23, batch_size=32) 