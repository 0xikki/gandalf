"""Gemini Pro LLM provider implementation."""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .base_provider import BaseLLMProvider, LLMConfig, LLMResponse

class GeminiConfig(LLMConfig):
    """Configuration for Gemini Pro provider."""
    model: str = "gemini-pro"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0

class GeminiProvider(BaseLLMProvider):
    """Gemini Pro LLM provider implementation."""
    
    MODEL_NAME = "gemini-pro"
    EMBEDDING_MODEL = "embedding-001"  # Gemini's embedding model
    MAX_TOKENS = 30720  # Gemini Pro's context window
    
    def __init__(self, config: GeminiConfig):
        """Initialize the Gemini Pro provider.
        
        Args:
            config (GeminiConfig): Provider configuration
        """
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        
        # Configure safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Initialize models
        self.model = genai.GenerativeModel(
            model_name=self.MODEL_NAME,
            safety_settings=self.safety_settings,
            generation_config={
                "temperature": config.temperature,
                "top_p": config.top_p,
                "max_output_tokens": config.max_tokens or self.MAX_TOKENS
            }
        )
        self.embedding_model = genai.GenerativeModel(model_name=self.EMBEDDING_MODEL)
    
    def _validate_config(self) -> None:
        """Validate the Gemini Pro configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.api_key:
            raise ValueError("Gemini Pro API key is required")
        
        if self.config.max_tokens and self.config.max_tokens > self.MAX_TOKENS:
            raise ValueError(f"Max tokens cannot exceed {self.MAX_TOKENS}")
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Gemini Pro.
        
        Args:
            prompt (str): The input prompt
            **kwargs: Additional parameters for generation
        
        Returns:
            str: The generated text
        
        Raises:
            Exception: If text generation fails
        """
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    'temperature': self.config.temperature,
                    'max_output_tokens': self.config.max_tokens
                }
            )
            
            if not response.text:
                raise Exception("Gemini returned empty response")
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Failed to generate text with Gemini: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Generate embeddings using Gemini's embedding model.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
            **kwargs: Additional parameters for embedding generation
        
        Returns:
            List[List[float]]: List of embedding vectors
        
        Raises:
            Exception: If embedding generation fails
        """
        try:
            embeddings = []
            for text in texts:
                result = await self.embedding_model.generate_content_async(
                    text,
                    generation_config={"model": self.EMBEDDING_MODEL}
                )
                embeddings.append(result.embedding)
            return embeddings
            
        except Exception as e:
            raise Exception(f"Gemini Pro embedding generation failed: {str(e)}")
    
    def get_token_count(self, text: str) -> int:
        """Get the number of tokens in the text using Gemini's tokenizer.
        
        Args:
            text (str): Text to count tokens for
        
        Returns:
            int: Number of tokens
        """
        # Note: This is an approximation as Gemini doesn't provide a direct token count API
        # We use a rough estimate of 4 characters per token
        return len(text) // 4
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information for Gemini Pro.
        
        Returns:
            Dict[str, Any]: Rate limit details
        """
        # Note: Gemini Pro currently doesn't provide direct rate limit info
        # This is a placeholder for future implementation
        return {
            "requests_remaining": None,
            "requests_limit": None,
            "reset_time": None,
            "current_usage": None
        }
    
    def validate_api_key(self) -> bool:
        """Validate the Gemini Pro API key.
        
        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            # Attempt a simple generation to validate the API key
            self.model.generate_content("test")
            return True
        except Exception:
            return False 