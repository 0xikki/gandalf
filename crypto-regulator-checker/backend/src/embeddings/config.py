"""Configuration for embeddings generation."""

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class EmbeddingsConfig:
    """Configuration for embeddings generation."""
    
    model_name: str = "all-MiniLM-L6-v2"
    max_seq_length: int = 512
    batch_size: int = 32
    device: Optional[str] = None
    normalize_embeddings: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not isinstance(self.model_name, str) or not self.model_name:
            raise ValueError("Model name must be a non-empty string")
        if not isinstance(self.max_seq_length, int) or self.max_seq_length <= 0:
            raise ValueError("Max sequence length must be a positive integer")
        if not isinstance(self.batch_size, int) or self.batch_size <= 0:
            raise ValueError("Batch size must be a positive integer")
        if self.device is not None and not isinstance(self.device, str):
            raise ValueError("Device must be a string or None")
        if not isinstance(self.normalize_embeddings, bool):
            raise ValueError("normalize_embeddings must be a boolean") 