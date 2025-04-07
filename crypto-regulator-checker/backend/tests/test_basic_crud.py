import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.document import Document
from app.models.base import Base
from app.crud.document import document as document_crud
from app.schemas.document import DocumentCreate, ProcessingStatus
from app.core.exceptions import DocumentNotFoundError, DatabaseError
from sqlalchemy.exc import SQLAlchemyError
from .factories import DocumentCreateFactory, ProcessingStatusFactory

# Test database URL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:0xf0rdsn0tbr0gues@localhost/crypto_regulator_test"

# Setup and teardown
@pytest.fixture(scope="module")
def engine():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_create_document(db_session):
    doc_in = DocumentCreateFactory()
    doc = document_crud.create(db=db_session, document=doc_in)
    
    assert doc.filename == doc_in.filename
    assert doc.file_type == doc_in.file_type
    assert doc.size == doc_in.size
    assert doc.status == "pending"
    assert doc.progress == 0.0

def test_create_document_with_db_error(db_session, mocker):
    doc_in = DocumentCreateFactory()
    
    # Mock SQLAlchemy to raise an error
    mocker.patch.object(db_session, 'add', side_effect=SQLAlchemyError("Database error"))
    
    with pytest.raises(DatabaseError) as exc_info:
        document_crud.create(db=db_session, document=doc_in)
    assert exc_info.value.status_code == 500
    assert "Error creating document" in exc_info.value.message

def test_get_document(db_session):
    doc_in = DocumentCreateFactory()
    created_doc = document_crud.create(db=db_session, document=doc_in)
    
    doc = document_crud.get(db=db_session, document_id=created_doc.id)
    assert doc is not None
    assert doc.filename == created_doc.filename
    assert doc.size == created_doc.size

def test_get_nonexistent_document(db_session):
    with pytest.raises(DocumentNotFoundError) as exc_info:
        document_crud.get(db=db_session, document_id=99999)
    assert exc_info.value.status_code == 404
    assert "99999" in exc_info.value.message

def test_update_document_status(db_session):
    doc_in = DocumentCreateFactory()
    doc = document_crud.create(db=db_session, document=doc_in)
    
    status_update = ProcessingStatusFactory(status="processing")
    updated_doc = document_crud.update_status(
        db=db_session,
        document_id=doc.id,
        status_update=status_update
    )
    
    assert updated_doc is not None
    assert updated_doc.status == status_update.status
    assert updated_doc.progress == status_update.progress
    assert updated_doc.message == status_update.message
    assert updated_doc.result == status_update.result

def test_update_nonexistent_document(db_session):
    status_update = ProcessingStatusFactory()
    
    with pytest.raises(DocumentNotFoundError) as exc_info:
        document_crud.update_status(
            db=db_session,
            document_id=99999,
            status_update=status_update
        )
    assert exc_info.value.status_code == 404
    assert "99999" in exc_info.value.message

def test_update_document_with_db_error(db_session, mocker):
    doc_in = DocumentCreateFactory()
    doc = document_crud.create(db=db_session, document=doc_in)
    
    status_update = ProcessingStatusFactory()
    
    # Mock SQLAlchemy to raise an error
    mocker.patch.object(db_session, 'commit', side_effect=SQLAlchemyError("Database error"))
    
    with pytest.raises(DatabaseError) as exc_info:
        document_crud.update_status(
            db=db_session,
            document_id=doc.id,
            status_update=status_update
        )
    assert exc_info.value.status_code == 500
    assert "Error updating document" in exc_info.value.message

def test_delete_document(db_session):
    doc_in = DocumentCreateFactory()
    doc = document_crud.create(db=db_session, document=doc_in)
    
    result = document_crud.delete(db=db_session, document_id=doc.id)
    assert result is True
    
    with pytest.raises(DocumentNotFoundError) as exc_info:
        document_crud.get(db=db_session, document_id=doc.id)
    assert exc_info.value.status_code == 404

def test_delete_nonexistent_document(db_session):
    with pytest.raises(DocumentNotFoundError) as exc_info:
        document_crud.delete(db=db_session, document_id=99999)
    assert exc_info.value.status_code == 404
    assert "99999" in exc_info.value.message

def test_delete_document_with_db_error(db_session, mocker):
    doc_in = DocumentCreateFactory()
    doc = document_crud.create(db=db_session, document=doc_in)
    
    # Mock SQLAlchemy to raise an error
    mocker.patch.object(db_session, 'delete', side_effect=SQLAlchemyError("Database error"))
    
    with pytest.raises(DatabaseError) as exc_info:
        document_crud.delete(db=db_session, document_id=doc.id)
    assert exc_info.value.status_code == 500
    assert "Error deleting document" in exc_info.value.message 