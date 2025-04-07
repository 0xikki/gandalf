from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.storage.file_service import SecureFileStorage
from app.core.exceptions import ValidationError, FileProcessingError
from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentResponse

router = APIRouter()
storage = SecureFileStorage()

@router.post("/upload/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Upload a document for processing.
    
    Args:
        file: The file to upload
        db: Database session
    
    Returns:
        DocumentResponse: Created document information
    
    Raises:
        HTTPException: If file upload or processing fails
    """
    try:
        # Save file using secure storage service
        file_path, mime_type, size = await storage.save_file(file)
        
        # Create document record in database
        doc = Document(
            filename=file.filename,
            file_path=file_path,
            file_type=mime_type,
            size=size,
            status="pending"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        return DocumentResponse.from_orm(doc)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileProcessingError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Delete file if database operation fails
        if 'file_path' in locals():
            storage.delete_file(file_path)
        raise HTTPException(status_code=500, detail="Failed to process upload")

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Get document information by ID.
    
    Args:
        document_id: The ID of the document
        db: Database session
    
    Returns:
        DocumentResponse: Document information
    
    Raises:
        HTTPException: If document not found
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.from_orm(doc)

@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[DocumentResponse]:
    """
    List all documents with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
    
    Returns:
        List[DocumentResponse]: List of documents
    """
    docs = db.query(Document).offset(skip).limit(limit).all()
    return [DocumentResponse.from_orm(doc) for doc in docs]

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Delete a document and its associated file.
    
    Args:
        document_id: The ID of the document to delete
        db: Database session
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException: If document not found or deletion fails
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete the physical file
        storage.delete_file(doc.file_path)
        
        # Delete database record
        db.delete(doc)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except FileProcessingError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete document") 