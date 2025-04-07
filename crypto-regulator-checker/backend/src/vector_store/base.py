"""Base class for vector stores."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from ..document_processing.chunking import TextChunk

@dataclass
class SearchResult:
    """A search result from the vector store."""
    chunk: TextChunk
    score: float

class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    def add_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[np.ndarray] = None
    ) -> None:
        """Add text to the vector store.
        
        Args:
            text: Text to add
            metadata: Optional metadata to associate with the text
            embedding: Optional pre-computed embedding
        """
        pass
    
    @abstractmethod
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[np.ndarray]] = None
    ) -> None:
        """Add multiple texts to the vector store.
        
        Args:
            texts: List of texts to add
            metadatas: Optional list of metadata dicts
            embeddings: Optional list of pre-computed embeddings
        """
        pass
    
    @abstractmethod
    def similarity_search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar texts using a query embedding.
        
        Args:
            query_embedding: Query embedding to search with
            k: Number of results to return
            min_score: Minimum similarity score to include
            filters: Optional metadata filters
            
        Returns:
            List of search results with similarity scores
        """
        pass
    
    @abstractmethod
    def get_embedding(self, text: str) -> np.ndarray:
        """Get the embedding for a text.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            Embedding vector
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all texts and embeddings from the store."""
        pass 