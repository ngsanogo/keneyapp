"""
Schemas for notification management and preferences.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.notification import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


# ===== Notification Schemas =====


class NotificationBase(BaseModel):
    """Base schema for notification."""

    type: NotificationType
    channel: NotificationChannel
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    action_url: Optional[str] = Field(None, max_length=500)


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""

    user_id: int
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None


class NotificationUpdate(BaseModel):
    """Schema for updating notification status."""

    status: NotificationStatus
    failed_reason: Optional[str] = None


class NotificationResponse(NotificationBase):
    """Schema for notification response."""

    id: int
    user_id: int
    status: NotificationStatus
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationMarkRead(BaseModel):
    """Schema for marking notifications as read."""

    notification_ids: List[int] = Field(..., min_length=1, max_length=100)


class NotificationStats(BaseModel):
    """Statistics for user notifications."""

    total: int
    unread: int
    by_type: dict[str, int]
    by_status: dict[str, int]


# ===== Notification Preference Schemas =====


class NotificationPreferenceBase(BaseModel):
    """Base schema for notification preferences."""

    # Email preferences
    email_enabled: bool = True
    email_appointment_reminders: bool = True
    email_lab_results: bool = True
    email_prescription_renewals: bool = True
    email_messages: bool = True
    email_documents: bool = True
    email_system_alerts: bool = True

    # SMS preferences
    sms_enabled: bool = False
    sms_appointment_reminders: bool = True
    sms_lab_results: bool = False
    sms_prescription_renewals: bool = True
    sms_messages: bool = False

    # Push preferences
    push_enabled: bool = True
    push_appointment_reminders: bool = True
    push_lab_results: bool = True
    push_prescription_renewals: bool = True
    push_messages: bool = True
    push_documents: bool = True

    # WebSocket preferences
    websocket_enabled: bool = True

    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = Field("22:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_hours_end: str = Field("08:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating notification preferences."""

    pass


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    """Schema for updating notification preferences."""

    pass


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema for notification preference response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ===== Notification Send Request =====


class NotificationSendRequest(BaseModel):
    """Request schema for sending notifications."""

    user_ids: List[int] = Field(..., min_length=1, max_length=1000)
    type: NotificationType
    channels: List[NotificationChannel] = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    action_url: Optional[str] = Field(None, max_length=500)
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    respect_preferences: bool = True


class NotificationSendResponse(BaseModel):
    """Response schema for sending notifications."""

    success: bool
    total_requested: int
    notifications_created: int
    notifications_sent: int
    failures: int
    errors: List[dict] = []
