"""Embeddings provider module for generating text embeddings."""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor

@dataclass
class EmbeddingsConfig:
    """Configuration for embeddings generation."""
    model_name: str = "all-MiniLM-L6-v2"  # Default model
    normalize_embeddings: bool = True  # Whether to normalize embeddings
    max_seq_length: int = 512  # Maximum sequence length
    batch_size: int = 32  # Batch size for processing
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.model_name:
            raise ValueError("Model name must not be empty")
        if self.max_seq_length <= 0:
            raise ValueError("Maximum sequence length must be positive")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")

class EmbeddingsProvider(ABC):
    """Abstract base class for embeddings providers."""
    
    @abstractmethod
    def get_embeddings_sync(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for texts synchronously.
        
        Args:
            texts: List of texts to get embeddings for
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for texts asynchronously.
        
        Args:
            texts: List of texts to get embeddings for
            
        Returns:
            List of embedding vectors
        """
        pass

class SentenceTransformerProvider(EmbeddingsProvider):
    """Embeddings provider using SentenceTransformers."""
    
    def __init__(
        self,
        config: Optional[EmbeddingsConfig] = None,
        executor: Optional[ThreadPoolExecutor] = None
    ):
        """Initialize the provider.
        
        Args:
            config: Optional embeddings configuration
            executor: Optional thread pool executor for async operations
        """
        self.config = config or EmbeddingsConfig()
        self.model = SentenceTransformer(self.config.model_name)
        self.executor = executor or ThreadPoolExecutor(max_workers=4)
    
    def get_embeddings_sync(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for texts synchronously.
        
        Args:
            texts: List of texts to get embeddings for
            
        Returns:
            List of embedding vectors
        """
        # Generate embeddings in batches
        embeddings = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]
            batch_embeddings = self.model.encode(
                batch,
                normalize_embeddings=self.config.normalize_embeddings,
                max_seq_length=self.config.max_seq_length,
                show_progress_bar=False
            )
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for texts asynchronously.
        
        Args:
            texts: List of texts to get embeddings for
            
        Returns:
            List of embedding vectors
        """
        # Run embedding generation in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.get_embeddings_sync,
            texts
        ) 