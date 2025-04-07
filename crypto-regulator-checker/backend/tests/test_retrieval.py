"""Tests for the retrieval system."""

import pytest
from unittest.mock import Mock, AsyncMock
import numpy as np

from services.rag.retrieval import (
    RetrievalConfig,
    RetrievedChunk,
    SemanticRetrieval,
    HybridRetrieval
)
from services.document_processing.chunking import TextChunk

@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    store = Mock()
    # Return different embeddings for different texts
    store.get_embedding = Mock(side_effect=lambda text: {
        "Test chunk 1": np.array([0.1, 0.2, 0.3]),
        "Test chunk 2": np.array([0.4, 0.5, 0.6]),
        "Lower score": np.array([0.7, 0.8, 0.9]),
        "Higher score": np.array([0.1, 0.2, 0.3])
    }[text])
    store.similarity_search = Mock(return_value=[
        Mock(
            chunk=TextChunk(
                text="Test chunk 1",
                metadata={"source": "doc1"},
                start_char=0,
                end_char=12,
                chunk_index=0
            ),
            score=0.9
        ),
        Mock(
            chunk=TextChunk(
                text="Test chunk 2",
                metadata={"source": "doc1"},
                start_char=13,
                end_char=25,
                chunk_index=1
            ),
            score=0.8
        )
    ])
    return store

@pytest.fixture
def mock_embeddings_provider():
    """Create a mock embeddings provider."""
    provider = AsyncMock()
    provider.get_embeddings = AsyncMock(return_value=[np.array([0.1, 0.2, 0.3])])
    return provider

def test_retrieval_config_validation():
    """Test retrieval configuration validation."""
    # Test valid config
    config = RetrievalConfig(
        top_k=5,
        min_similarity=0.6,
        duplicate_threshold=0.95
    )
    assert config.top_k == 5
    assert config.min_similarity == 0.6
    assert config.duplicate_threshold == 0.95
    
    # Test invalid top_k
    with pytest.raises(ValueError):
        RetrievalConfig(top_k=0)
    
    # Test invalid min_similarity
    with pytest.raises(ValueError):
        RetrievalConfig(min_similarity=1.5)
    
    # Test invalid duplicate_threshold
    with pytest.raises(ValueError):
        RetrievalConfig(duplicate_threshold=-0.1)

@pytest.mark.asyncio
async def test_semantic_retrieval_basic(mock_vector_store, mock_embeddings_provider):
    """Test basic semantic retrieval functionality."""
    retriever = SemanticRetrieval(
        vector_store=mock_vector_store,
        embeddings_provider=mock_embeddings_provider,
        config=RetrievalConfig(
            top_k=2,
            filter_duplicates=False,
            rerank_results=False
        )
    )
    
    results = await retriever.retrieve("test query")
    
    assert len(results) == 2
    assert isinstance(results[0], RetrievedChunk)
    assert results[0].similarity == 0.9
    assert results[0].rank == 1
    assert results[1].similarity == 0.8
    assert results[1].rank == 2

@pytest.mark.asyncio
async def test_semantic_retrieval_with_filters(mock_vector_store, mock_embeddings_provider):
    """Test semantic retrieval with metadata filters."""
    retriever = SemanticRetrieval(
        vector_store=mock_vector_store,
        embeddings_provider=mock_embeddings_provider,
        config=RetrievalConfig(
            filter_duplicates=False,
            rerank_results=False
        )
    )
    
    filters = {"source": "doc1"}
    await retriever.retrieve("test query", filters=filters)
    
    # Verify filters were passed to vector store
    mock_vector_store.similarity_search.assert_called_once()
    call_args = mock_vector_store.similarity_search.call_args[1]
    assert call_args["filters"] == filters

@pytest.mark.asyncio
async def test_semantic_retrieval_duplicate_filtering(mock_vector_store, mock_embeddings_provider):
    """Test duplicate filtering in semantic retrieval."""
    # Configure mock to return similar embeddings
    mock_vector_store.get_embedding.side_effect = [
        np.array([0.1, 0.2, 0.3]),  # First chunk
        np.array([0.11, 0.21, 0.31])  # Very similar to first
    ]
    
    retriever = SemanticRetrieval(
        vector_store=mock_vector_store,
        embeddings_provider=mock_embeddings_provider,
        config=RetrievalConfig(
            top_k=2,
            filter_duplicates=True,
            duplicate_threshold=0.95,
            rerank_results=False
        )
    )
    
    results = await retriever.retrieve("test query")
    
    # Should only return one result since second is too similar
    assert len(results) == 1
    assert results[0].similarity == 0.9

@pytest.mark.asyncio
async def test_semantic_retrieval_reranking(mock_vector_store, mock_embeddings_provider):
    """Test result reranking in semantic retrieval."""
    retriever = SemanticRetrieval(
        vector_store=mock_vector_store,
        embeddings_provider=mock_embeddings_provider,
        config=RetrievalConfig(
            filter_duplicates=False,
            rerank_results=True
        )
    )
    
    # Mock similarity search to return results in non-optimal order
    mock_vector_store.similarity_search.return_value = [
        Mock(
            chunk=TextChunk(
                text="Lower score",
                metadata={},
                start_char=0,
                end_char=11,
                chunk_index=0
            ),
            score=0.7
        ),
        Mock(
            chunk=TextChunk(
                text="Higher score",
                metadata={},
                start_char=12,
                end_char=24,
                chunk_index=1
            ),
            score=0.9
        )
    ]
    
    results = await retriever.retrieve("test query")
    
    # Verify results are reranked by similarity score
    assert len(results) == 2
    assert results[0].similarity == 0.9
    assert results[0].rank == 1
    assert results[1].similarity == 0.7
    assert results[1].rank == 2

@pytest.mark.asyncio
async def test_hybrid_retrieval_not_implemented(mock_vector_store, mock_embeddings_provider):
    """Test that hybrid retrieval raises NotImplementedError."""
    retriever = HybridRetrieval(
        vector_store=mock_vector_store,
        embeddings_provider=mock_embeddings_provider
    )
    
    with pytest.raises(NotImplementedError):
        await retriever.retrieve("test query") 