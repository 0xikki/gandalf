import os
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import numpy as np
from .base_store import BaseVectorStore, VectorStoreConfig, VectorSearchResult

class MemoryStore(BaseVectorStore):
    """Simple in-memory implementation of vector store using NumPy."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize the in-memory store.
        
        Args:
            config (VectorStoreConfig): Store configuration
        """
        super().__init__(config)
        self._texts: Dict[str, str] = {}
        self._embeddings: Dict[str, np.ndarray] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def _validate_config(self) -> None:
        """Validate the store configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.collection_name:
            raise ValueError("Collection name is required")
        
        if self.config.embedding_dimension <= 0:
            raise ValueError("Embedding dimension must be positive")
    
    async def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add texts and their embeddings to the store.
        
        Args:
            texts (List[str]): The texts to add
            embeddings (List[List[float]]): The embeddings for each text
            metadata (Optional[List[Dict[str, Any]]], optional): Optional metadata for each text. Defaults to None.
            ids (Optional[List[str]], optional): Optional IDs for each text. Defaults to None.
        
        Returns:
            List[str]: The IDs of the added texts
        """
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid4()) for _ in range(len(texts))]
            
            # Normalize embeddings and store data
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                id = ids[i]
                embedding_array = np.array(embedding, dtype=np.float64)
                norm = np.linalg.norm(embedding_array)
                if norm > 0:  # Avoid division by zero
                    embedding_array = embedding_array / norm
                
                self._texts[id] = text
                self._embeddings[id] = embedding_array
                if metadata and i < len(metadata):
                    self._metadata[id] = metadata[i]
                else:
                    self._metadata[id] = {}
            
            return ids
            
        except Exception as e:
            raise Exception(f"Failed to add texts to memory store: {str(e)}")
    
    async def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar texts using an embedding.

        Args:
            query_embedding (List[float]): The query embedding to search with
            k (int, optional): Number of results to return. Defaults to 5.
            filter_metadata (Optional[Dict[str, Any]], optional): Metadata filter. Defaults to None.

        Returns:
            List[VectorSearchResult]: List of search results
        """
        try:
            # Normalize query embedding
            query_array = np.array(query_embedding, dtype=np.float64)
            query_array = query_array / np.linalg.norm(query_array)
            
            # Calculate distances for all embeddings
            results = []
            for id in self._embeddings:
                # Apply metadata filter if provided
                if filter_metadata:
                    metadata = self._metadata.get(id, {})
                    if not all(metadata.get(k) == v for k, v in filter_metadata.items()):
                        continue
                
                # Calculate cosine distance
                if self.config.distance_metric == "cosine":
                    score = 1 - np.dot(query_array, self._embeddings[id])
                elif self.config.distance_metric == "euclidean":
                    score = np.linalg.norm(query_array - self._embeddings[id])
                else:  # dot product
                    score = -np.dot(query_array, self._embeddings[id])  # Negative to sort ascending
                
                results.append(VectorSearchResult(
                    id=id,
                    text=self._texts[id],
                    metadata=self._metadata[id],
                    score=float(score),
                    embedding=self._embeddings[id].tolist(),
                    timestamp=datetime.now()
                ))
            
            # Sort by score and return top k
            results.sort(key=lambda x: x.score)
            return results[:k]

        except Exception as e:
            raise Exception(f"Failed to search in memory store: {str(e)}")
    
    async def delete(self, ids: List[str]) -> bool:
        """Delete texts by their IDs.
        
        Args:
            ids (List[str]): The IDs to delete
        
        Returns:
            bool: True if deletion was successful
        """
        try:
            for id in ids:
                self._texts.pop(id, None)
                self._embeddings.pop(id, None)
                self._metadata.pop(id, None)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete from memory store: {str(e)}")
    
    async def get_by_id(self, id: str) -> Optional[VectorSearchResult]:
        """Get a text by its ID.
        
        Args:
            id (str): The ID to retrieve
        
        Returns:
            Optional[VectorSearchResult]: The result if found
        """
        try:
            if id not in self._texts:
                return None
                
            return VectorSearchResult(
                id=id,
                text=self._texts[id],
                metadata=self._metadata.get(id, {}),
                score=0.0,  # No score for direct retrieval
                embedding=self._embeddings[id].tolist(),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Failed to get text from memory store: {str(e)}")
    
    async def clear(self) -> bool:
        """Clear all texts from the store.
        
        Returns:
            bool: True if clearing was successful
        """
        try:
            self._texts.clear()
            self._embeddings.clear()
            self._metadata.clear()
            return True
        except Exception as e:
            raise Exception(f"Failed to clear memory store: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics.
        
        Returns:
            Dict[str, Any]: Statistics about the store
        """
        return {
            "total_texts": len(self._texts),
            "total_embeddings": len(self._embeddings),
            "collection_name": self.config.collection_name,
            "embedding_dimension": self.config.embedding_dimension
        } 