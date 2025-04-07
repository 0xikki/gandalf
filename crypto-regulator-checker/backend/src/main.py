"""Main application module."""
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime
import time

from src.core.config import settings
from src.core.logging import setup_logging
from src.core.exceptions import FileValidationError
from src.api import health, documents, auth
from src.core.database import Base, engine, get_db
from src.core.middleware.performance import PerformanceMiddleware
from src.core.middleware.caching import CachingMiddleware
from src.api.websocket import websocket_endpoint

# Import all models to ensure they are registered with SQLAlchemy
from src.models.user import User
from src.models.document import Document
from src.models.analysis_result import AnalysisResult

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize rate limiter with in-memory storage and strict limits
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1/second"],
    headers_enabled=True,
    storage_options={"storage_class": "slowapi.storage.MemoryStorage"}
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging()

# Add performance monitoring
app.add_middleware(PerformanceMiddleware)

# Add caching middleware
app.add_middleware(CachingMiddleware)

# Add file size limit middleware
@app.middleware("http")
async def check_file_size(request: Request, call_next):
    """Check file size before processing."""
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_UPLOAD_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    "status": "error",
                    "message": f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE/1024/1024}MB"
                }
            )
    return await call_next(request)

# Add rate limit headers middleware
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    """Add rate limit headers to all responses."""
    response = await call_next(request)
    
    # Get rate limit info from limiter
    rate_limit = getattr(request.state, "rate_limit", None)
    if rate_limit:
        window_stats = rate_limit.get_window_stats()
        response.headers["X-RateLimit-Limit"] = str(rate_limit.limit)
        response.headers["X-RateLimit-Remaining"] = str(window_stats["remaining"])
        response.headers["X-RateLimit-Reset"] = str(window_stats["reset"])
    else:
        # Default headers if no rate limit info
        response.headers["X-RateLimit-Limit"] = "1"
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 1))
    
    # Add rate limit headers to 429 responses
    if response.status_code == 429:
        response.headers["X-RateLimit-Limit"] = "1"
        response.headers["X-RateLimit-Remaining"] = "0"
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 1))
    
    return response

# Configuration
class Config:
    # Base directory is the backend folder
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Upload directory structure
    UPLOAD_DIR = BASE_DIR / 'uploads'
    UPLOAD_DIR_TEMP = UPLOAD_DIR / 'temp'  # For temporary storage during processing
    UPLOAD_DIR_PROCESSED = UPLOAD_DIR / 'processed'  # For successfully processed files
    
    # Ensure all upload directories exist
    UPLOAD_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR_TEMP.mkdir(exist_ok=True)
    UPLOAD_DIR_PROCESSED.mkdir(exist_ok=True)
    
    # File upload settings
    MAX_CONTENT_LENGTH = settings.MAX_UPLOAD_SIZE
    ALLOWED_EXTENSIONS = settings.ALLOWED_FILE_EXTENSIONS

# Exception handlers
@app.exception_handler(FileValidationError)
async def file_validation_exception_handler(request: Request, exc: FileValidationError):
    return JSONResponse(
        status_code=400,
        content={
            'status': 'error',
            'message': str(exc)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            'status': 'error',
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while processing your request. Please try again later.',
            'request_id': str(uuid.uuid4())  # For tracking issues in logs
        }
    )

# Include routers with API prefix
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)

@app.websocket("/ws/{document_id}")
async def websocket_route(websocket: WebSocket, document_id: int):
    """WebSocket endpoint for real-time document updates."""
    await websocket_endpoint(websocket, document_id, get_db())

@app.get("/health")
@limiter.limit("1/second")  # Very strict rate limit for testing
async def health_check(request: Request):
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/")
@limiter.limit("5/minute")
async def root(request: Request):
    """Root endpoint."""
    return {"message": "Welcome to Crypto Regulator Checker API"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 