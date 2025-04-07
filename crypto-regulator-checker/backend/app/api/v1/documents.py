from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.exceptions import DocumentNotFoundError, ValidationError, FileProcessingError
from app.crud.document import document as document_crud
from app.schemas.document import DocumentCreate, Document, ProcessingStatus
from app.core.database import get_db
import shutil
import os
from pathlib import Path

router = APIRouter()

UPLOAD_DIR = Path("uploads")
ALLOWED_MIME_TYPES = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

# Ensure upload directory exists
UPLOAD_DIR.mkdir(exist_ok=True)

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            message="Invalid file type",
            errors={"file_type": f"Must be one of: {', '.join(ALLOWED_MIME_TYPES)}"}
        )
    
    # Check file size (FastAPI handles this in chunks, so we need to read and discard)
    file_size = 0
    while chunk := file.file.read(8192):
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise ValidationError(
                message="File too large",
                errors={"file_size": f"Must be less than {MAX_FILE_SIZE // (1024 * 1024)}MB"}
            )
    file.file.seek(0)  # Reset file pointer

@router.post("/", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Document:
    """Upload a new document."""
    try:
        validate_file(file)
        
        # Save file
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record
        doc_in = DocumentCreate(
            filename=file.filename,
            file_type=file.content_type,
            size=os.path.getsize(file_path),
            file_path=str(file_path)
        )
        return document_crud.create(db=db, document=doc_in)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "errors": e.details}
        )
    except Exception as e:
        # Clean up file if creation fails
        if 'file_path' in locals():
            os.unlink(file_path)
        raise FileProcessingError(
            filename=file.filename,
            reason=str(e)
        )

@router.get("/{document_id}", response_model=Document)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> Document:
    """Get a document by ID."""
    try:
        return document_crud.get(db=db, document_id=document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "errors": e.details}
        )

@router.get("/", response_model=List[Document])
def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Document]:
    """List all documents with pagination."""
    return document_crud.get_multi(db=db, skip=skip, limit=limit)

@router.put("/{document_id}/status", response_model=Document)
def update_document_status(
    document_id: int,
    status_update: ProcessingStatus,
    db: Session = Depends(get_db)
) -> Document:
    """Update document processing status."""
    try:
        return document_crud.update_status(
            db=db,
            document_id=document_id,
            status_update=status_update
        )
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "errors": e.details}
        )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> None:
    """Delete a document."""
    try:
        document = document_crud.get(db=db, document_id=document_id)
        
        # Delete file first
        file_path = Path(document.file_path)
        if file_path.exists():
            os.unlink(file_path)
        
        # Then delete database record
        document_crud.delete(db=db, document_id=document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"message": e.message, "errors": e.details}
        ) 