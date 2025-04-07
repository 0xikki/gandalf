import pytest
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import UploadFile
from app.core.storage.file_service import SecureFileStorage
from app.core.exceptions import ValidationError, FileProcessingError

@pytest.fixture
def storage_service(tmp_path):
    """Create a storage service with temporary directories."""
    # Override settings for test
    import app.core.config
    app.core.config.settings.UPLOAD_DIR = str(tmp_path)
    
    service = SecureFileStorage()
    yield service
    
    # Cleanup after tests
    shutil.rmtree(tmp_path)

@pytest.fixture
def pdf_file(tmp_path):
    """Create a test PDF file."""
    file_path = tmp_path / "test.pdf"
    with open(file_path, "wb") as f:
        f.write(b"%PDF-1.5\n%Test PDF content")
    return file_path

@pytest.fixture
def docx_file(tmp_path):
    """Create a test DOCX file."""
    file_path = tmp_path / "test.docx"
    with open(file_path, "wb") as f:
        f.write(b"PK\x03\x04\x14\x00\x00\x00\x00\x00")  # DOCX magic number
    return file_path

@pytest.fixture
def large_file(tmp_path):
    """Create a large test file."""
    file_path = tmp_path / "large.pdf"
    with open(file_path, "wb") as f:
        f.write(b"0" * (26 * 1024 * 1024))  # 26MB
    return file_path

async def test_save_valid_pdf(storage_service, pdf_file):
    """Test saving a valid PDF file."""
    with open(pdf_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.pdf",
            file=f,
            content_type="application/pdf"
        )
        file_path, mime_type, size = await storage_service.save_file(upload_file)
    
    assert Path(file_path).exists()
    assert mime_type == "application/pdf"
    assert size > 0
    assert Path(file_path).stat().st_mode & 0o777 == 0o600

async def test_save_valid_docx(storage_service, docx_file):
    """Test saving a valid DOCX file."""
    with open(docx_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.docx",
            file=f,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        file_path, mime_type, size = await storage_service.save_file(upload_file)
    
    assert Path(file_path).exists()
    assert mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert size > 0

async def test_save_large_file(storage_service, large_file):
    """Test that large files are rejected."""
    with open(large_file, "rb") as f:
        upload_file = UploadFile(
            filename="large.pdf",
            file=f,
            content_type="application/pdf"
        )
        with pytest.raises(ValidationError) as exc_info:
            await storage_service.save_file(upload_file)
    
    assert "File too large" in str(exc_info.value)

async def test_save_invalid_type(storage_service, tmp_path):
    """Test that invalid file types are rejected."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("Plain text content")
    
    with open(text_file, "rb") as f:
        upload_file = UploadFile(
            filename="test.txt",
            file=f,
            content_type="text/plain"
        )
        with pytest.raises(ValidationError) as exc_info:
            await storage_service.save_file(upload_file)
    
    assert "Invalid file type" in str(exc_info.value)

def test_delete_file(storage_service, tmp_path):
    """Test file deletion."""
    # Create a file in the storage directory
    test_file = storage_service.storage_path / "test.pdf"
    test_file.write_bytes(b"%PDF-1.5\n%Test PDF content")
    
    storage_service.delete_file(str(test_file))
    assert not test_file.exists()

def test_delete_nonexistent_file(storage_service):
    """Test deleting a nonexistent file."""
    with pytest.raises(FileProcessingError) as exc_info:
        storage_service.delete_file("/nonexistent/file.pdf")
    assert "Failed to delete file" in str(exc_info.value)

def test_delete_outside_storage(storage_service, tmp_path):
    """Test that files outside storage directory cannot be deleted."""
    outside_file = tmp_path / "outside.pdf"
    outside_file.write_bytes(b"test content")
    
    with pytest.raises(FileProcessingError) as exc_info:
        storage_service.delete_file(str(outside_file))
    assert "Invalid file path" in str(exc_info.value)

async def test_cleanup_temp_files(storage_service):
    """Test temporary file cleanup."""
    # Create some old and new temp files
    old_file = storage_service.temp_path / "old.tmp"
    new_file = storage_service.temp_path / "new.tmp"
    
    old_file.write_bytes(b"old content")
    new_file.write_bytes(b"new content")
    
    # Set old file's modification time to 25 hours ago
    old_time = datetime.now() - timedelta(hours=25)
    os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
    
    await storage_service.cleanup_temp_files(max_age_hours=24)
    
    assert not old_file.exists()
    assert new_file.exists()

def test_get_file_info(storage_service):
    """Test getting file information."""
    # Create a test file
    test_file = storage_service.storage_path / "test.pdf"
    test_file.write_bytes(b"%PDF-1.5\n%Test PDF content")
    
    info = storage_service.get_file_info(str(test_file))
    assert info is not None
    assert info["name"] == "test.pdf"
    assert info["size"] > 0
    assert isinstance(info["created"], datetime)
    assert isinstance(info["modified"], datetime)
    assert info["mime_type"] == "application/pdf"

def test_get_file_info_nonexistent(storage_service):
    """Test getting info for nonexistent file."""
    info = storage_service.get_file_info("/nonexistent/file.pdf")
    assert info is None

def test_get_file_info_outside_storage(storage_service, tmp_path):
    """Test getting info for file outside storage directory."""
    outside_file = tmp_path / "outside.pdf"
    outside_file.write_bytes(b"test content")
    
    info = storage_service.get_file_info(str(outside_file))
    assert info is None 