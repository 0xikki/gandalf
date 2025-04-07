"""Retrieval system for finding relevant regulations based on queries."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from ..vector_store.base import VectorStore
from ..embeddings.provider import EmbeddingsProvider
from ..document_processing.chunking import TextChunk

@dataclass
class RetrievalConfig:
    """Configuration for the retrieval system."""
    top_k: int = 5  # Number of most relevant chunks to retrieve
    min_similarity: float = 0.6  # Minimum similarity score to consider
    rerank_results: bool = True  # Whether to rerank results based on additional criteria
    filter_duplicates: bool = True  # Whether to filter near-duplicate chunks
    duplicate_threshold: float = 0.95  # Similarity threshold for duplicate detection
    
    def __post_init__(self):
        """Validate configuration."""
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        if not 0 <= self.min_similarity <= 1:
            raise ValueError("min_similarity must be between 0 and 1")
        if not 0 <= self.duplicate_threshold <= 1:
            raise ValueError("duplicate_threshold must be between 0 and 1")

@dataclass
class RetrievedChunk:
    """A retrieved chunk with its similarity score and metadata."""
    chunk: TextChunk
    similarity: float
    rank: int

class RetrievalStrategy(ABC):
    """Abstract base class for retrieval strategies."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embeddings_provider: EmbeddingsProvider,
        config: Optional[RetrievalConfig] = None
    ):
        """Initialize the retrieval strategy.
        
        Args:
            vector_store: Vector store containing document embeddings
            embeddings_provider: Provider for generating query embeddings
            config: Optional retrieval configuration
        """
        self.vector_store = vector_store
        self.embeddings_provider = embeddings_provider
        self.config = config or RetrievalConfig()
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """Retrieve relevant chunks for a query.
        
        Args:
            query: The search query
            filters: Optional metadata filters
            
        Returns:
            List of retrieved chunks with similarity scores
        """
        pass
    
    def _filter_duplicates(
        self,
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """Filter near-duplicate chunks based on similarity.
        
        Args:
            chunks: List of chunks to filter
            
        Returns:
            Filtered list with duplicates removed
        """
        if not chunks:
            return chunks
            
        filtered = []
        seen_embeddings = []
        
        for chunk in chunks:
            # Get embedding for current chunk
            chunk_embedding = self.vector_store.get_embedding(chunk.chunk.text)
            # Normalize the embedding
            chunk_embedding = chunk_embedding / np.linalg.norm(chunk_embedding)
            
            # Check if this is too similar to any previously seen chunk
            is_duplicate = False
            for seen_embedding in seen_embeddings:
                # Calculate cosine similarity with normalized vectors
                similarity = np.dot(chunk_embedding, seen_embedding)
                if similarity > self.config.duplicate_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(chunk)
                seen_embeddings.append(chunk_embedding)
        
        return filtered

class SemanticRetrieval(RetrievalStrategy):
    """Semantic retrieval using vector similarity search."""
    
    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """Retrieve chunks using semantic similarity search.
        
        Args:
            query: The search query
            filters: Optional metadata filters
            
        Returns:
            List of retrieved chunks with similarity scores
        """
        # Generate query embedding
        query_embedding = await self.embeddings_provider.get_embeddings([query])
        query_embedding = query_embedding[0]  # Get first embedding
        
        # Search vector store
        results = self.vector_store.similarity_search(
            query_embedding,
            k=self.config.top_k * 2 if self.config.filter_duplicates else self.config.top_k,  # Get extra results only if filtering duplicates
            min_score=self.config.min_similarity,
            filters=filters
        )
        
        # Convert to RetrievedChunk objects
        chunks = [
            RetrievedChunk(
                chunk=result.chunk,
                similarity=result.score,
                rank=i + 1
            )
            for i, result in enumerate(results)
        ]
        
        # Filter duplicates if explicitly enabled
        if self.config.filter_duplicates:
            chunks = self._filter_duplicates(chunks)
            # Update ranks after filtering
            for i, chunk in enumerate(chunks):
                chunk.rank = i + 1
        
        # Rerank if enabled
        if self.config.rerank_results:
            chunks = self._rerank_results(chunks)
            # Update ranks after reranking
            for i, chunk in enumerate(chunks):
                chunk.rank = i + 1
        
        # Return top k after filtering/reranking
        return chunks[:self.config.top_k]
    
    def _rerank_results(
        self,
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """Rerank results based on additional criteria.
        
        Args:
            chunks: List of chunks to rerank
            
        Returns:
            Reranked list of chunks
        """
        # TODO: Implement more sophisticated reranking
        # For now, just sort by similarity score
        reranked = sorted(
            chunks,
            key=lambda x: x.similarity,
            reverse=True
        )
        
        # Update ranks
        for i, chunk in enumerate(reranked):
            chunk.rank = i + 1
        
        return reranked

class HybridRetrieval(RetrievalStrategy):
    """Hybrid retrieval combining semantic and keyword search."""
    
    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedChunk]:
        """Retrieve chunks using both semantic and keyword search.
        
        Args:
            query: The search query
            filters: Optional metadata filters
            
        Returns:
            List of retrieved chunks with similarity scores
        """
        # TODO: Implement hybrid search combining:
        # - Semantic similarity (vector search)
        # - Keyword matching (BM25 or similar)
        # - Named entity overlap
        # - Document structure/hierarchy
        raise NotImplementedError("Hybrid retrieval not yet implemented") 