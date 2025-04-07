from typing import List, Optional
import asyncio
from sentence_transformers import SentenceTransformer
try:
    from pydantic.v1 import BaseModel  # For backwards compatibility
except ImportError:
    from pydantic import BaseModel

class EmbeddingConfig(BaseModel):
    model_name: str = "all-MiniLM-L6-v2"
    max_seq_length: int = 512
    normalize_embeddings: bool = True
    
    class Config:
        arbitrary_types_allowed = True  # Required for Pydantic v2

class EmbeddingsProvider:
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.model = SentenceTransformer(
            self.config.model_name,
            device="cpu"  # Can be changed to "cuda" if GPU is available
        )
        self.model.max_seq_length = self.config.max_seq_length
        
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts asynchronously
        
        Args:
            texts: List of text strings to generate embeddings for
            
        Returns:
            List of embeddings as float vectors
        """
        if not texts:
            return []
            
        # Run in thread pool since SentenceTransformer is not async
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(
                texts,
                normalize_embeddings=self.config.normalize_embeddings
            ).tolist()
        )
        
        return embeddings
        
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string
        
        Args:
            text: Text string to generate embedding for
            
        Returns:
            Embedding as float vector
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] 