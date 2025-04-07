from typing import Optional, Dict, Type
from .embeddings_provider import EmbeddingsProvider, EmbeddingConfig
from .base_store import BaseVectorStore, VectorStoreConfig
from .memory_store import MemoryStore

class EmbeddingsFactory:
    _providers: Dict[str, EmbeddingsProvider] = {}
    _default_provider: Optional[EmbeddingsProvider] = None
    
    @classmethod
    def get_provider(
        cls,
        provider_name: str = "default",
        config: Optional[EmbeddingConfig] = None
    ) -> EmbeddingsProvider:
        """
        Get or create an embeddings provider instance
        
        Args:
            provider_name: Name of the provider to get/create
            config: Optional configuration for the provider
            
        Returns:
            EmbeddingsProvider instance
        """
        if provider_name not in cls._providers:
            provider = EmbeddingsProvider(config)
            cls._providers[provider_name] = provider
            
            if provider_name == "default":
                cls._default_provider = provider
                
        return cls._providers[provider_name]
    
    @classmethod
    def get_default_provider(cls) -> EmbeddingsProvider:
        """
        Get the default embeddings provider
        
        Returns:
            Default EmbeddingsProvider instance
        """
        if not cls._default_provider:
            cls._default_provider = cls.get_provider("default")
        return cls._default_provider 

    @staticmethod
    def create_store(
        collection_name: str,
        embedding_dimension: int,
        distance_metric: str = "cosine",
        persist_directory: Optional[str] = None,
        cache_directory: Optional[str] = None
    ) -> BaseVectorStore:
        """Create a vector store instance.
        
        Args:
            collection_name (str): Name of the collection
            embedding_dimension (int): Dimension of embeddings
            distance_metric (str, optional): Distance metric to use. Defaults to "cosine".
            persist_directory (Optional[str], optional): Directory for persistence. Defaults to None.
            cache_directory (Optional[str], optional): Directory for caching. Defaults to None.
        
        Returns:
            BaseVectorStore: The vector store instance
        """
        config = VectorStoreConfig(
            collection_name=collection_name,
            embedding_dimension=embedding_dimension,
            distance_metric=distance_metric,
            persist_directory=persist_directory,
            cache_directory=cache_directory
        )
        
        return MemoryStore(config) 