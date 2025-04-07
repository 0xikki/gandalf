"""Tests for document processing functionality."""

import os
import tempfile
from pathlib import Path
import pytest
from docx import Document as DocxDocument
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from sqlalchemy.orm import Session
from PyPDF2 import PdfWriter

from src.services.document_processing.document_processor import DocumentProcessor
from src.services.document_processor import process_document
from src.models.document import Document
from src.core.config import settings

@pytest.fixture
def test_pdf_file():
    """Create a test PDF file."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    try:
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(temp_file)
        temp_file.close()  # Close the file before yielding
        yield temp_file.name
    finally:
        if os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except PermissionError:
                pass  # Ignore permission errors during cleanup

@pytest.fixture
def test_docx_file():
    """Create a test DOCX file."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    try:
        doc = DocxDocument()
        doc.add_paragraph("Test content")
        doc.save(temp_file.name)
        temp_file.close()  # Close the file before yielding
        yield temp_file.name
    finally:
        if os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except PermissionError:
                pass  # Ignore permission errors during cleanup

def test_init_with_invalid_file():
    """Test initialization with invalid file."""
    with pytest.raises(ValueError):
        DocumentProcessor("test.xyz")  # Unsupported extension

    with pytest.raises(FileNotFoundError):
        DocumentProcessor("nonexistent.pdf")

def test_extract_pdf_text(test_pdf_file):
    """Test extracting text from a PDF file."""
    processor = DocumentProcessor(test_pdf_file)
    text = processor.extract_text()
    assert isinstance(text, str)

def test_extract_docx_text(test_docx_file):
    """Test extracting text from a DOCX file."""
    processor = DocumentProcessor(test_docx_file)
    text = processor.extract_text()
    assert text.strip() == "Test content"

def test_preprocess_text(test_pdf_file):
    """Test text preprocessing."""
    processor = DocumentProcessor(test_pdf_file)
    text = "  Multiple   spaces   and\nline\nbreaks  "
    processed = processor.preprocess_text(text)
    assert processed == "Multiple spaces and line breaks"

def test_chunk_text(test_pdf_file):
    """Test text chunking."""
    processor = DocumentProcessor(test_pdf_file)
    
    # Test word-based chunking (small chunk size)
    text = "This is a test. Another sentence. Yet another one."
    chunks = processor.chunk_text(text, chunk_size=2, overlap=0)
    assert len(chunks) == 5  # ["This is", "a test.", "Another sentence.", "Yet another", "one."]
    
    # Test sentence-based chunking (larger chunk size)
    text = "This is a test. Another sentence. Yet another one."
    chunks = processor.chunk_text(text, chunk_size=100, overlap=0)
    assert len(chunks) == 1  # All sentences fit in one chunk

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock(spec=Session)
    db.commit = Mock()
    db.refresh = Mock()
    db.add = Mock()
    return db

@pytest.fixture
def mock_file():
    """Create a mock upload file."""
    file = Mock(spec=UploadFile)
    file.filename = "test_document.pdf"
    file.read = AsyncMock(return_value=b"test content")
    return file

@pytest.mark.asyncio
async def test_process_document_success(mock_db, mock_file, tmp_path):
    """Test successful document processing."""
    # Create a test text file (simpler than PDF for testing)
    test_file = tmp_path / "test_document.txt"
    with open(test_file, "w") as f:
        f.write("Test content for document processing.")
    
    # Mock the file object
    mock_file.filename = "test_document.txt"
    with open(test_file, "rb") as f:
        file_content = f.read()
    
    # Mock the async read method
    async def mock_read():
        return file_content
    
    mock_file.read = mock_read
    
    # Mock the database session
    mock_document = Mock()
    mock_document.id = 1
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    mock_db.refresh.side_effect = lambda x: setattr(x, 'id', 1)
    
    with patch('src.services.document_processor.settings') as mock_settings:
        # Setup mocks
        mock_settings.UPLOAD_DIR = str(tmp_path)
        
        # Process document
        user_id = 1
        document_id = await process_document(mock_file, user_id, mock_db)
        
        # Verify document was processed
        assert document_id == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called()  # Called twice

@pytest.mark.asyncio
async def test_process_document_file_error(mock_db, mock_file):
    """Test handling of file save errors."""
    with patch('builtins.open') as mock_open:
        mock_open.side_effect = IOError("Failed to save file")
        
        with pytest.raises(Exception) as exc_info:
            await process_document(mock_file, 1, mock_db)
        
        assert "Failed to save file" in str(exc_info.value)
        assert not mock_db.add.called

@pytest.mark.asyncio
async def test_process_document_analysis_error(mock_db, mock_file, tmp_path):
    """Test handling of analysis errors."""
    with patch('src.services.document_processor.settings') as mock_settings, \
         patch('src.services.document_processing.document_processor.DocumentProcessor.extract_text') as mock_extract:
        
        # Setup mocks
        mock_settings.UPLOAD_DIR = str(tmp_path)
        mock_extract.side_effect = Exception("Analysis failed")
        
        with pytest.raises(Exception) as exc_info:
            await process_document(mock_file, 1, mock_db)
        
        # Verify error handling
        assert "Analysis failed" in str(exc_info.value)
        
        # Verify file cleanup
        saved_files = list(tmp_path.glob("*"))
        assert len(saved_files) == 0  # File should be deleted

@pytest.mark.asyncio
async def test_process_document_db_error(mock_db, mock_file, tmp_path):
    """Test handling of database errors."""
    with patch('src.services.document_processor.settings') as mock_settings:
        # Setup mocks
        mock_settings.UPLOAD_DIR = str(tmp_path)
        mock_db.add.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            await process_document(mock_file, 1, mock_db)
        
        # Verify error handling
        assert "Database error" in str(exc_info.value)
        
        # Verify file cleanup
        saved_files = list(tmp_path.glob("*"))
        assert len(saved_files) == 0  # File should be deleted

if __name__ == '__main__':
    pytest.main() 