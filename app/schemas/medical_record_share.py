"""
Pydantic schemas for medical record sharing.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.medical_record_share import ShareScope, ShareStatus


class ShareCreate(BaseModel):
    """Schema for creating a new share."""

    patient_id: int = Field(..., description="Patient ID to share")
    scope: ShareScope = Field(..., description="Scope of data to share")
    custom_resources: Optional[dict] = Field(
        None, description="Custom resource selection for CUSTOM scope"
    )
    recipient_email: Optional[EmailStr] = Field(
        None, description="Optional: restrict access to this email"
    )
    recipient_name: Optional[str] = Field(
        None, max_length=255, description="Name of recipient"
    )
    expires_in_hours: int = Field(
        24, ge=1, le=720, description="Validity duration in hours (1h - 30 days)"
    )
    max_access_count: Optional[int] = Field(
        None, ge=1, description="Maximum number of accesses allowed"
    )
    require_pin: bool = Field(False, description="Require PIN for access")
    purpose: Optional[str] = Field(
        None, max_length=500, description="Purpose of sharing"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class ShareResponse(BaseModel):
    """Schema for share response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    shared_by_user_id: int
    share_token: str
    scope: ShareScope
    custom_resources: Optional[str]
    recipient_email: Optional[str]
    recipient_name: Optional[str]
    access_pin: Optional[str]  # Only returned on creation
    status: ShareStatus
    expires_at: datetime
    access_count: int
    max_access_count: Optional[int]
    last_accessed_at: Optional[datetime]
    purpose: Optional[str]
    notes: Optional[str]
    consent_given: bool
    consent_date: datetime
    tenant_id: str
    created_at: datetime
    updated_at: datetime


class ShareSummary(BaseModel):
    """Lightweight share summary."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    scope: ShareScope
    recipient_name: Optional[str]
    status: ShareStatus
    expires_at: datetime
    access_count: int
    created_at: datetime


class ShareAccessRequest(BaseModel):
    """Schema for accessing shared record."""

    token: str = Field(..., description="Share access token")
    pin: Optional[str] = Field(None, description="Access PIN if required")


class ShareAccessLog(BaseModel):
    """Log entry for share access."""

    share_id: int
    accessed_at: datetime
    accessed_by_ip: str
    success: bool
    failure_reason: Optional[str]


class SharedMedicalRecord(BaseModel):
    """Shared medical record data."""

    patient: dict  # Patient info (limited)
    appointments: Optional[List[dict]] = None
    prescriptions: Optional[List[dict]] = None
    documents: Optional[List[dict]] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    blood_type: Optional[str] = None
    scope: ShareScope
    accessed_at: datetime
