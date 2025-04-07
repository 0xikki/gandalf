"""Base module for database models."""
from src.core.database import Base
from src.models.user import User
from src.models.document import Document
from src.models.analysis_result import AnalysisResult

# Import all models here
__all__ = [
    "Base",
    "User",
    "Document",
    "AnalysisResult",
] 