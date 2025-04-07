from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from ..conftest import engine, db_session, clean_db
from ..factories import DocumentCreateFactory, ProcessingStatusFactory

client = TestClient(app)

# Override the database dependency
def override_get_db():
    try:
        db = db_session
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def test_create_document(clean_db, tmp_path):
    # Create a test file
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"test content")
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["file_type"] == "application/pdf"
    assert data["status"] == "pending"
    assert data["progress"] == 0.0

def test_create_document_invalid_type(clean_db, tmp_path):
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"test content")
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("test.txt", f, "text/plain")}
        )
    
    assert response.status_code == 422
    data = response.json()
    assert "Invalid file type" in data["detail"]["message"]

def test_create_document_too_large(clean_db, tmp_path):
    # Create a large test file (26MB)
    test_file = tmp_path / "large.pdf"
    test_file.write_bytes(b"0" * (26 * 1024 * 1024))
    
    with open(test_file, "rb") as f:
        response = client.post(
            "/api/v1/documents/",
            files={"file": ("large.pdf", f, "application/pdf")}
        )
    
    assert response.status_code == 422
    data = response.json()
    assert "File too large" in data["detail"]["message"]

def test_get_document(clean_db):
    # First create a document
    doc_in = DocumentCreateFactory()
    doc = client.post(
        "/api/v1/documents/",
        files={"file": ("test.pdf", b"test content", "application/pdf")}
    ).json()
    
    # Then get it
    response = client.get(f"/api/v1/documents/{doc['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc["id"]
    assert data["filename"] == doc["filename"]

def test_get_nonexistent_document(clean_db):
    response = client.get("/api/v1/documents/99999")
    assert response.status_code == 404
    data = response.json()
    assert "99999" in data["detail"]["message"]

def test_list_documents(clean_db):
    # Create multiple documents
    for _ in range(3):
        client.post(
            "/api/v1/documents/",
            files={"file": ("test.pdf", b"test content", "application/pdf")}
        )
    
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

def test_update_document_status(clean_db):
    # Create a document
    doc = client.post(
        "/api/v1/documents/",
        files={"file": ("test.pdf", b"test content", "application/pdf")}
    ).json()
    
    # Update its status
    status_update = ProcessingStatusFactory(
        status="processing",
        progress=50.0,
        message="Processing document..."
    )
    
    response = client.put(
        f"/api/v1/documents/{doc['id']}/status",
        json=status_update.dict()
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["progress"] == 50.0
    assert data["message"] == "Processing document..."

def test_update_nonexistent_document_status(clean_db):
    status_update = ProcessingStatusFactory()
    response = client.put(
        "/api/v1/documents/99999/status",
        json=status_update.dict()
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "99999" in data["detail"]["message"]

def test_delete_document(clean_db):
    # Create a document
    doc = client.post(
        "/api/v1/documents/",
        files={"file": ("test.pdf", b"test content", "application/pdf")}
    ).json()
    
    # Delete it
    response = client.delete(f"/api/v1/documents/{doc['id']}")
    assert response.status_code == 204
    
    # Verify it's gone
    response = client.get(f"/api/v1/documents/{doc['id']}")
    assert response.status_code == 404

def test_delete_nonexistent_document(clean_db):
    response = client.delete("/api/v1/documents/99999")
    assert response.status_code == 404
    data = response.json()
    assert "99999" in data["detail"]["message"]