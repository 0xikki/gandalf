"""Document processor class for handling document processing."""
import os
import logging
from pathlib import Path
from typing import List, Optional
import PyPDF2
from docx import Document

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Class for processing documents."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def __init__(self, file_path: str):
        """Initialize the document processor."""
        self.file_path = Path(file_path)
        
        if self.file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {self.file_path.suffix}")
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.debug(f"Initialized DocumentProcessor for {file_path}")

    def extract_text(self) -> str:
        """Extract text from the document."""
        try:
            if self.file_path.suffix.lower() == ".pdf":
                return self._extract_pdf_text()
            elif self.file_path.suffix.lower() == ".docx":
                return self._extract_docx_text()
            elif self.file_path.suffix.lower() == ".txt":
                return self._extract_txt_text()
            else:
                raise ValueError(f"Unsupported file type: {self.file_path.suffix}")
        except Exception as e:
            logger.error(f"Error extracting text from {self.file_path}: {e}")
            raise

    def _extract_pdf_text(self) -> str:
        """Extract text from a PDF file."""
        try:
            with open(self.file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {self.file_path}: {e}")
            raise

    def _extract_docx_text(self) -> str:
        """Extract text from a DOCX file."""
        try:
            doc = Document(self.file_path)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {self.file_path}: {e}")
            raise

    def _extract_txt_text(self) -> str:
        """Extract text from a TXT file."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text from TXT {self.file_path}: {e}")
            raise

    def preprocess_text(self, text: str) -> str:
        """Preprocess extracted text."""
        try:
            # Remove extra whitespace and normalize line breaks
            text = " ".join(text.split())
            return text
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into chunks."""
        try:
            # Split text into sentences
            sentences = text.split(".")
            sentences = [s.strip() + "." for s in sentences if s.strip()]
            
            # If chunk size is smaller than average sentence length, split by words
            if chunk_size < 50:  # Arbitrary threshold for small chunk size
                words = text.split()
                chunks = []
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i + chunk_size])
                    chunks.append(chunk)
                return chunks
            
            chunks = []
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                if current_length + sentence_length > chunk_size and current_chunk:
                    # Add current chunk to chunks
                    chunks.append(" ".join(current_chunk))
                    
                    # Keep overlapping sentences for next chunk
                    overlap_sentences = current_chunk[-overlap:] if overlap > 0 else []
                    current_chunk = overlap_sentences + [sentence]
                    current_length = sum(len(s) for s in current_chunk)
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length
            
            # Add the last chunk if it exists
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            return chunks
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise 