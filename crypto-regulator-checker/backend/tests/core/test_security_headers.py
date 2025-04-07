from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_security_headers_present():
    """Test that all security headers are present in the response."""
    response = client.get("/health")
    assert response.status_code == 200
    
    # Content Security Policy
    assert "content-security-policy" in response.headers
    csp = response.headers["content-security-policy"]
    assert "default-src 'self'" in csp
    assert "script-src" in csp
    assert "style-src" in csp
    
    # MIME type sniffing protection
    assert response.headers["x-content-type-options"] == "nosniff"
    
    # Clickjacking protection
    assert response.headers["x-frame-options"] == "DENY"
    
    # XSS protection
    assert response.headers["x-xss-protection"] == "1; mode=block"
    
    # Referrer Policy
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    
    # Permissions Policy
    permissions = response.headers["permissions-policy"]
    assert "camera=()" in permissions
    assert "microphone=()" in permissions
    assert "payment=()" in permissions

def test_hsts_header():
    """Test that HSTS header is present only for HTTPS requests."""
    # Mock HTTPS request
    response = client.get("/health", headers={"X-Forwarded-Proto": "https"})
    assert "strict-transport-security" in response.headers
    assert "max-age=31536000" in response.headers["strict-transport-security"]
    
    # HTTP request should not have HSTS header
    response = client.get("/health")
    assert "strict-transport-security" not in response.headers

def test_csp_blocks_unsafe_resources():
    """Test that CSP blocks unsafe resources."""
    response = client.get("/health")
    csp = response.headers["content-security-policy"]
    
    # Check that unsafe sources are properly restricted
    assert "object-src 'none'" in csp
    assert "frame-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "media-src 'none'" in csp

def test_csp_allows_required_resources():
    """Test that CSP allows required resources."""
    response = client.get("/health")
    csp = response.headers["content-security-policy"]
    
    # Check that necessary sources are allowed
    assert "connect-src 'self' wss:" in csp  # WebSocket support
    assert "img-src 'self' data: https:" in csp  # Images
    assert "font-src 'self' data: https:" in csp  # Fonts

def test_permissions_policy():
    """Test that Permissions Policy is properly configured."""
    response = client.get("/health")
    permissions = response.headers["permissions-policy"]
    
    # Check that sensitive permissions are restricted
    required_restrictions = [
        "accelerometer=()",
        "camera=()",
        "geolocation=()",
        "gyroscope=()",
        "magnetometer=()",
        "microphone=()",
        "payment=()",
        "usb=()"
    ]
    
    for restriction in required_restrictions:
        assert restriction in permissions 