from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class BaseAppException(Exception):
    """Base exception for all application exceptions."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DocumentNotFoundError(BaseAppException):
    """Raised when a document is not found."""
    def __init__(self, document_id: int):
        super().__init__(
            message=f"Document with ID {document_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"document_id": document_id}
        )

class ValidationError(BaseAppException):
    """Raised when validation fails."""
    def __init__(self, message: str, errors: Dict[str, Any]):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"validation_errors": errors}
        )

class FileProcessingError(BaseAppException):
    """Raised when file processing fails."""
    def __init__(self, filename: str, reason: str):
        super().__init__(
            message=f"Failed to process file {filename}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"filename": filename, "reason": reason}
        )

class DatabaseError(BaseAppException):
    """Raised when database operations fail."""
    def __init__(self, operation: str, details: Dict[str, Any]):
        super().__init__(
            message=f"Database operation '{operation}' failed",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

class AuthenticationError(BaseAppException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationError(BaseAppException):
    """Raised when user lacks required permissions."""
    def __init__(self, resource: str, action: str):
        super().__init__(
            message=f"Not authorized to {action} {resource}",
            status_code=status.HTTP_403_FORBIDDEN,
            details={"resource": resource, "action": action}
        )

class RateLimitError(BaseAppException):
    """Raised when rate limit is exceeded."""
    def __init__(self, limit: int, reset_after: int):
        super().__init__(
            message="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"limit": limit, "reset_after": reset_after}
        ) 