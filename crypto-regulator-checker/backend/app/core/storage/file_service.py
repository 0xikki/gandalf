import os
import shutil
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Dict
from fastapi import UploadFile
import aiofiles
import magic
from app.core.exceptions import FileProcessingError, ValidationError
from app.core.config import settings
from app.core.config.storage import storage_settings

class SecureFileStorage:
    """Secure file storage service with enhanced validation and chunked upload support."""
    
    ALLOWED_MIME_TYPES = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"
    }
    
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
    CHUNK_SIZE = 8192  # 8KB chunks for reading
    
    def __init__(self):
        """Initialize storage service with configured paths."""
        self.storage_path = storage_settings.UPLOAD_DIR
        self.temp_path = storage_settings.TEMP_DIR
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure storage directories exist with proper permissions."""
        storage_settings.create_directories()
    
    async def save_file(self, file: UploadFile) -> Tuple[str, str, int]:
        """
        Save an uploaded file securely with enhanced validation.
        
        Args:
            file: The uploaded file
            
        Returns:
            Tuple[str, str, int]: (file path, mime type, file size)
            
        Raises:
            ValidationError: If file validation fails
            FileProcessingError: If file processing fails
        """
        try:
            # Create temporary file for validation
            temp_path = self.temp_path / f"temp_{datetime.now().timestamp()}"
            size = 0
            
            # Read file in chunks to handle large files
            with open(temp_path, "wb") as temp_file:
                while chunk := await file.read(storage_settings.CHUNK_SIZE):
                    size += len(chunk)
                    if size > storage_settings.MAX_FILE_SIZE:
                        os.unlink(temp_path)
                        raise ValidationError("File too large")
                    temp_file.write(chunk)
            
            # Validate actual file content
            mime_type = self._get_mime_type(temp_path)
            if mime_type not in storage_settings.ALLOWED_MIME_TYPES:
                os.unlink(temp_path)
                raise ValidationError(f"Invalid file type: {mime_type}")
            
            # Generate secure filename using hash
            file_hash = self._calculate_file_hash(temp_path)
            ext = Path(file.filename).suffix
            secure_filename = f"{file_hash}{ext}"
            final_path = self.storage_path / secure_filename
            
            # Move file to final location with secure permissions
            shutil.move(temp_path, final_path)
            os.chmod(final_path, storage_settings.FILE_PERMISSIONS)
            
            return str(final_path), mime_type, size
            
        except (OSError, IOError) as e:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise FileProcessingError(f"Failed to process file: {str(e)}")
    
    def _get_mime_type(self, file_path: Path) -> str:
        """
        Get actual MIME type from file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: MIME type
        """
        mime = magic.Magic(mime=True)
        return mime.from_file(str(file_path))
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file for secure naming.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: File hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(storage_settings.CHUNK_SIZE):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def delete_file(self, file_path: str) -> None:
        """
        Delete a file securely.
        
        Args:
            file_path: Path to the file to delete
            
        Raises:
            FileProcessingError: If deletion fails
        """
        path = Path(file_path)
        if not path.is_relative_to(self.storage_path):
            raise FileProcessingError("Invalid file path")
            
        try:
            if path.exists():
                os.unlink(path)
            else:
                raise FileProcessingError("Failed to delete file: File not found")
        except OSError as e:
            raise FileProcessingError(f"Failed to delete file: {str(e)}")
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> None:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of temporary files in hours
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        for temp_file in self.temp_path.glob("temp_*"):
            try:
                mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                if mtime < cutoff:
                    os.unlink(temp_file)
            except OSError:
                continue
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """
        Get information about a stored file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[Dict]: File information or None if file not found
        """
        path = Path(file_path)
        if not path.is_relative_to(self.storage_path) or not path.exists():
            return None
            
        try:
            stat = path.stat()
            return {
                "name": path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "mime_type": self._get_mime_type(path)
            }
        except OSError:
            return None 