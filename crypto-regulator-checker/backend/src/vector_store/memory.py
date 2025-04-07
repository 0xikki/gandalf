"""In-memory vector store implementation."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass, field

from .base import VectorStore, SearchResult
from ..document_processing.chunking import TextChunk
from ..embeddings.provider import EmbeddingsProvider

@dataclass
class MemoryVectorStore(VectorStore):
    """In-memory vector store using NumPy arrays."""
    
    embeddings_provider: EmbeddingsProvider
    texts: List[str] = field(default_factory=list)
    embeddings: List[np.ndarray] = field(default_factory=list)
    metadatas: List[Dict[str, Any]] = field(default_factory=list)
    
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
        if embedding is None:
            embedding = self.embeddings_provider.get_embeddings_sync([text])[0]
        
        self.texts.append(text)
        self.embeddings.append(embedding)
        self.metadatas.append(metadata or {})
    
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
        if embeddings is None:
            embeddings = self.embeddings_provider.get_embeddings_sync(texts)
        
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        self.texts.extend(texts)
        self.embeddings.extend(embeddings)
        self.metadatas.extend(metadatas)
    
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
        if not self.embeddings:
            return []
        
        # Convert list of embeddings to numpy array for efficient computation
        embeddings_array = np.array(self.embeddings)
        
        # Compute cosine similarities
        similarities = np.dot(embeddings_array, query_embedding)
        
        # Create list of (index, similarity) tuples
        results: List[Tuple[int, float]] = []
        for i, similarity in enumerate(similarities):
            # Apply metadata filters if provided
            if filters:
                metadata = self.metadatas[i]
                if not all(metadata.get(k) == v for k, v in filters.items()):
                    continue
            
            # Only include results above minimum score
            if similarity >= min_score:
                results.append((i, float(similarity)))
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Take top k results
        results = results[:k]
        
        # Convert to SearchResult objects
        search_results = []
        for i, (idx, score) in enumerate(results):
            chunk = TextChunk(
                text=self.texts[idx],
                metadata=self.metadatas[idx],
                start_char=0,  # Not tracking original positions in memory store
                end_char=len(self.texts[idx]),
                chunk_index=i
            )
            search_results.append(SearchResult(chunk=chunk, score=score))
        
        return search_results
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get the embedding for a text.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            Embedding vector
        """
        return self.embeddings_provider.get_embeddings_sync([text])[0]
    
    def clear(self) -> None:
        """Clear all texts and embeddings from the store."""
        self.texts.clear()
        self.embeddings.clear()
        self.metadatas.clear() 