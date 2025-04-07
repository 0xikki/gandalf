"""Tests for Gemini provider."""

import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from services.llm.providers import GeminiProvider, GeminiConfig
from services.llm.providers.base_provider import LLMResponse

@pytest.fixture
def config():
    """Create a test configuration."""
    return GeminiConfig(
        api_key="test_key",
        max_tokens=1000,
        temperature=0.7,
        top_p=1.0
    )

@pytest.fixture
def provider(config):
    """Create a test provider instance."""
    return GeminiProvider(config)

@pytest.fixture
def mock_gemini_client():
    """Create a mock Gemini client."""
    with patch('services.llm.providers.gemini_provider.genai.GenerativeModel') as mock_model:
        mock_model_instance = AsyncMock()
        mock_model.return_value = mock_model_instance
        yield mock_model_instance

def test_init_with_valid_config(config):
    """Test provider initialization with valid config."""
    provider = GeminiProvider(config)
    assert provider.config == config
    assert provider.MODEL_NAME == "gemini-pro"

def test_init_with_invalid_max_tokens(config):
    """Test initialization with invalid max tokens."""
    config.max_tokens = GeminiProvider.MAX_TOKENS + 1
    with pytest.raises(ValueError):
        GeminiProvider(config)

def test_init_without_api_key():
    """Test initialization without API key."""
    config = GeminiConfig(api_key="")
    with pytest.raises(ValueError):
        GeminiProvider(config)

@pytest.mark.asyncio
async def test_generate_text(mock_gemini_client, provider):
    """Test text generation."""
    expected_text = "Generated text response"
    mock_response = AsyncMock()
    mock_response.text = expected_text
    mock_gemini_client.generate_content_async.return_value = mock_response
    
    result = await provider.generate_text("Test prompt")
    assert result == expected_text
    mock_gemini_client.generate_content_async.assert_called_once_with(
        "Test prompt",
        generation_config={
            'temperature': 0.7,
            'max_output_tokens': 1000
        }
    )

@pytest.mark.asyncio
async def test_generate_text_with_error(mock_gemini_client, provider):
    """Test error handling in text generation."""
    mock_gemini_client.generate_content_async.side_effect = Exception("API Error")
    
    with pytest.raises(Exception, match="Failed to generate text with Gemini: API Error"):
        await provider.generate_text("Test prompt")

@pytest.mark.asyncio
async def test_generate_text_with_empty_response(mock_gemini_client, provider):
    """Test handling of empty response."""
    mock_response = AsyncMock()
    mock_response.text = ""
    mock_gemini_client.generate_content_async.return_value = mock_response
    
    with pytest.raises(Exception, match="Failed to generate text with Gemini: Gemini returned empty response"):
        await provider.generate_text("Test prompt")

@pytest.mark.asyncio
async def test_generate_embeddings_success(provider):
    """Test successful embeddings generation."""
    mock_response = Mock()
    mock_response.embedding = [0.1, 0.2, 0.3]
    
    with patch.object(provider.embedding_model, 'generate_content_async',
                     return_value=mock_response) as mock_generate:
        embeddings = await provider.generate_embeddings(["Test text"])
        
        assert len(embeddings) == 1
        assert len(embeddings[0]) == 3
        assert all(isinstance(x, float) for x in embeddings[0])
        
        mock_generate.assert_called_once_with(
            "Test text",
            generation_config={"model": provider.EMBEDDING_MODEL}
        )

@pytest.mark.asyncio
async def test_generate_embeddings_error(provider):
    """Test embeddings generation error handling."""
    with patch.object(provider.embedding_model, 'generate_content_async',
                     side_effect=Exception("API Error")):
        with pytest.raises(Exception) as exc_info:
            await provider.generate_embeddings(["Test text"])
        assert "Gemini Pro embedding generation failed" in str(exc_info.value)

def test_get_token_count(provider):
    """Test token counting."""
    text = "This is a test text"
    token_count = provider.get_token_count(text)
    assert token_count > 0
    assert isinstance(token_count, int)

def test_get_rate_limit_info(provider):
    """Test rate limit information retrieval."""
    info = provider.get_rate_limit_info()
    assert isinstance(info, dict)
    assert "requests_remaining" in info
    assert "requests_limit" in info
    assert "reset_time" in info
    assert "current_usage" in info

def test_validate_api_key_success(provider):
    """Test successful API key validation."""
    with patch.object(provider.model, 'generate_content',
                     return_value=Mock()) as mock_generate:
        assert provider.validate_api_key() is True
        mock_generate.assert_called_once_with("test")

def test_validate_api_key_failure(provider):
    """Test API key validation failure."""
    with patch.object(provider.model, 'generate_content',
                     side_effect=Exception("Invalid API key")):
        assert provider.validate_api_key() is False 