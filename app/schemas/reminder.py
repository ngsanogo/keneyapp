"""
Pydantic schemas for appointment reminders.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment_reminder import ReminderChannel, ReminderStatus


class ReminderBase(BaseModel):
    """Base schema for appointment reminders."""

    channel: ReminderChannel = Field(default=ReminderChannel.EMAIL)
    hours_before: int = Field(default=24, ge=1, le=168)


class ReminderCreate(ReminderBase):
    """Schema for creating appointment reminders."""

    appointment_id: int = Field(..., gt=0)


class ReminderBulkCreate(BaseModel):
    """Schema for creating multiple reminders."""

    appointment_id: int = Field(..., gt=0)
    channels: list[ReminderChannel] = Field(
        default=[ReminderChannel.EMAIL, ReminderChannel.SMS]
    )
    hours_before: list[int] = Field(default=[24, 2])


class ReminderResponse(ReminderBase):
    """Schema for reminder responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    appointment_id: int
    scheduled_time: datetime
    status: ReminderStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime


class ReminderStats(BaseModel):
    """Statistics about reminder processing."""

    total: int = Field(default=0)
    sent: int = Field(default=0)
    failed: int = Field(default=0)
    pending: int = Field(default=0)
    cancelled: int = Field(default=0)
