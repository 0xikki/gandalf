"""Document processing service."""
import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import UploadFile
from sqlalchemy.orm import Session
from src.core.config import settings
from src.models.document import Document
from src.services.document_processing.document_processor import DocumentProcessor

# Initialize logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

async def process_document(file: UploadFile, user_id: int, db: Session) -> str:
    """Process an uploaded document."""
    file_path = None
    try:
        # Create upload directory if it doesn't exist
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = upload_dir / f"{timestamp}_{file.filename}"
        
        # Save file
        logger.info(f"Saving file to {file_path}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create document record
        document = Document(
            filename=file.filename,
            file_path=str(file_path),
            user_id=user_id,
            status="processing"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document
        logger.info(f"Processing document {document.id}")
        processor = DocumentProcessor(str(file_path))
        text = processor.extract_text()
        text = processor.preprocess_text(text)
        chunks = processor.chunk_text(text)
        
        # Update document status
        document.status = "processed"
        document.processed_at = datetime.utcnow()
        db.commit()
        
        return document.id
    
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        if file_path and file_path.exists():
            file_path.unlink()
        raise 