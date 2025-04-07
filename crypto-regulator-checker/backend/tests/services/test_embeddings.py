"""Tests for embeddings service."""

import pytest
import numpy as np
from unittest.mock import patch, AsyncMock

from backend.services.embeddings.provider import SentenceTransformerProvider
from backend.services.embeddings.config import EmbeddingsConfig
from backend.core.exceptions import EmbeddingError
from backend.core.cache import Cache

pytestmark = pytest.mark.asyncio

@pytest.fixture
def embeddings_config():
    """Get embeddings configuration for testing."""
    return EmbeddingsConfig(
        model_name="all-MiniLM-L6-v2",
        normalize_embeddings=True,
        max_seq_length=512,
        batch_size=32
    )

@pytest.fixture
def mock_sentence_transformer():
    """Mock SentenceTransformer model."""
    with patch("sentence_transformers.SentenceTransformer") as mock:
        model = mock.return_value
        model.encode.return_value = np.random.rand(384)
        yield model

@pytest.fixture
async def embeddings_provider(
    embeddings_config,
    mock_sentence_transformer,
    cache: Cache
):
    """Get embeddings provider instance."""
    provider = SentenceTransformerProvider(
        config=embeddings_config,
        cache=cache
    )
    provider.model = mock_sentence_transformer
    return provider

async def test_get_embeddings_single(embeddings_provider):
    """Test getting embeddings for a single text."""
    text = "Test text for embedding generation"
    embeddings = await embeddings_provider.get_embeddings([text])
    
    assert len(embeddings) == 1
    assert isinstance(embeddings[0], np.ndarray)
    assert embeddings[0].shape == (384,)  # Default model dimension

async def test_get_embeddings_batch(embeddings_provider):
    """Test getting embeddings for multiple texts."""
    texts = [
        "First test text",
        "Second test text",
        "Third test text"
    ]
    embeddings = await embeddings_provider.get_embeddings(texts)
    
    assert len(embeddings) == len(texts)
    for emb in embeddings:
        assert isinstance(emb, np.ndarray)
        assert emb.shape == (384,)

async def test_get_embeddings_empty(embeddings_provider):
    """Test getting embeddings for empty input."""
    with pytest.raises(ValueError):
        await embeddings_provider.get_embeddings([])

async def test_get_embeddings_invalid_input(embeddings_provider):
    """Test getting embeddings with invalid input."""
    with pytest.raises(ValueError):
        await embeddings_provider.get_embeddings([None])

async def test_get_embeddings_model_error(embeddings_provider):
    """Test handling model errors."""
    embeddings_provider.model.encode.side_effect = Exception("Model error")
    
    with pytest.raises(EmbeddingError):
        await embeddings_provider.get_embeddings(["Test text"])

async def test_embeddings_caching(embeddings_provider, cache):
    """Test that embeddings are properly cached."""
    text = "Test text for caching"
    
    # First call should use the model
    embeddings1 = await embeddings_provider.get_embeddings([text])
    assert embeddings_provider.model.encode.call_count == 1
    
    # Second call should use cache
    embeddings2 = await embeddings_provider.get_embeddings([text])
    assert embeddings_provider.model.encode.call_count == 1  # No additional calls
    
    # Results should be identical
    np.testing.assert_array_equal(embeddings1[0], embeddings2[0])

async def test_embeddings_normalization(embeddings_provider):
    """Test that embeddings are properly normalized."""
    text = "Test text for normalization"
    embeddings = await embeddings_provider.get_embeddings([text])
    
    # Check that the vector is normalized (L2 norm ≈ 1)
    norm = np.linalg.norm(embeddings[0])
    np.testing.assert_almost_equal(norm, 1.0, decimal=6)

async def test_embeddings_batch_size(embeddings_provider):
    """Test that batch size limits are respected."""
    # Create more texts than the batch size
    texts = [f"Text {i}" for i in range(50)]  # Batch size is 32
    
    await embeddings_provider.get_embeddings(texts)
    
    # Check that encode was called twice (32 + 18 texts)
    calls = embeddings_provider.model.encode.call_args_list
    assert len(calls) == 2
    assert len(calls[0][0][0]) == 32  # First batch
    assert len(calls[1][0][0]) == 18  # Second batch

async def test_embeddings_max_sequence_length(embeddings_provider):
    """Test handling of long sequences."""
    # Create a text longer than max_seq_length
    long_text = "word " * 1000  # Much longer than 512 tokens
    
    embeddings = await embeddings_provider.get_embeddings([long_text])
    
    # Check that we got valid embeddings despite long input
    assert isinstance(embeddings[0], np.ndarray)
    assert embeddings[0].shape == (384,)

async def test_concurrent_embedding_requests(embeddings_provider):
    """Test handling concurrent embedding requests."""
    texts = [f"Text {i}" for i in range(10)]
    
    # Make concurrent requests
    tasks = [
        embeddings_provider.get_embeddings([text])
        for text in texts
    ]
    
    import asyncio
    results = await asyncio.gather(*tasks)
    
    # Check that all requests were processed
    assert len(results) == len(texts)
    for embeddings in results:
        assert isinstance(embeddings[0], np.ndarray)
        assert embeddings[0].shape == (384,) 