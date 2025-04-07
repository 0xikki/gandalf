"""Performance profiling script."""
import cProfile
import pstats
import io
import asyncio
import httpx
import logging
import tracemalloc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data
register_data = {
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
}

login_data = {
    "username": "test@example.com",
    "password": "testpassword123"
}

async def test_document_processing():
    """Test document processing performance."""
    async with httpx.AsyncClient() as client:
        try:
            # Register a new user
            response = await client.post(
                "http://localhost:8000/api/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "testpass",
                    "full_name": "Test User"
                },
            )
            if response.status_code == 201:
                logger.info("User registered successfully")
            else:
                logger.info(f"User registration failed (might already exist): {response.text}")
            
            # Login with the registered user
            response = await client.post(
                "http://localhost:8000/api/auth/login",
                data={"username": "test@example.com", "password": "testpass"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            access_token = response.json()["access_token"]
            
            # Upload document
            headers = {"Authorization": f"Bearer {access_token}"}
            files = {"file": ("test.txt", "Test content for document processing.")}
            response = await client.post("http://localhost:8000/api/documents/upload", headers=headers, files=files)
            response.raise_for_status()
            document_id = response.json()["document_id"]
            
            # Get document analysis
            response = await client.get(f"http://localhost:8000/api/documents/{document_id}/analysis", headers=headers)
            response.raise_for_status()
            
            logger.info("Test completed successfully")
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            raise

def main():
    """Main function to run performance tests."""
    logger.info("Starting performance test...")
    
    # Start memory tracing
    tracemalloc.start()
    
    # Run the test with profiling
    profiler = cProfile.Profile()
    profiler.enable()
    
    try:
        asyncio.run(test_document_processing())
    finally:
        profiler.disable()
        
        # Print CPU profiling results
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        stats.print_stats(20)  # Show top 20 functions
        print("\nCPU Profiling Results:")
        print(s.getvalue())
        
        # Print memory usage
        current, peak = tracemalloc.get_traced_memory()
        print(f"\nMemory Usage:")
        print(f"Current: {current / 10**6:.1f} MB")
        print(f"Peak: {peak / 10**6:.1f} MB")
        
        tracemalloc.stop()

if __name__ == '__main__':
    main() 