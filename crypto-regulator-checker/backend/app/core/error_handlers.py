from fastapi import Request
from fastapi.responses import JSONResponse
from .exceptions import BaseAppException
import logging

# Configure logging
logger = logging.getLogger(__name__)

async def app_exception_handler(request: Request, exc: BaseAppException):
    """Handle all application-specific exceptions."""
    logger.error(
        f"Application error: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details,
                "status_code": exc.status_code,
                "type": exc.__class__.__name__
            }
        }
    )

async def validation_exception_handler(request: Request, exc: Exception):
    """Handle validation errors."""
    logger.warning(
        "Validation error",
        extra={
            "errors": str(exc),
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation error",
                "details": {"errors": str(exc)},
                "status_code": 422,
                "type": "ValidationError"
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Handle any unhandled exceptions."""
    logger.error(
        f"Unhandled error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "details": {"error": str(exc)} if not isinstance(exc, Exception) else {},
                "status_code": 500,
                "type": "InternalServerError"
            }
        }
    ) 