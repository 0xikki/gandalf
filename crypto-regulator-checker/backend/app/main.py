from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware.rate_limit import RateLimitMiddleware
from app.core.middleware.security import SecurityHeadersMiddleware
from app.core.config.cors import cors_settings
from app.api.endpoints import documents

app = FastAPI(
    title="Crypto Regulator Checker",
    description="API for checking cryptocurrency regulatory compliance",
    version="1.0.0"
)

# Configure security headers
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS with secure settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_settings.ALLOWED_ORIGINS,
    allow_credentials=cors_settings.ALLOW_CREDENTIALS,
    allow_methods=cors_settings.ALLOWED_METHODS,
    allow_headers=cors_settings.ALLOWED_HEADERS,
    expose_headers=cors_settings.EXPOSED_HEADERS,
    max_age=cors_settings.MAX_AGE
)

# Configure rate limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_limit=10,
    exclude_paths=["/docs", "/redoc", "/openapi.json", "/health"]
)

# Include routers
app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["documents"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 