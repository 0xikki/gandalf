from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, text
from sqlalchemy.sql import func
from app.models.base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)
    size = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, index=True)
    progress = Column(Float, nullable=True)
    message = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) 