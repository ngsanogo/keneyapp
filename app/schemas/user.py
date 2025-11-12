"""
User schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    tenant_id: int


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    tenant_id: int
    is_active: bool
    is_locked: bool
    mfa_enabled: bool
    last_login: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""

    username: Optional[str] = None
    role: Optional[UserRole] = None
    tenant_id: Optional[int] = None


class UserStatusUpdate(BaseModel):
    """Update user activation or lock status."""

    is_active: Optional[bool] = None
    is_locked: Optional[bool] = None


class UserRoleUpdate(BaseModel):
    """Update the role of a user."""

    role: UserRole


class UserPasswordReset(BaseModel):
    """Admin initiated password reset."""

    new_password: str = Field(min_length=8)


class ChangePasswordRequest(BaseModel):
    """User initiated password change."""

    current_password: str
    new_password: str = Field(min_length=8)


class MFASetupResponse(BaseModel):
    """Payload for MFA provisioning."""

    secret: str
    provisioning_uri: str


class MFAVerifyRequest(BaseModel):
    """Payload for verifying MFA codes."""

    code: str
