import os
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import chromadb
from chromadb.config import Settings
from .base_store import BaseVectorStore, VectorStoreConfig, VectorSearchResult
import numpy as np
from chromadb import Client, Collection

class ChromaStore(BaseVectorStore):
    """ChromaDB implementation of vector store."""
    
    def __init__(self, config: VectorStoreConfig):
        """Initialize the ChromaDB store.
        
        Args:
            config (VectorStoreConfig): Store configuration
        """
        super().__init__(config)
        
        # Initialize ChromaDB client with persistence
        settings = Settings()
        if config.persist_directory:
            settings.persist_directory = config.persist_directory
        if config.cache_directory:
            settings.chroma_cache_directory = config.cache_directory
            
        self.client = Client(Settings(anonymized_telemetry=False))
        
        # Delete collection if it exists and recreate it
        try:
            self.client.delete_collection(config.collection_name)
        except ValueError:
            pass  # Collection doesn't exist
            
        # Create collection with specified parameters
        self.collection = self.client.get_or_create_collection(config.collection_name)
    
    def _validate_config(self) -> None:
        """Validate the ChromaDB configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.collection_name:
            raise ValueError("Collection name is required")
        
        if self.config.embedding_dimension <= 0:
            raise ValueError("Embedding dimension must be positive")
        
        if self.config.persist_directory and not os.path.exists(self.config.persist_directory):
            os.makedirs(self.config.persist_directory, exist_ok=True)
    
    async def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add texts and their embeddings to ChromaDB.
        
        Args:
            texts (List[str]): The texts to add
            embeddings (List[List[float]]): The embeddings for each text
            metadata (Optional[List[Dict[str, Any]]], optional): Optional metadata for each text. Defaults to None.
            ids (Optional[List[str]], optional): Optional IDs for each text. Defaults to None.
        
        Returns:
            List[str]: The IDs of the added texts
        
        Raises:
            Exception: If adding fails
        """
        try:
            # Convert embeddings to numpy arrays for normalization
            embeddings_np = np.array(embeddings)
            # Normalize embeddings
            norms = np.linalg.norm(embeddings_np, axis=1, keepdims=True)
            normalized_embeddings = embeddings_np / norms
            # Convert back to list for ChromaDB
            normalized_embeddings = normalized_embeddings.tolist()

            # Create default metadata if none provided
            if metadata is None:
                metadata = [{"type": "text", "timestamp": datetime.now().isoformat()} for _ in range(len(texts))]

            # Add to collection
            self.collection.add(
                documents=texts,
                embeddings=normalized_embeddings,
                metadatas=metadata,
                ids=ids if ids else [str(i) for i in range(len(texts))]
            )
            return ids if ids else [str(i) for i in range(len(texts))]
            
        except Exception as e:
            raise Exception(f"Failed to add texts to ChromaDB: {str(e)}")
    
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
            # Normalize the query embedding for consistent results
            query_embedding = np.array(query_embedding)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)

            # Perform the search
            result = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k,
                where=filter_metadata,
                include=["documents", "metadatas", "embeddings", "distances"]
            )

            if not result["ids"] or len(result["ids"][0]) == 0:
                return []

            # Process results
            results = []
            for i in range(len(result["ids"][0])):
                # Handle embeddings - they are already lists from ChromaDB
                embedding = result["embeddings"][0][i] if result.get("embeddings") else None
                metadata = result["metadatas"][0][i] if result.get("metadatas") else None
                
                results.append(VectorSearchResult(
                    id=result["ids"][0][i],
                    text=result["documents"][0][i],
                    metadata=metadata,
                    score=float(result["distances"][0][i]),
                    embedding=embedding,
                    timestamp=datetime.now()
                ))

            return results

        except Exception as e:
            raise Exception(f"Failed to search in ChromaDB: {str(e)}")
    
    async def delete(self, ids: List[str]) -> bool:
        """Delete texts from ChromaDB by their IDs.
        
        Args:
            ids (List[str]): The IDs to delete
        
        Returns:
            bool: True if deletion was successful
        
        Raises:
            Exception: If deletion fails
        """
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete from ChromaDB: {str(e)}")
    
    async def get_by_id(self, id: str) -> Optional[VectorSearchResult]:
        """Get a text from ChromaDB by its ID.
        
        Args:
            id (str): The ID to retrieve
        
        Returns:
            Optional[VectorSearchResult]: The result if found
        
        Raises:
            Exception: If retrieval fails
        """
        try:
            result = self.collection.get(
                ids=[id],
                include=["documents", "metadatas", "embeddings"]
            )
            
            if len(result["ids"]) == 0:
                return None
                
            # Handle embeddings - they are already lists from ChromaDB
            embeddings = result.get("embeddings", [])
            embedding = embeddings[0] if len(embeddings) > 0 else None

            # Handle metadata properly
            metadatas = result.get("metadatas", [])
            metadata = metadatas[0] if len(metadatas) > 0 else None

            return VectorSearchResult(
                id=result["ids"][0],
                text=result["documents"][0],
                metadata=metadata,
                score=0.0,  # No score for direct retrieval
                embedding=embedding,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            if "not found" in str(e).lower():
                return None
            raise Exception(f"Failed to get text from ChromaDB: {str(e)}")
    
    async def clear(self) -> bool:
        """Clear all texts from ChromaDB.
        
        Returns:
            bool: True if clearing was successful
        
        Raises:
            Exception: If clearing fails
        """
        try:
            # Delete and recreate the collection for a clean slate
            self.client.delete_collection(self.config.collection_name)
            self.collection = self.client.get_or_create_collection(self.config.collection_name)
            return True
        except Exception as e:
            raise Exception(f"Failed to clear ChromaDB: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics.
        
        Returns:
            Dict[str, Any]: Statistics about the store
        """
        try:
            count = self.collection.count()
            return {
                "total_texts": count,
                "total_embeddings": count,
                "collection_name": self.config.collection_name,
                "embedding_dimension": self.config.embedding_dimension,
                "is_persistent": bool(self.config.persist_directory)
            }
        except Exception as e:
            raise Exception(f"Failed to get ChromaDB stats: {str(e)}") 