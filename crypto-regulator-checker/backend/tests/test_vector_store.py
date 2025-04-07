"""Tests for the vector store implementations."""

import pytest
import numpy as np
from unittest.mock import Mock

from services.vector_store.memory import MemoryVectorStore
from services.document_processing.chunking import TextChunk

@pytest.fixture
def mock_embeddings_provider():
    """Create a mock embeddings provider."""
    provider = Mock()
    provider.get_embeddings_sync = Mock(return_value=[
        np.array([1.0, 0.0, 0.0]),  # First text
        np.array([0.0, 1.0, 0.0])   # Second text
    ])
    return provider

def test_memory_store_add_text(mock_embeddings_provider):
    """Test adding single text to memory store."""
    store = MemoryVectorStore(embeddings_provider=mock_embeddings_provider)
    
    # Add text with metadata
    store.add_text(
        text="Test text",
        metadata={"source": "test"}
    )
    
    assert len(store.texts) == 1
    assert store.texts[0] == "Test text"
    assert len(store.embeddings) == 1
    assert np.array_equal(store.embeddings[0], np.array([1.0, 0.0, 0.0]))
    assert len(store.metadatas) == 1
    assert store.metadatas[0] == {"source": "test"}

def test_memory_store_add_texts(mock_embeddings_provider):
    """Test adding multiple texts to memory store."""
    store = MemoryVectorStore(embeddings_provider=mock_embeddings_provider)
    
    # Add multiple texts with metadata
    store.add_texts(
        texts=["Text 1", "Text 2"],
        metadatas=[{"source": "1"}, {"source": "2"}]
    )
    
    assert len(store.texts) == 2
    assert store.texts == ["Text 1", "Text 2"]
    assert len(store.embeddings) == 2
    assert np.array_equal(store.embeddings[0], np.array([1.0, 0.0, 0.0]))
    assert np.array_equal(store.embeddings[1], np.array([0.0, 1.0, 0.0]))
    assert len(store.metadatas) == 2
    assert store.metadatas == [{"source": "1"}, {"source": "2"}]

def test_memory_store_similarity_search(mock_embeddings_provider):
    """Test similarity search in memory store."""
    store = MemoryVectorStore(embeddings_provider=mock_embeddings_provider)
    
    # Add test data
    store.add_texts(
        texts=["Text 1", "Text 2"],
        metadatas=[{"source": "1"}, {"source": "2"}]
    )
    
    # Search with query embedding similar to first text
    results = store.similarity_search(
        query_embedding=np.array([0.9, 0.1, 0.0]),
        k=2,
        min_score=0.0
    )
    
    assert len(results) == 2
    assert results[0].chunk.text == "Text 1"  # Most similar
    assert results[0].score > results[1].score
    assert results[1].chunk.text == "Text 2"

def test_memory_store_similarity_search_with_filters(mock_embeddings_provider):
    """Test similarity search with metadata filters."""
    store = MemoryVectorStore(embeddings_provider=mock_embeddings_provider)
    
    # Add test data
    store.add_texts(
        texts=["Text 1", "Text 2"],
        metadatas=[{"source": "1"}, {"source": "2"}]
    )
    
    # Search with filter
    results = store.similarity_search(
        query_embedding=np.array([0.9, 0.1, 0.0]),
        k=2,
        filters={"source": "1"}
    )
    
    assert len(results) == 1
    assert results[0].chunk.text == "Text 1"
    assert results[0].chunk.metadata == {"source": "1"}

def test_memory_store_similarity_search_min_score(mock_embeddings_provider):
    """Test similarity search with minimum score threshold."""
    store = MemoryVectorStore(embeddings_provider=mock_embeddings_provider)
    
    # Add test data
    store.add_texts(
        texts=["Text 1", "Text 2"],
        metadatas=[{"source": "1"}, {"source": "2"}]
    )
    
    # Search with high minimum score
    results = store.similarity_search(
        query_embedding=np.array([0.9, 0.1, 0.0]),
        k=2,
        min_score=0.8  # Only first text should match
    )
    
    assert len(results) == 1
    assert results[0].chunk.text == "Text 1"

def test_memory_store_get_embedding(mock_embeddings_provider):
    """Test getting embedding for text."""
    store = MemoryVectorStore(embeddings_provider=mock_embeddings_provider)
    
    embedding = store.get_embedding("Test text")
    
    assert np.array_equal(embedding, np.array([1.0, 0.0, 0.0]))
    mock_embeddings_provider.get_embeddings_sync.assert_called_once_with(["Test text"])

def test_memory_store_clear(mock_embeddings_provider):
    """Test clearing the memory store."""
    store = MemoryVectorStore(embeddings_provider=mock_embeddings_provider)
    
    # Add some data
    store.add_text("Test text")
    assert len(store.texts) == 1
    
    # Clear store
    store.clear()
    assert len(store.texts) == 0
    assert len(store.embeddings) == 0
    assert len(store.metadatas) == 0 