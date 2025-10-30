"""
Appointment schemas for request/response validation.
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    """Base appointment schema with common fields."""

    patient_id: int
    doctor_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    reason: str
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Schema for creating a new appointment."""

    pass


class AppointmentUpdate(BaseModel):
    """Schema for updating appointment information."""

    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    status: Optional[AppointmentStatus] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    """Schema for appointment response."""

    id: int
    status: AppointmentStatus
    tenant_id: int

    model_config = ConfigDict(from_attributes=True)
