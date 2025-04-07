import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.middleware.rate_limit import RateLimitMiddleware
import time

app = FastAPI()
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=5,
    burst_limit=3,
    exclude_paths=["/health"]
)

@app.get("/test")
async def test_endpoint():
    return {"message": "success"}

@app.get("/health")
async def health_endpoint():
    return {"status": "healthy"}

client = TestClient(app)

def test_basic_rate_limiting():
    """Test that basic rate limiting works."""
    # First 3 requests should succeed (burst limit)
    for _ in range(3):
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers
    
    # Fourth request should fail
    response = client.get("/test")
    assert response.status_code == 429
    assert "retry_after" in response.json()

def test_rate_limit_headers():
    """Test that rate limit headers are present and correct."""
    response = client.get("/test")
    assert response.status_code == 200
    
    headers = response.headers
    assert "X-RateLimit-Limit" in headers
    assert "X-RateLimit-Remaining" in headers
    assert "X-RateLimit-Reset" in headers
    
    assert int(headers["X-RateLimit-Limit"]) == 5
    assert int(headers["X-RateLimit-Remaining"]) >= 0
    assert int(headers["X-RateLimit-Reset"]) > 0

def test_excluded_paths():
    """Test that excluded paths bypass rate limiting."""
    # Make many requests to excluded path
    for _ in range(10):
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" not in response.headers

def test_rate_limit_reset():
    """Test that rate limits reset after the specified time."""
    # Use up the burst limit
    for _ in range(3):
        client.get("/test")
    
    # Wait for reset (in test we'll wait just a bit)
    time.sleep(1)
    
    # Should be able to make another request
    response = client.get("/test")
    assert response.status_code == 200

def test_different_ips():
    """Test that rate limits are applied per IP."""
    # First IP
    for _ in range(3):
        response = client.get("/test", headers={"X-Forwarded-For": "1.1.1.1"})
        assert response.status_code == 200
    
    response = client.get("/test", headers={"X-Forwarded-For": "1.1.1.1"})
    assert response.status_code == 429
    
    # Second IP should still have full quota
    for _ in range(3):
        response = client.get("/test", headers={"X-Forwarded-For": "2.2.2.2"})
        assert response.status_code == 200

def test_burst_limit():
    """Test that burst limit is enforced."""
    # Send requests as fast as possible
    for _ in range(3):
        response = client.get("/test")
        assert response.status_code == 200
    
    # Next request should fail due to burst limit
    response = client.get("/test")
    assert response.status_code == 429
    
    error_data = response.json()
    assert "detail" in error_data
    assert "retry_after" in error_data
    assert error_data["detail"] == "Too many requests" 