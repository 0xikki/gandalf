"""Global configuration management."""

from typing import Optional, Dict, Any, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os
from functools import lru_cache

class ChunkingConfig(BaseSettings):
    """Configuration for document chunking."""
    chunk_size: int = Field(default=512, gt=0)
    chunk_overlap: int = Field(default=50, ge=0)
    min_chunk_size: int = Field(default=20, gt=0)
    split_on_newline: bool = True
    respect_sentences: bool = True

class EmbeddingsConfig(BaseSettings):
    """Configuration for embeddings generation."""
    model_name: str = Field(default="all-MiniLM-L6-v2")
    normalize_embeddings: bool = True
    max_seq_length: int = Field(default=512, gt=0)
    batch_size: int = Field(default=32, gt=0)
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")

class VectorStoreConfig(BaseSettings):
    """Configuration for vector store."""
    implementation: str = Field(default="chroma")
    collection_name: str = Field(default="regulations")
    persist_directory: str = Field(default="./data/vector_store")
    distance_metric: str = Field(default="cosine")
    embedding_dimension: int = Field(default=384)

class LLMConfig(BaseSettings):
    """Configuration for LLM service."""
    provider: str = Field(default="google")
    model_name: str = Field(default="gemini-pro")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, gt=0)
    cache_ttl: int = Field(default=3600)
    request_timeout: int = Field(default=30)

class RedisConfig(BaseSettings):
    """Configuration for Redis."""
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: Optional[str] = None
    socket_timeout: int = Field(default=5)
    socket_connect_timeout: int = Field(default=5)
    retry_on_timeout: bool = True
    health_check_interval: int = Field(default=30)

class CacheConfig(BaseSettings):
    """Configuration for caching."""
    backend: str = Field(default="redis")
    url: str = Field(default="redis://localhost:6379")
    default_ttl: int = Field(default=3600)
    max_memory: str = Field(default="1gb")
    eviction_policy: str = Field(default="allkeys-lru")

class LoggingConfig(BaseSettings):
    """Configuration for logging."""
    level: str = Field(default="INFO")
    format: str = Field(default="json")
    output_file: Optional[str] = Field(default=None)
    log_requests: bool = True
    log_responses: bool = True

class HealthConfig(BaseSettings):
    """Configuration for health checks."""
    enabled: bool = True
    check_interval: int = Field(default=30, description="Health check interval in seconds")
    timeout: int = Field(default=5, description="Health check timeout in seconds")
    failure_threshold: int = Field(default=3, description="Number of failures before marking unhealthy")
    success_threshold: int = Field(default=1, description="Number of successes before marking healthy")
    include_system_metrics: bool = True
    dependencies: list = Field(default=["redis"])

class Settings(BaseSettings):
    """Global application settings."""
    # Basic settings
    env: str = "development"
    debug: bool = True
    api_prefix: str = Field(default="/api/v1")
    version: str = Field(default="1.0.0")
    VERSION: str = Field(default="1.0.0")  # For backward compatibility
    
    # Host settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")  # For backward compatibility
    PORT: int = Field(default=8000)  # For backward compatibility
    
    # Service configurations
    chunking: ChunkingConfig = ChunkingConfig()
    embeddings: EmbeddingsConfig = EmbeddingsConfig()
    vector_store: VectorStoreConfig = VectorStoreConfig()
    llm: LLMConfig = LLMConfig()
    redis: RedisConfig = RedisConfig()
    cache: CacheConfig = CacheConfig()
    logging: LoggingConfig = LoggingConfig()
    health: HealthConfig = HealthConfig()
    
    # Security settings
    secret_key: str = os.environ.get("SECRET_KEY", "test-secret-key-for-testing-only")
    allowed_hosts: list = Field(default=["*"])
    cors_origins: list = Field(default=["*"])
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)  # seconds
    
    # File upload settings
    max_upload_size: int = Field(default=25 * 1024 * 1024)  # 25MB
    allowed_file_extensions: list = Field(default=[".pdf", ".docx"])
    MAX_UPLOAD_SIZE: int = Field(default=25 * 1024 * 1024)  # For backward compatibility
    ALLOWED_FILE_EXTENSIONS: list = Field(default=[".pdf", ".docx"])  # For backward compatibility
    
    # Project info
    PROJECT_NAME: str = "Crypto Regulator Checker"
    DESCRIPTION: str = "API for analyzing regulatory compliance of crypto documents"

    # API
    API_PREFIX: str = "/api"
    CORS_ORIGINS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "sqlite:///./test.db" if env == "test" else "sqlite:///./app.db"
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Authentication
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File upload
    UPLOAD_DIR: str = "uploads"

    # Performance
    ENABLE_METRICS: bool = True
    ENABLE_PROFILING: bool = False
    CACHE_TTL: int = 300  # 5 minutes
    RATE_LIMIT: int = 100  # requests per minute
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )
    
    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        if v == "your-secret-key-here":
            raise ValueError("Please set a proper secret key")
        return v

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Global settings instance
settings = get_settings()

# Example usage:
# settings = get_settings()
# chunk_size = settings.chunking.chunk_size
# model_name = settings.embeddings.model_name 