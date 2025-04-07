from typing import List, Optional
from sqlalchemy.orm import Session
from src.models.document import Document
from src.schemas.document import DocumentCreate, ProcessingStatus

def create_document(db: Session, *, document: DocumentCreate, user_id: int) -> Document:
    db_document = Document(
        filename=document.filename,
        file_path=document.file_path,
        file_type=document.file_type,
        size=document.size,
        user_id=user_id,
        status="pending",
        progress=0.0
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_document(db: Session, document_id: int) -> Optional[Document]:
    return db.query(Document).filter(Document.id == document_id).first()

def get_documents_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Document]:
    return db.query(Document).filter(Document.user_id == user_id).offset(skip).limit(limit).all()

def update_document_status(db: Session, *, document_id: int, status: ProcessingStatus) -> Optional[Document]:
    document = get_document(db, document_id)
    if not document:
        return None
    
    document.status = status.status
    document.progress = status.progress
    document.message = status.message
    if status.result:
        document.result = status.result
    
    db.commit()
    db.refresh(document)
    return document

def delete_document(db: Session, *, document_id: int) -> bool:
    document = get_document(db, document_id)
    if not document:
        return False
    
    db.delete(document)
    db.commit()
    return True 