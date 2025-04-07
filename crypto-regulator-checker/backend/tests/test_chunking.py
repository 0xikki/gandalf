"""Tests for document chunking module."""

import pytest
from services.document_processing.chunking import (
    ChunkConfig,
    TextChunk,
    SimpleChunker,
    RecursiveChunker
)

def test_chunk_config_validation():
    """Test chunk configuration validation."""
    # Valid configurations
    ChunkConfig(chunk_size=512, chunk_overlap=50)
    ChunkConfig(chunk_size=1000, chunk_overlap=0)
    
    # Invalid configurations
    with pytest.raises(ValueError):
        ChunkConfig(chunk_size=0)  # Zero chunk size
    with pytest.raises(ValueError):
        ChunkConfig(chunk_size=100, chunk_overlap=-1)  # Negative overlap
    with pytest.raises(ValueError):
        ChunkConfig(chunk_size=100, chunk_overlap=100)  # Overlap equals chunk size
    with pytest.raises(ValueError):
        ChunkConfig(chunk_size=100, min_chunk_size=101)  # Min size exceeds max

def test_simple_chunker_empty_text():
    """Test simple chunker with empty text."""
    chunker = SimpleChunker()
    chunks = chunker.chunk_text("")
    assert len(chunks) == 0

def test_simple_chunker_small_text():
    """Test simple chunker with text smaller than chunk size."""
    chunker = SimpleChunker(ChunkConfig(chunk_size=100))
    text = "This is a small text."
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == len(text)
    assert chunks[0].chunk_index == 0

def test_simple_chunker_sentence_boundaries():
    """Test simple chunker respects sentence boundaries."""
    chunker = SimpleChunker(ChunkConfig(
        chunk_size=50,
        chunk_overlap=10,
        respect_sentences=True
    ))
    
    text = "First sentence. Second sentence here. Third sentence is longer."
    chunks = chunker.chunk_text(text)
    
    # Check that chunks end at sentence boundaries
    for chunk in chunks:
        assert chunk.text.strip().endswith((".", "!", "?"))

def test_simple_chunker_newline_boundaries():
    """Test simple chunker respects newline boundaries."""
    chunker = SimpleChunker(ChunkConfig(
        chunk_size=50,
        chunk_overlap=10,
        split_on_newline=True
    ))
    
    text = "First line\nSecond line\nThird line is longer\nFourth line"
    chunks = chunker.chunk_text(text)
    
    # Check that chunks tend to split at newlines
    for chunk in chunks[:-1]:  # All but last chunk
        assert "\n" not in chunk.text.strip()

def test_simple_chunker_metadata():
    """Test simple chunker preserves metadata."""
    chunker = SimpleChunker(ChunkConfig(chunk_size=100))
    metadata = {"source": "test", "language": "en"}
    chunks = chunker.chunk_text("Some text here", metadata)
    
    assert len(chunks) == 1
    assert chunks[0].metadata == metadata
    assert chunks[0].metadata is not metadata  # Should be a copy

def test_recursive_chunker_large_text():
    """Test recursive chunker with large text."""
    chunker = RecursiveChunker(ChunkConfig(
        chunk_size=100,
        chunk_overlap=20
    ))
    
    # Create a large text with various types of boundaries
    paragraphs = [
        "First paragraph with multiple sentences. This is another sentence.",
        "Second paragraph also has\nsome internal line breaks\nand continues.",
        "Third paragraph is quite long and will need to be split into multiple chunks because it exceeds the maximum chunk size.",
        "Fourth paragraph."
    ]
    
    text = "\n\n".join(paragraphs)
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 1  # Should create multiple chunks
    assert all(len(chunk.text) <= 100 for chunk in chunks)  # All chunks within size limit
    
    # Check chunk ordering
    for i in range(len(chunks) - 1):
        assert chunks[i].chunk_index < chunks[i + 1].chunk_index

def test_recursive_chunker_nested_structure():
    """Test recursive chunker with nested document structure."""
    chunker = RecursiveChunker(ChunkConfig(
        chunk_size=50,
        chunk_overlap=10
    ))
    
    text = """Section 1
    
Subsection 1.1
This is some content.

Subsection 1.2
More content here.

Section 2

This section has a very long sentence that needs to be split because it exceeds the maximum chunk size limit.

Section 3
Short section."""

    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 1
    assert all(len(chunk.text) <= 50 for chunk in chunks)
    
    # First chunk should start with "Section 1"
    assert chunks[0].text.startswith("Section 1")
    
    # Last chunk should contain "Short section"
    assert any("Short section" in chunk.text for chunk in chunks)

def test_chunkers_consistent_indices():
    """Test that both chunkers produce consistent chunk indices."""
    text = "A" * 1000  # Long text to force multiple chunks
    config = ChunkConfig(chunk_size=100, chunk_overlap=10)
    
    simple_chunks = SimpleChunker(config).chunk_text(text)
    recursive_chunks = RecursiveChunker(config).chunk_text(text)
    
    # Check that indices are sequential
    assert all(chunk.chunk_index == i for i, chunk in enumerate(simple_chunks))
    assert all(chunk.chunk_index == i for i, chunk in enumerate(recursive_chunks))

def test_chunkers_with_unicode():
    """Test chunkers handle Unicode text correctly."""
    text = "Hello 👋 World! This is a test with émojis 🌍 and accents éèê."
    config = ChunkConfig(chunk_size=20, chunk_overlap=5)
    
    simple_chunks = SimpleChunker(config).chunk_text(text)
    recursive_chunks = RecursiveChunker(config).chunk_text(text)
    
    # Reconstruct text (without overlaps) should match original
    simple_text = "".join(chunk.text for chunk in simple_chunks)
    recursive_text = "".join(chunk.text for chunk in recursive_chunks)
    
    assert all(c in simple_text for c in "👋🌍éèê")
    assert all(c in recursive_text for c in "👋🌍éèê") 