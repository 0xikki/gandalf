import pytest
from sqlalchemy.orm import Session
from app.crud.document import document as document_crud
from app.schemas.document import DocumentCreate, ProcessingStatus
from app.models.document import Document

def test_create_document(db: Session) -> None:
    doc_in = DocumentCreate(
        filename="test.pdf",
        file_type="application/pdf",
        size=1024,
        file_path="/tmp/test.pdf"
    )
    doc = document_crud.create(db=db, document=doc_in)
    assert doc.filename == "test.pdf"
    assert doc.file_type == "application/pdf"
    assert doc.size == 1024
    assert doc.status == "pending"
    assert doc.progress == 0.0

def test_get_document(db: Session) -> None:
    doc_in = DocumentCreate(
        filename="get_test.pdf",
        file_type="application/pdf",
        size=2048,
        file_path="/tmp/get_test.pdf"
    )
    doc = document_crud.create(db=db, document=doc_in)
    stored_doc = document_crud.get(db=db, document_id=doc.id)
    assert stored_doc
    assert stored_doc.id == doc.id
    assert stored_doc.filename == doc.filename

def test_update_document_status(db: Session) -> None:
    doc_in = DocumentCreate(
        filename="update_test.pdf",
        file_type="application/pdf",
        size=3072,
        file_path="/tmp/update_test.pdf"
    )
    doc = document_crud.create(db=db, document=doc_in)
    
    status_update = ProcessingStatus(
        status="processing",
        progress=50.0,
        message="Processing document...",
        result={"page_count": 5}
    )
    
    updated_doc = document_crud.update_status(
        db=db,
        document_id=doc.id,
        status_update=status_update
    )
    
    assert updated_doc
    assert updated_doc.status == "processing"
    assert updated_doc.progress == 50.0
    assert updated_doc.message == "Processing document..."
    assert updated_doc.result == {"page_count": 5}

def test_delete_document(db: Session) -> None:
    doc_in = DocumentCreate(
        filename="delete_test.pdf",
        file_type="application/pdf",
        size=4096,
        file_path="/tmp/delete_test.pdf"
    )
    doc = document_crud.create(db=db, document=doc_in)
    
    result = document_crud.delete(db=db, document_id=doc.id)
    assert result is True
    
    deleted_doc = document_crud.get(db=db, document_id=doc.id)
    assert deleted_doc is None 