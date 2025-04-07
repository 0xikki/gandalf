"""Analysis result model for storing document analysis results."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.core.database import Base

class AnalysisResult(Base):
    """Analysis result model."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    result_type = Column(String, nullable=False)  # e.g., "sentiment", "classification", etc.
    result_data = Column(Text, nullable=False)  # JSON string of analysis results
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    document = relationship("Document", back_populates="analysis_results")

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "result_type": self.result_type,
            "result_data": self.result_data,
            "created_at": self.created_at.isoformat()
        } 