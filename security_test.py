"""Security testing script for Crypto Regulator Checker."""
import asyncio
import logging
import httpx
import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityTester:
    """Security testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """Initialize security tester."""
        self.base_url = base_url
        self.test_user = {
            "email": "security_test@example.com",
            "password": "SecurePass123!",
            "full_name": "Security Tester"
        }
        
    async def setup(self) -> None:
        """Setup test environment."""
        async with httpx.AsyncClient() as client:
            try:
                # Register test user
                response = await client.post(
                    f"{self.base_url}/api/auth/register",
                    json=self.test_user
                )
                if response.status_code == 201:
                    logger.info("Test user created successfully")
                elif response.status_code == 400:
                    logger.info("Test user already exists")
                else:
                    logger.error(f"Failed to create test user: {response.text}")
                    
            except Exception as e:
                logger.error(f"Setup failed: {str(e)}")
                raise
    
    async def test_auth_security(self) -> Dict[str, Any]:
        """Test authentication security."""
        results = {
            "invalid_token": False,
            "expired_token": False,
            "missing_auth": False,
            "tampered_token": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Get valid token first
                response = await client.post(
                    f"{self.base_url}/api/auth/login",
                    data={
                        "username": self.test_user["email"],
                        "password": self.test_user["password"]
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                valid_token = response.json()["access_token"]
                
                # Test invalid token
                response = await client.get(
                    f"{self.base_url}/api/documents/1/analysis",
                    headers={"Authorization": "Bearer invalid_token"}
                )
                results["invalid_token"] = response.status_code == 401
                
                # Test expired token
                expired_payload = jwt.decode(valid_token, options={"verify_signature": False})
                expired_payload["exp"] = datetime.utcnow() - timedelta(hours=1)
                expired_token = jwt.encode(expired_payload, "invalid_key", algorithm="HS256")
                response = await client.get(
                    f"{self.base_url}/api/documents/1/analysis",
                    headers={"Authorization": f"Bearer {expired_token}"}
                )
                results["expired_token"] = response.status_code == 401
                
                # Test missing auth header
                response = await client.get(f"{self.base_url}/api/documents/1/analysis")
                results["missing_auth"] = response.status_code == 401
                
                # Test tampered token payload
                tampered_payload = jwt.decode(valid_token, options={"verify_signature": False})
                tampered_payload["sub"] = "hacker"
                tampered_token = jwt.encode(tampered_payload, "invalid_key", algorithm="HS256")
                response = await client.get(
                    f"{self.base_url}/api/documents/1/analysis",
                    headers={"Authorization": f"Bearer {tampered_token}"}
                )
                results["tampered_token"] = response.status_code == 401
                
                return results
                
            except Exception as e:
                logger.error(f"Auth security test failed: {str(e)}")
                raise
    
    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting."""
        results = {
            "rapid_requests": False,
            "rate_limit_headers": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Test rapid requests
                responses = []
                
                # Send requests in rapid succession
                for _ in range(5):
                    # Send 10 requests at once
                    batch_responses = await asyncio.gather(*[
                        client.get(f"{self.base_url}/health")
                        for _ in range(10)
                    ])
                    responses.extend(batch_responses)
                    # Wait a very short time to simulate rapid but not instant requests
                    await asyncio.sleep(0.1)
                
                # Check if any requests were rate limited
                rate_limited = any(r.status_code == 429 for r in responses)
                results["rapid_requests"] = rate_limited
                
                # Check rate limit headers
                results["rate_limit_headers"] = all(
                    "X-RateLimit-Limit" in r.headers and
                    "X-RateLimit-Remaining" in r.headers and
                    "X-RateLimit-Reset" in r.headers
                    for r in valid_responses
                ) if valid_responses else False
                
                return results
                
            except Exception as e:
                logger.error(f"Rate limit test failed: {str(e)}")
                raise
    
    async def test_file_upload_security(self) -> Dict[str, Any]:
        """Test file upload security."""
        results = {
            "size_limit": False,
            "type_validation": False,
            "malicious_content": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Login to get token
                response = await client.post(
                    f"{self.base_url}/api/auth/login",
                    data={
                        "username": self.test_user["email"],
                        "password": self.test_user["password"]
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                token = response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Test file size limit
                large_file = b"0" * (30 * 1024 * 1024)  # 30MB file
                files = {"file": ("large.txt", large_file)}
                response = await client.post(
                    f"{self.base_url}/api/documents/upload",
                    headers=headers,
                    files=files
                )
                results["size_limit"] = response.status_code == 413
                
                # Test file type validation
                files = {"file": ("malicious.exe", b"fake executable content")}
                response = await client.post(
                    f"{self.base_url}/api/documents/upload",
                    headers=headers,
                    files=files
                )
                results["type_validation"] = response.status_code == 400
                
                # Test malicious content detection
                files = {"file": ("script.txt", b"<script>alert('xss')</script>")}
                response = await client.post(
                    f"{self.base_url}/api/documents/upload",
                    headers=headers,
                    files=files
                )
                results["malicious_content"] = response.status_code == 400
                
                return results
                
            except Exception as e:
                logger.error(f"File upload security test failed: {str(e)}")
                raise

async def main():
    """Run security tests."""
    logger.info("Starting security tests...")
    
    tester = SecurityTester()
    await tester.setup()
    
    # Run auth security tests
    logger.info("Testing authentication security...")
    auth_results = await tester.test_auth_security()
    logger.info(f"Auth security results: {auth_results}")
    
    # Run rate limiting tests
    logger.info("Testing rate limiting...")
    rate_limit_results = await tester.test_rate_limiting()
    logger.info(f"Rate limit results: {rate_limit_results}")
    
    # Run file upload security tests
    logger.info("Testing file upload security...")
    upload_results = await tester.test_file_upload_security()
    logger.info(f"File upload security results: {upload_results}")
    
    logger.info("Security tests completed")

if __name__ == "__main__":
    asyncio.run(main()) 