"""Base classes for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LLMResponse:
    """Data class for standardized LLM response."""
    text: str
    metadata: Dict[str, Any]
    timestamp: datetime
    provider: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None

@dataclass
class LLMConfig:
    """Base configuration for LLM providers."""
    api_key: str
    model: str = "default"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the provider.
        
        Args:
            config (LLMConfig): Provider configuration
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the provider configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the LLM.
        
        Args:
            prompt (str): The input prompt
            **kwargs: Additional parameters for generation
        
        Returns:
            str: The generated text
        
        Raises:
            Exception: If text generation fails
        """
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Generate embeddings for texts.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
            **kwargs: Additional parameters for embedding generation
        
        Returns:
            List[List[float]]: List of embedding vectors
        
        Raises:
            Exception: If embedding generation fails
        """
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the text.
        
        Args:
            text (str): Text to count tokens for
        
        Returns:
            int: Number of tokens
        """
        pass
    
    @abstractmethod
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information.
        
        Returns:
            Dict[str, Any]: Rate limit details
        """
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate the API key.
        
        Returns:
            bool: True if API key is valid, False otherwise
        """
        pass 