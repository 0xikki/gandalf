import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config.cors import CORSSettings, settings

client = TestClient(app)

def test_cors_allowed_origin():
    """Test that CORS allows configured origins."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

def test_cors_allowed_methods():
    """Test that CORS allows configured methods."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        }
    )
    assert response.status_code == 200
    assert "POST" in response.headers["access-control-allow-methods"]

def test_cors_allowed_headers():
    """Test that CORS allows configured headers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type, Authorization",
        }
    )
    assert response.status_code == 200
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert "authorization" in response.headers["access-control-allow-headers"].lower()

def test_cors_exposed_headers():
    """Test that CORS exposes configured headers."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    exposed_headers = response.headers["access-control-expose-headers"].lower()
    assert "x-ratelimit-limit" in exposed_headers
    assert "x-ratelimit-remaining" in exposed_headers

def test_cors_credentials():
    """Test that CORS allows credentials."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"

def test_cors_max_age():
    """Test that CORS preflight response includes max age."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert "access-control-max-age" in response.headers

def test_cors_disallowed_origin():
    """Test that CORS blocks unauthorized origins."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers

@pytest.mark.skipif(settings.ENVIRONMENT != "production", reason="Production-only test")
def test_cors_production_origins():
    """Test that CORS settings are properly configured for production."""
    cors_settings = CORSSettings()
    assert all(not origin.startswith("http://localhost") 
              for origin in cors_settings.ALLOWED_ORIGINS)
    assert len(cors_settings.ALLOWED_ORIGINS) > 0 