"""Tests for the context augmentation system."""

import pytest
from services.llm.context_augmentation import ContextConfig, ContextAugmenter
from services.rag.retrieval import RetrievedChunk
from services.rag.chunking import TextChunk

@pytest.fixture
def mock_chunk():
    """Create a mock retrieved chunk for testing."""
    def _create_chunk(text: str = "Test text", source: str = "test.pdf", similarity: float = 0.9) -> RetrievedChunk:
        return RetrievedChunk(
            chunk=TextChunk(
                text=text,
                metadata={"source": source},
                start_char=0,
                end_char=len(text),
                chunk_index=0
            ),
            similarity=similarity,
            rank=1
        )
    return _create_chunk

@pytest.fixture
def augmenter():
    """Create a context augmenter instance."""
    return ContextAugmenter()

def test_context_config_defaults():
    """Test default configuration values."""
    config = ContextConfig()
    assert config.max_context_length == 4000
    assert "Context:" in config.context_template
    assert config.chunk_separator == "\n---\n"
    assert config.include_metadata is True

def test_custom_context_config():
    """Test custom configuration values."""
    config = ContextConfig(
        max_context_length=2000,
        context_template="Custom template: {context}\nQ: {question}",
        chunk_separator="===",
        include_metadata=False
    )
    assert config.max_context_length == 2000
    assert config.context_template == "Custom template: {context}\nQ: {question}"
    assert config.chunk_separator == "==="
    assert config.include_metadata is False

def test_format_chunk_metadata(augmenter, mock_chunk):
    """Test chunk metadata formatting."""
    chunk = mock_chunk("Test text", "doc.pdf", 0.95)
    
    # Test with metadata enabled
    metadata = augmenter.format_chunk_metadata(chunk)
    assert "Source: doc.pdf" in metadata
    assert "Relevance: 0.95" in metadata
    
    # Test with metadata disabled
    augmenter.config.include_metadata = False
    metadata = augmenter.format_chunk_metadata(chunk)
    assert metadata == ""

def test_format_chunk(augmenter, mock_chunk):
    """Test chunk formatting."""
    chunk = mock_chunk("Test text", "doc.pdf", 0.95)
    
    # Test with metadata
    formatted = augmenter.format_chunk(chunk)
    assert "Test text" in formatted
    assert "Source: doc.pdf" in formatted
    assert "Relevance: 0.95" in formatted
    
    # Test without metadata
    augmenter.config.include_metadata = False
    formatted = augmenter.format_chunk(chunk)
    assert formatted == "Test text"

def test_augment_prompt(augmenter, mock_chunk):
    """Test prompt augmentation with context."""
    chunks = [
        mock_chunk("First chunk", "doc1.pdf", 0.95),
        mock_chunk("Second chunk", "doc2.pdf", 0.85)
    ]
    question = "Test question?"
    
    augmented = augmenter.augment_prompt(question, chunks)
    
    # Check that all components are present
    assert "Context:" in augmented
    assert "Question: Test question?" in augmented
    assert "First chunk" in augmented
    assert "Second chunk" in augmented
    assert "doc1.pdf" in augmented
    assert "doc2.pdf" in augmented
    
    # Check chunk separator
    assert "\n---\n" in augmented

def test_create_system_prompt(augmenter):
    """Test system prompt creation for different task types."""
    # Test compliance check prompt
    compliance_prompt = augmenter.create_system_prompt("compliance_check")
    assert "regulatory compliance assistant" in compliance_prompt
    assert "Determine if the given scenario complies" in compliance_prompt
    
    # Test risk assessment prompt
    risk_prompt = augmenter.create_system_prompt("risk_assessment")
    assert "risk assessment specialist" in risk_prompt
    assert "Identify potential risks" in risk_prompt
    
    # Test general prompt
    general_prompt = augmenter.create_system_prompt("general")
    assert "regulatory expert assistant" in general_prompt
    assert "Answer questions based solely on" in general_prompt
    
    # Test unknown task type falls back to general
    unknown_prompt = augmenter.create_system_prompt("unknown_type")
    assert unknown_prompt == general_prompt 