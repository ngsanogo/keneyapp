"""
Prescription schemas for request/response validation.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class PrescriptionBase(BaseModel):
    """Base prescription schema with common fields."""

    patient_id: int
    doctor_id: int
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None
    refills: int = 0


class PrescriptionCreate(PrescriptionBase):
    """Schema for creating a new prescription."""

    pass


class PrescriptionResponse(PrescriptionBase):
    """Schema for prescription response."""

    id: int
    prescribed_date: datetime
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
