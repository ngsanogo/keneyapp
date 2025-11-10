"""
Patient schemas for request/response validation.
"""

from datetime import date, datetime
from typing import Optional
import re

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
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
    ins_number: Optional[str] = None
    social_security_number: Optional[str] = None
    
    @field_validator('ins_number')
    @classmethod
    def validate_ins(cls, v: Optional[str]) -> Optional[str]:
        """Validate INS format: 1YYMMSSNNNCCCXX (15 digits)."""
        if v is None:
            return v
        # Remove spaces and formatting
        v_clean = v.replace(" ", "").replace("-", "")
        if not v_clean.isdigit() or len(v_clean) != 15:
            raise ValueError('INS must be 15 digits in format 1YYMMSSNNNCCCXX')
        if not v_clean.startswith('1'):
            raise ValueError('INS must start with 1')
        return v_clean
    
    @field_validator('social_security_number')
    @classmethod
    def validate_ssn(cls, v: Optional[str]) -> Optional[str]:
        """Validate French Social Security Number (NIR): 13 digits + 2 key digits."""
        if v is None:
            return v
        v_clean = v.replace(" ", "").replace("-", "")
        if not v_clean.isdigit() or len(v_clean) != 15:
            raise ValueError('Social Security Number must be 15 digits (13 + 2 key)')
        return v_clean


class PatientCreate(PatientBase):
    """Schema for creating a new patient."""

    pass


class PatientUpdate(BaseModel):
    """Schema for updating an existing patient."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    ins_number: Optional[str] = None
    social_security_number: Optional[str] = None


class PatientResponse(PatientBase):
    """Schema for patient response."""

    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
