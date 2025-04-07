from typing import List
from pydantic import BaseModel, Field, validator
from app.core.config.settings import settings

class CORSSettings(BaseModel):
    """Configuration settings for CORS."""
    
    # List of allowed origins
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",  # Development frontend
            "http://localhost:8000",  # Development API
        ],
        description="List of allowed origins"
    )
    
    # List of allowed HTTP methods
    ALLOWED_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="List of allowed HTTP methods"
    )
    
    # List of allowed HTTP headers
    ALLOWED_HEADERS: List[str] = Field(
        default=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
        description="List of allowed HTTP headers"
    )
    
    # List of headers exposed to the browser
    EXPOSED_HEADERS: List[str] = Field(
        default=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Request-ID",
        ],
        description="List of headers exposed to the browser"
    )
    
    # Maximum age for CORS preflight requests (in seconds)
    MAX_AGE: int = Field(
        default=600,  # 10 minutes
        description="Maximum age for CORS preflight requests in seconds"
    )
    
    # Whether to allow credentials (cookies, authorization headers)
    ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Whether to allow credentials"
    )
    
    @validator("ALLOWED_ORIGINS")
    def validate_origins(cls, v: List[str]) -> List[str]:
        """Validate and process allowed origins."""
        # In production, ensure only specific domains are allowed
        if settings.ENVIRONMENT == "production":
            v = [origin for origin in v if not origin.startswith("http://localhost")]
            if not v:
                raise ValueError("No production origins configured")
        return v
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True

# Create settings instance
cors_settings = CORSSettings()

# If in production, add production domains
if settings.ENVIRONMENT == "production":
    cors_settings.ALLOWED_ORIGINS.extend([
        # Add your production domains here
        # Example: "https://app.example.com"
    ]) 