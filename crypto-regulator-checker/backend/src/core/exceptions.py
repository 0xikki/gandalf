"""Custom exception classes and error handling utilities."""

from typing import Optional, Dict, Any
from http import HTTPStatus

class BaseError(Exception):
    """Base class for all custom exceptions."""
    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "status": self.status_code
            }
        }

class FileValidationError(BaseError):
    """Raised when file validation fails."""
    def __init__(self, message: str = "File validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
            error_code="FILE_VALIDATION_ERROR",
            details=details
        )

# Authentication and Authorization Errors
class AuthenticationError(BaseError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code="AUTH_ERROR",
            details=details
        )

class AuthorizationError(BaseError):
    """Raised when user lacks required permissions."""
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.FORBIDDEN,
            error_code="FORBIDDEN",
            details=details
        )

# Validation Errors
class ValidationError(BaseError):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )

# Resource Errors
class NotFoundError(BaseError):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.NOT_FOUND,
            error_code="NOT_FOUND",
            details=details
        )

class ConflictError(BaseError):
    """Raised when there's a conflict with existing resources."""
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.CONFLICT,
            error_code="CONFLICT",
            details=details
        )

# Service Errors
class ServiceError(BaseError):
    """Base class for service-specific errors."""
    def __init__(
        self,
        message: str,
        service_name: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        error_code = f"{service_name.upper()}_ERROR"
        super().__init__(message=message, status_code=status_code, error_code=error_code, details=details)

class EmbeddingError(ServiceError):
    """Raised when embedding generation fails."""
    def __init__(self, message: str = "Failed to generate embeddings", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, service_name="EMBEDDING", details=details)

class VectorStoreError(ServiceError):
    """Raised when vector store operations fail."""
    def __init__(self, message: str = "Vector store operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, service_name="VECTOR_STORE", details=details)

class LLMError(ServiceError):
    """Raised when LLM operations fail."""
    def __init__(self, message: str = "LLM operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, service_name="LLM", details=details)

class DocumentProcessingError(ServiceError):
    """Raised when document processing fails."""
    def __init__(self, message: str = "Document processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, service_name="DOCUMENT_PROCESSING", details=details)

# Rate Limiting Errors
class RateLimitError(BaseError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details
        )

# Cache Errors
class CacheError(ServiceError):
    """Raised when cache operations fail."""
    def __init__(self, message: str = "Cache operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, service_name="CACHE", details=details)

# Configuration Errors
class ConfigurationError(BaseError):
    """Raised when there's a configuration issue."""
    def __init__(self, message: str = "Configuration error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="CONFIG_ERROR",
            details=details
        ) 