from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate, ProcessingStatus
from app.core.exceptions import DocumentNotFoundError, DatabaseError

class DocumentCRUD:
    @staticmethod
    def create(db: Session, *, document: DocumentCreate) -> Document:
        try:
            db_document = Document(
                filename=document.filename,
                file_path=document.file_path,
                file_type=document.file_type,
                size=document.size,
                status="pending",
                progress=0.0
            )
            db.add(db_document)
            db.commit()
            db.refresh(db_document)
            return db_document
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(
                operation="create_document",
                details={"error": str(e), "document": document.dict()}
            )

    @staticmethod
    def get(db: Session, document_id: int) -> Document:
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise DocumentNotFoundError(document_id)
            return document
        except SQLAlchemyError as e:
            raise DatabaseError(
                operation="get_document",
                details={"error": str(e), "document_id": document_id}
            )

    @staticmethod
    def get_multi(db: Session, *, skip: int = 0, limit: int = 100) -> List[Document]:
        try:
            return db.query(Document).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(
                operation="get_multi_documents",
                details={"error": str(e), "skip": skip, "limit": limit}
            )

    @staticmethod
    def update_status(db: Session, *, document_id: int, status_update: ProcessingStatus) -> Document:
        try:
            document = DocumentCRUD.get(db, document_id)
            
            document.status = status_update.status
            document.progress = status_update.progress
            if status_update.message:
                document.message = status_update.message
            if status_update.result:
                document.result = status_update.result
            
            db.commit()
            db.refresh(document)
            return document
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(
                operation="update_document_status",
                details={
                    "error": str(e),
                    "document_id": document_id,
                    "status_update": status_update.dict()
                }
            )

    @staticmethod
    def delete(db: Session, *, document_id: int) -> bool:
        try:
            document = DocumentCRUD.get(db, document_id)
            db.delete(document)
            db.commit()
            return True
        except DocumentNotFoundError:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseError(
                operation="delete_document",
                details={"error": str(e), "document_id": document_id}
            )

document = DocumentCRUD() 