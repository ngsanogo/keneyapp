"""
Notification models for storing notification history and user preferences.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationType(str, Enum):
    """Notification type enumeration."""

    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    LAB_RESULTS_READY = "lab_results_ready"
    PRESCRIPTION_RENEWAL = "prescription_renewal"
    MESSAGE_RECEIVED = "message_received"
    DOCUMENT_SHARED = "document_shared"
    DOCUMENT_UPLOADED = "document_uploaded"
    SYSTEM_ALERT = "system_alert"
    SECURITY_ALERT = "security_alert"


class NotificationChannel(str, Enum):
    """Notification delivery channel."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBSOCKET = "websocket"


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class Notification(Base):
    """
    Notification history table for tracking all sent notifications.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Notification details
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(
        SQLEnum(NotificationStatus),
        nullable=False,
        default=NotificationStatus.PENDING,
        index=True,
    )

    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)  # Optional action link

    # Metadata
    recipient_email = Column(String(255), nullable=True)
    recipient_phone = Column(String(50), nullable=True)

    # Related resource
    resource_type = Column(
        String(50), nullable=True
    )  # e.g., "appointment", "lab_result"
    resource_id = Column(Integer, nullable=True)

    # Delivery tracking
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    failed_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="notifications")
    tenant = relationship("Tenant", back_populates="notifications")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_notification_user_status", "user_id", "status"),
        Index("idx_notification_user_created", "user_id", "created_at"),
        Index("idx_notification_tenant_created", "tenant_id", "created_at"),
        Index("idx_notification_type_status", "type", "status"),
    )


class NotificationPreference(Base):
    """
    User preferences for notification channels and types.
    """

    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Email preferences
    email_enabled = Column(Boolean, default=True, nullable=False)
    email_appointment_reminders = Column(Boolean, default=True, nullable=False)
    email_lab_results = Column(Boolean, default=True, nullable=False)
    email_prescription_renewals = Column(Boolean, default=True, nullable=False)
    email_messages = Column(Boolean, default=True, nullable=False)
    email_documents = Column(Boolean, default=True, nullable=False)
    email_system_alerts = Column(Boolean, default=True, nullable=False)

    # SMS preferences
    sms_enabled = Column(Boolean, default=False, nullable=False)
    sms_appointment_reminders = Column(Boolean, default=True, nullable=False)
    sms_lab_results = Column(Boolean, default=False, nullable=False)
    sms_prescription_renewals = Column(Boolean, default=True, nullable=False)
    sms_messages = Column(Boolean, default=False, nullable=False)

    # Push notification preferences
    push_enabled = Column(Boolean, default=True, nullable=False)
    push_appointment_reminders = Column(Boolean, default=True, nullable=False)
    push_lab_results = Column(Boolean, default=True, nullable=False)
    push_prescription_renewals = Column(Boolean, default=True, nullable=False)
    push_messages = Column(Boolean, default=True, nullable=False)
    push_documents = Column(Boolean, default=True, nullable=False)

    # WebSocket real-time preferences
    websocket_enabled = Column(Boolean, default=True, nullable=False)

    # Quiet hours (24-hour format, e.g., "22:00-08:00")
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(5), default="22:00", nullable=False)
    quiet_hours_end = Column(String(5), default="08:00", nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="notification_preference")
    tenant = relationship("Tenant")
