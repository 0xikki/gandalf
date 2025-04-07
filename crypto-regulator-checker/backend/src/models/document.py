"""Document model for database storage."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base

class Document(Base):
    """Document model."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, processing, processed, failed
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="documents")
    analysis_results = relationship("AnalysisResult", back_populates="document")

    def update_status(self, status: str):
        """Update document status."""
        self.status = status
        if status == "processed":
            self.processed_at = datetime.utcnow()

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "status": self.status,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        } 