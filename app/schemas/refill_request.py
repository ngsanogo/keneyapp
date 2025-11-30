"""
Schemas for prescription refill requests.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.prescription_refill import RefillRequestStatus


class RefillRequestBase(BaseModel):
    """Base schema for refill requests."""

    reason: Optional[str] = None
    patient_notes: Optional[str] = None
    pharmacy_name: Optional[str] = None
    pharmacy_phone: Optional[str] = None


class RefillRequestCreate(RefillRequestBase):
    """Schema for creating refill requests."""

    prescription_id: int = Field(..., gt=0)


class RefillRequestReview(BaseModel):
    """Schema for reviewing refill requests."""

    status: RefillRequestStatus = Field(..., description="approved or denied")
    review_notes: Optional[str] = None
    denial_reason: Optional[str] = Field(
        None, description="Required if status is denied"
    )
    new_prescription_id: Optional[int] = Field(
        None, description="If creating modified prescription"
    )


class RefillRequestResponse(RefillRequestBase):
    """Schema for refill request responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    prescription_id: int
    patient_id: int
    doctor_id: int
    status: RefillRequestStatus

    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    denial_reason: Optional[str] = None
    new_prescription_id: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    # Additional computed fields
    days_since_request: Optional[int] = None
    can_be_cancelled: Optional[bool] = None


class RefillRequestWithDetails(RefillRequestResponse):
    """Extended refill request with prescription details."""

    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None
