"""Sentence transformer embeddings provider."""

import asyncio
import numpy as np
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer

from ..config import EmbeddingsConfig

class SentenceTransformerProvider:
    """Sentence transformer embeddings provider."""

    def __init__(
        self,
        config: Optional[EmbeddingsConfig] = None,
        executor: Optional[ThreadPoolExecutor] = None
    ):
        """Initialize the provider.
        
        Args:
            config (Optional[EmbeddingsConfig], optional): Provider configuration. Defaults to None.
            executor (Optional[ThreadPoolExecutor], optional): Thread pool executor. Defaults to None.
        """
        self.config = config or EmbeddingsConfig()
        self.executor = executor or ThreadPoolExecutor(max_workers=1)
        self.model = SentenceTransformer(self.config.model_name, device=self.config.device)
        self.model.max_seq_length = self.config.max_seq_length

    def generate_embeddings_sync(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings synchronously.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
        
        Returns:
            List[List[float]]: List of embedding vectors

        Raises:
            Exception: If texts is empty or embeddings generation fails
        """
        if not texts:
            raise Exception("Failed to generate embeddings: empty input")

        try:
            # Generate embeddings in batches
            embeddings = []
            for i in range(0, len(texts), self.config.batch_size):
                batch = texts[i:i + self.config.batch_size]
                batch_embeddings = self.model.encode(
                    batch,
                    normalize_embeddings=self.config.normalize_embeddings
                )
                embeddings.extend(batch_embeddings.tolist())
            return embeddings

        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {str(e)}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings asynchronously.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
        
        Returns:
            List[List[float]]: List of embedding vectors
        """
        try:
            # Use thread pool to run sync method asynchronously
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                self.generate_embeddings_sync,
                texts
            )

        except Exception as e:
            raise Exception(f"Failed to generate embeddings asynchronously: {str(e)}")

    def __len__(self) -> int:
        """Get the embedding dimension.
        
        Returns:
            int: Embedding dimension
        """
        return self.model.get_sentence_embedding_dimension() 