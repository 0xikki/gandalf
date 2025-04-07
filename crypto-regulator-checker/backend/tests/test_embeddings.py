"""Tests for embeddings generation."""

import pytest
from services.vector_store.providers.embeddings_factory import EmbeddingsFactory
from services.vector_store.providers.embeddings_provider import EmbeddingConfig
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from services.embeddings import EmbeddingsConfig, SentenceTransformerProvider

@pytest.mark.asyncio
async def test_embeddings_generation():
    # Get default provider
    provider = EmbeddingsFactory.get_default_provider()
    
    # Test single text embedding
    text = "This is a test document for embedding generation"
    embedding = await provider.generate_embedding(text)
    
    # Check embedding dimensions (384 for all-MiniLM-L6-v2)
    assert len(embedding) == 384
    
    # Test batch embedding generation
    texts = [
        "First test document",
        "Second test document",
        "Third test document"
    ]
    embeddings = await provider.generate_embeddings(texts)
    
    # Check number of embeddings
    assert len(embeddings) == len(texts)
    
    # Check dimensions of each embedding
    for emb in embeddings:
        assert len(emb) == 384
        
@pytest.mark.asyncio
async def test_empty_input():
    provider = EmbeddingsFactory.get_default_provider()
    
    # Test empty list
    embeddings = await provider.generate_embeddings([])
    assert len(embeddings) == 0
    
@pytest.mark.asyncio
async def test_custom_config():
    config = EmbeddingConfig(
        model_name="all-MiniLM-L6-v2",
        max_seq_length=256,
        normalize_embeddings=True
    )
    
    provider = EmbeddingsFactory.get_provider("custom", config)
    
    text = "Test document"
    embedding = await provider.generate_embedding(text)
    
    assert len(embedding) == 384  # Model output dimension remains same
    
@pytest.mark.asyncio
async def test_provider_singleton():
    provider1 = EmbeddingsFactory.get_provider("test")
    provider2 = EmbeddingsFactory.get_provider("test")
    
    assert provider1 is provider2  # Same instance 

def test_embeddings_config_validation():
    """Test embeddings configuration validation."""
    # Test valid config
    config = EmbeddingsConfig(
        model_name="all-MiniLM-L6-v2",
        max_seq_length=512,
        batch_size=32
    )
    assert config.model_name == "all-MiniLM-L6-v2"
    assert config.max_seq_length == 512
    assert config.batch_size == 32
    
    # Test invalid model name
    with pytest.raises(ValueError):
        EmbeddingsConfig(model_name="")
    
    # Test invalid max sequence length
    with pytest.raises(ValueError):
        EmbeddingsConfig(max_seq_length=0)
    
    # Test invalid batch size
    with pytest.raises(ValueError):
        EmbeddingsConfig(batch_size=0)

def test_sentence_transformer_sync():
    """Test synchronous embedding generation."""
    provider = SentenceTransformerProvider(
        config=EmbeddingsConfig(batch_size=2)
    )
    texts = ["This is a test", "Another test"]
    embeddings = provider.generate_embeddings_sync(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == len(provider)

@pytest.mark.asyncio
async def test_sentence_transformer_async():
    """Test asynchronous embedding generation."""
    provider = SentenceTransformerProvider(
        config=EmbeddingsConfig(batch_size=2),
        executor=ThreadPoolExecutor(max_workers=1)
    )
    texts = ["This is a test", "Another test"]
    embeddings = await provider.generate_embeddings(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == len(provider)

def test_sentence_transformer_batching():
    """Test batch processing of texts."""
    provider = SentenceTransformerProvider(
        config=EmbeddingsConfig(batch_size=2)
    )
    texts = ["Text 1", "Text 2", "Text 3", "Text 4"]
    embeddings = provider.generate_embeddings_sync(texts)
    assert len(embeddings) == 4
    assert all(len(emb) == len(provider) for emb in embeddings)

def test_sentence_transformer_long_text():
    """Test handling of long texts."""
    provider = SentenceTransformerProvider(
        config=EmbeddingsConfig(max_seq_length=10)  # Small max length for testing
    )
    text = "This is a very long text that should be truncated"
    embeddings = provider.generate_embeddings_sync([text])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == len(provider)

def test_sentence_transformer_empty_input():
    """Test handling of empty input."""
    provider = SentenceTransformerProvider()
    with pytest.raises(Exception, match="Failed to generate embeddings"):
        provider.generate_embeddings_sync([])

@pytest.mark.asyncio
async def test_sentence_transformer_concurrent():
    """Test concurrent embedding generation."""
    provider = SentenceTransformerProvider(
        executor=ThreadPoolExecutor(max_workers=2)
    )
    texts = ["Text 1", "Text 2", "Text 3", "Text 4"]
    embeddings = await provider.generate_embeddings(texts)
    assert len(embeddings) == 4
    assert all(len(emb) == len(provider) for emb in embeddings) 