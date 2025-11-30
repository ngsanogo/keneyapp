from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AppointmentBase(BaseModel):
    patient_id: int = Field(..., gt=0)
    doctor_id: int = Field(..., gt=0)
    appointment_date: datetime
    duration_minutes: int = Field(30, ge=1, le=480)
    status: Optional[str] = None
    reason: str
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=480)
    status: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
"""
Appointment schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
