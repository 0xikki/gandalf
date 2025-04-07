import pytest
from src.core.security import verify_password, get_password_hash, create_access_token, decode_token, verify_token

def test_password_hashing():
    """Test password hashing and verification."""
    password = "test-password"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)

def test_token_creation_and_verification():
    """Test JWT token creation and verification."""
    user_id = "test-user"
    token = create_access_token({"sub": user_id})
    assert token is not None
    
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded.get("sub") == user_id
    
    assert verify_token(token)

def test_invalid_token():
    """Test invalid token handling."""
    with pytest.raises(Exception):
        verify_token("invalid-token")
        
def test_expired_token():
    """Test expired token handling."""
    import time
    from datetime import timedelta
    
    token = create_access_token({"sub": "test-user"}, expires_delta=timedelta(seconds=1))
    time.sleep(2)  # Wait for token to expire
    
    with pytest.raises(Exception):
        verify_token(token) 