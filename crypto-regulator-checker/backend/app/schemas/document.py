from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentBase(BaseModel):
    """Base schema for document data."""
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    status: str = Field(
        ...,
        description="Processing status",
        pattern="^(pending|processing|completed|failed)$"
    )
    progress: Optional[int] = Field(
        None,
        description="Processing progress (0-100)",
        ge=0,
        le=100
    )
    message: Optional[str] = Field(None, description="Status message or error details")

class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    file_path: str = Field(..., description="Path to stored file")

class DocumentResponse(DocumentBase):
    """Schema for document responses."""
    id: int = Field(..., description="Document ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    result: Optional[dict] = Field(None, description="Processing results")
    
    class Config:
        """Pydantic model configuration."""
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProcessingStatus(BaseModel):
    status: str = Field(..., description="Current processing status (pending, processing, completed, failed)")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Processing progress percentage")
    message: Optional[str] = Field(None, description="Status message or error description")
    result: Optional[Dict[str, Any]] = Field(None, description="Processing results in JSON format")

class DocumentUpdate(ProcessingStatus):
    pass

class Document(DocumentBase):
    id: int
    file_path: str
    status: str
    progress: float
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 