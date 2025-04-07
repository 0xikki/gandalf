from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class VectorStoreConfig:
    """Configuration for vector stores."""
    collection_name: str
    embedding_dimension: int
    distance_metric: str = "cosine"  # or "euclidean", "dot"
    persist_directory: Optional[str] = None
    cache_directory: Optional[str] = None

@dataclass
class VectorSearchResult:
    """Data class for vector search results."""
    id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    embedding: Optional[List[float]] = None
    timestamp: datetime = datetime.now()

class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize the vector store with configuration.
        
        Args:
            config (VectorStoreConfig): Store configuration
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the store configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add texts and their embeddings to the store.
        
        Args:
            texts (List[str]): The texts to store
            embeddings (List[List[float]]): The embedding vectors
            metadata (Optional[List[Dict[str, Any]]]): Optional metadata for each text
            ids (Optional[List[str]]): Optional IDs for the texts
        
        Returns:
            List[str]: The IDs of the added texts
        
        Raises:
            Exception: If adding texts fails
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar texts using a query embedding.
        
        Args:
            query_embedding (List[float]): The query embedding vector
            k (int): Number of results to return
            filter_metadata (Optional[Dict[str, Any]]): Optional metadata filter
        
        Returns:
            List[VectorSearchResult]: The search results
        
        Raises:
            Exception: If search fails
        """
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]) -> bool:
        """Delete texts by their IDs.
        
        Args:
            ids (List[str]): The IDs to delete
        
        Returns:
            bool: True if deletion was successful
        
        Raises:
            Exception: If deletion fails
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[VectorSearchResult]:
        """Get a text by its ID.
        
        Args:
            id (str): The ID to retrieve
        
        Returns:
            Optional[VectorSearchResult]: The result if found
        
        Raises:
            Exception: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all texts from the store.
        
        Returns:
            bool: True if clearing was successful
        
        Raises:
            Exception: If clearing fails
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics.
        
        Returns:
            Dict[str, Any]: Statistics including:
                - total_texts: Total number of texts
                - total_embeddings: Total number of embeddings
                - collection_name: Name of the collection
                - embedding_dimension: Dimension of embeddings
        """
        pass 