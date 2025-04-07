"""Document processing endpoints."""
import os
import magic
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from src.core.config import settings
from src.core.database import get_db
from src.models.user import User
from src.models.document import Document
from .auth import get_current_user
from src.services.document_processor import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

# Maximum file size from settings
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'text/plain',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

def validate_file(file: UploadFile) -> None:
    """Validate file size and type."""
    # Check file size
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # Check file type
    content = file.file.read(2048)  # Read first 2KB for MIME detection
    file.file.seek(0)
    mime = magic.from_buffer(content, mime=True)
    
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {mime} not allowed. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Check for malicious content (basic check)
    content = content.lower()
    if b'<script' in content or b'<?php' in content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File contains potentially malicious content"
        )

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="File to upload"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document for analysis."""
    try:
        # Check file size from content length header
        content_length = int(file.headers.get("content-length", 0))
        if content_length > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE/1024/1024}MB"
            )
        
        # Validate file
        validate_file(file)
        
        # Process document
        document_id = await process_document(file, current_user.id, db)
        return {"document_id": document_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{document_id}/analysis")
async def get_analysis_results(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analysis results for a document."""
    # Verify document belongs to user
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document.analysis_results 