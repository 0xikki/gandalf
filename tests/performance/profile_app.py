"""Performance profiling for the application."""
import cProfile
import pstats
import io
from memory_profiler import profile
import asyncio
import httpx
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """Class to handle performance profiling of the application."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the profiler."""
        self.base_url = base_url
        self.profile_dir = Path("profile_results")
        self.profile_dir.mkdir(exist_ok=True)
        
    def _get_timestamp(self) -> str:
        """Get formatted timestamp for filenames."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @profile
    async def profile_document_processing(self):
        """Profile document processing performance."""
        async with httpx.AsyncClient() as client:
            # Login to get token
            login_data = {
                "email": "test@example.com",
                "password": "test-password"
            }
            response = await client.post(f"{self.base_url}/api/auth/login", json=login_data)
            token = response.json()["access_token"]
            
            # Create test document
            test_content = "Test content for performance profiling." * 1000  # 31KB of text
            files = {"file": ("test.txt", test_content.encode(), "text/plain")}
            headers = {"Authorization": f"Bearer {token}"}
            
            # Profile document upload and processing
            response = await client.post(
                f"{self.base_url}/api/documents/upload",
                files=files,
                headers=headers
            )
            document_id = response.json()["document_id"]
            
            # Profile document retrieval
            await client.get(f"{self.base_url}/api/documents/{document_id}", headers=headers)
    
    def run_cpu_profile(self):
        """Run CPU profiling on document processing."""
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Run the async function
        asyncio.run(self.profile_document_processing())
        
        profiler.disable()
        
        # Save results
        timestamp = self._get_timestamp()
        stats_file = self.profile_dir / f"cpu_profile_{timestamp}.stats"
        
        # Save detailed stats
        stats = pstats.Stats(profiler)
        stats.dump_stats(str(stats_file))
        
        # Generate readable report
        report_file = self.profile_dir / f"cpu_profile_{timestamp}.txt"
        s = io.StringIO()
        stats = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        stats.print_stats()
        
        with open(report_file, "w") as f:
            f.write(s.getvalue())
        
        logger.info(f"CPU profile saved to {stats_file} and {report_file}")
    
    def run_memory_profile(self):
        """Run memory profiling on document processing."""
        timestamp = self._get_timestamp()
        output_file = self.profile_dir / f"memory_profile_{timestamp}.txt"
        
        # memory_profiler will log to the file due to @profile decorator
        with open(output_file, "w") as f:
            asyncio.run(self.profile_document_processing())
        
        logger.info(f"Memory profile saved to {output_file}")

def main():
    """Run performance profiling."""
    profiler = PerformanceProfiler()
    
    logger.info("Starting CPU profiling...")
    profiler.run_cpu_profile()
    
    logger.info("Starting memory profiling...")
    profiler.run_memory_profile()
    
    logger.info("Performance profiling completed.")

if __name__ == "__main__":
    main() 