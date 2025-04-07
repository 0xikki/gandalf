import os
import pytest
import pytest_asyncio
from datetime import datetime
from typing import List, Dict, Any
from services.vector_store.providers import ChromaStore, VectorStoreConfig

@pytest.fixture
def test_config():
    """Create a test configuration."""
    return VectorStoreConfig(
        collection_name="test_collection",
        embedding_dimension=384,  # Typical dimension for small models
        persist_directory="test_chroma_db"
    )

@pytest_asyncio.fixture
async def store(test_config):
    """Create a test store instance."""
    store = ChromaStore(test_config)
    yield store
    # Cleanup after tests
    try:
        store.client.delete_collection(test_config.collection_name)
    except:
        pass
    if os.path.exists(test_config.persist_directory):
        import shutil
        shutil.rmtree(test_config.persist_directory)

@pytest.fixture
def sample_texts() -> List[str]:
    """Create sample texts."""
    return [
        "This is a test document about crypto regulations.",
        "Another document discussing financial compliance.",
        "Guidelines for cryptocurrency trading and reporting."
    ]

@pytest.fixture
def sample_embeddings() -> List[List[float]]:
    """Create sample embeddings."""
    # Create embeddings that will maintain relative distances after normalization
    return [
        [1.0] * 192 + [0.0] * 192,  # First half 1s, second half 0s
        [0.0] * 192 + [1.0] * 192,  # First half 0s, second half 1s
        [0.5] * 384  # All 0.5s
    ]

@pytest.fixture
def sample_metadata() -> List[Dict[str, Any]]:
    """Create sample metadata."""
    return [
        {"source": "test1", "category": "regulation"},
        {"source": "test2", "category": "compliance"},
        {"source": "test3", "category": "guidelines"}
    ]

@pytest.mark.asyncio
async def test_init_with_valid_config(test_config):
    """Test store initialization with valid config."""
    store = ChromaStore(test_config)
    assert store.config == test_config
    assert store.collection is not None

@pytest.mark.asyncio
async def test_init_with_invalid_config():
    """Test initialization with invalid config."""
    invalid_config = VectorStoreConfig(
        collection_name="",  # Invalid empty name
        embedding_dimension=384
    )
    with pytest.raises(ValueError):
        ChromaStore(invalid_config)

@pytest.mark.asyncio
async def test_add_texts(store, sample_texts, sample_embeddings):
    """Test adding texts with embeddings."""
    ids = await store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings
    )
    assert len(ids) == len(sample_texts)
    
    # Verify addition
    stats = store.get_stats()
    assert stats["total_texts"] == len(sample_texts)

@pytest.mark.asyncio
async def test_add_texts_with_metadata(
    store, sample_texts, sample_embeddings, sample_metadata
):
    """Test adding texts with metadata."""
    ids = await store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings,
        metadata=sample_metadata
    )
    assert len(ids) == len(sample_texts)
    
    # Verify metadata
    result = await store.get_by_id(ids[0])
    assert result is not None
    assert result.metadata["source"] == "test1"
    assert result.metadata["category"] == "regulation"

@pytest.mark.asyncio
async def test_search(store, sample_texts, sample_embeddings):
    """Test searching for similar texts."""
    await store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings
    )
    
    # Search using first embedding
    results = await store.search(
        query_embedding=sample_embeddings[0],
        k=2
    )
    assert len(results) == 2
    assert results[0].text == sample_texts[0]  # Most similar should be itself

@pytest.mark.asyncio
async def test_search_with_filter(
    store, sample_texts, sample_embeddings, sample_metadata
):
    """Test searching with metadata filter."""
    await store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings,
        metadata=sample_metadata
    )
    
    # Search with category filter
    results = await store.search(
        query_embedding=sample_embeddings[0],
        k=5,  # Increased to get all potential matches
        filter_metadata={"category": "compliance"}
    )
    assert len(results) > 0
    assert all(r.metadata["category"] == "compliance" for r in results)

@pytest.mark.asyncio
async def test_delete(store, sample_texts, sample_embeddings):
    """Test deleting texts."""
    ids = await store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings
    )
    
    # Delete first text
    success = await store.delete([ids[0]])
    assert success
    
    # Verify deletion
    result = await store.get_by_id(ids[0])
    assert result is None
    
    stats = store.get_stats()
    assert stats["total_texts"] == len(sample_texts) - 1

@pytest.mark.asyncio
async def test_get_by_id(store, sample_texts, sample_embeddings):
    """Test retrieving text by ID."""
    ids = await store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings
    )
    
    result = await store.get_by_id(ids[0])
    assert result is not None
    assert result.text == sample_texts[0]
    assert isinstance(result.timestamp, datetime)

@pytest.mark.asyncio
async def test_clear(store, sample_texts, sample_embeddings):
    """Test clearing all texts."""
    await store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings
    )
    
    success = await store.clear()
    assert success
    
    stats = store.get_stats()
    assert stats["total_texts"] == 0

@pytest.mark.asyncio
async def test_get_stats(store, sample_texts, sample_embeddings):
    """Test getting store statistics."""
    await store.add_texts(
        texts=sample_texts,
        embeddings=sample_embeddings
    )
    
    stats = store.get_stats()
    assert stats["total_texts"] == len(sample_texts)
    assert stats["total_embeddings"] == len(sample_embeddings)
    assert stats["collection_name"] == "test_collection"
    assert stats["embedding_dimension"] == 384
    assert stats["is_persistent"] is True 