"""
Patient schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date
from typing import Optional
from app.models.patient import Gender


class PatientBase(BaseModel):
    """Base patient schema with common fields."""

    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender
    email: Optional[EmailStr] = None
    phone: str
    address: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""

    pass


class PatientUpdate(BaseModel):
    """Schema for updating patient information."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientResponse(PatientBase):
    """Schema for patient response."""

    id: int
    tenant_id: int

    model_config = ConfigDict(from_attributes=True)
