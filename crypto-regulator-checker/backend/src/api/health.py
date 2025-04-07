"""Health check endpoints."""
import os
import psutil
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, Response
from pydantic import BaseModel
from src.core.config import settings

router = APIRouter(tags=["health"])

class ServiceStatus(BaseModel):
    """Service status model."""
    status: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str
    environment: str
    system: Dict[str, float]

def get_system_metrics() -> Dict[str, float]:
    """Get system metrics."""
    return {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent
    }

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the service",
    response_description="The health status of the service"
)
async def health_check(response: Response):
    """
    Basic health check endpoint that verifies:
    - Service status
    - System metrics
    """
    # Get system metrics
    metrics = get_system_metrics()
    
    # Simple health check - service is healthy if we can get metrics
    is_healthy = True
    
    # Set response status code
    response.status_code = 200 if is_healthy else 503
    
    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.VERSION,
        environment=settings.env,
        system=metrics
    )

@router.get(
    "/ping",
    summary="Simple Ping",
    description="Simple endpoint to verify the service is responding",
    response_description="A simple OK response"
)
async def ping():
    """Simple ping endpoint for basic health verification."""
    return {"status": "ok"} 