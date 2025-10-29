"""
User schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str
    full_name: str
    role: UserRole


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    username: Optional[str] = None
