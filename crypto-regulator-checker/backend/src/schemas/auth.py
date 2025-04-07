"""Authentication schemas for request/response models."""
from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str

class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    """User creation model."""
    password: str

class UserResponse(UserBase):
    """User response model."""
    id: int
    is_active: bool
    is_admin: bool

    class Config:
        """Pydantic config."""
        from_attributes = True 