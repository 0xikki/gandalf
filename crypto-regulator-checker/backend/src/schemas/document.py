from typing import Optional
from pydantic import BaseModel

class DocumentBase(BaseModel):
    filename: str
    file_path: str
    file_type: str
    size: int

class DocumentCreate(DocumentBase):
    pass

class ProcessingStatus(BaseModel):
    status: str
    progress: float
    message: Optional[str] = None
    result: Optional[dict] = None

class Document(DocumentBase):
    id: int
    user_id: int
    status: str
    progress: float
    message: Optional[str] = None
    result: Optional[dict] = None

    class Config:
        from_attributes = True 