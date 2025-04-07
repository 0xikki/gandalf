from pathlib import Path
from typing import Set

from pydantic import BaseModel, Field

class StorageSettings(BaseModel):
    """Configuration settings for file storage."""
    
    # Base directory for file uploads
    UPLOAD_DIR: Path = Field(
        default=Path("uploads"),
        description="Base directory for file uploads"
    )
    
    # Maximum file size in bytes (25MB)
    MAX_FILE_SIZE: int = Field(
        default=25 * 1024 * 1024,
        description="Maximum file size in bytes"
    )
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES: Set[str] = Field(
        default={
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        },
        description="Set of allowed MIME types"
    )
    
    # File permissions (0o600 = user read/write only)
    FILE_PERMISSIONS: int = Field(
        default=0o600,
        description="File permissions in octal"
    )
    
    # Temporary file cleanup settings
    TEMP_FILE_MAX_AGE_HOURS: int = Field(
        default=24,
        description="Maximum age of temporary files in hours"
    )
    TEMP_DIR: Path = Field(
        default=Path("uploads/temp"),
        description="Directory for temporary files"
    )
    
    # Chunk size for reading large files (1MB)
    CHUNK_SIZE: int = Field(
        default=1024 * 1024,
        description="Chunk size for reading files in bytes"
    )
    
    class Config:
        """Pydantic model configuration."""
        validate_assignment = True
        
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Set directory permissions to be secure (0o700 = user read/write/execute only)
        self.UPLOAD_DIR.chmod(0o700)
        self.TEMP_DIR.chmod(0o700)

# Create settings instance
storage_settings = StorageSettings()

# Create directories on import
storage_settings.create_directories() 