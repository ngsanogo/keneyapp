"""
Appointment reminder model for automated notification scheduling.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ReminderStatus(str, enum.Enum):
    """Status of appointment reminders."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReminderChannel(str, enum.Enum):
    """Delivery channel for reminders."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    ALL = "all"


class AppointmentReminder(Base):
    """Automated appointment reminder tracking."""

    __tablename__ = "appointment_reminders"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    appointment_id = Column(
        Integer, ForeignKey("appointments.id"), nullable=False, index=True
    )
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    channel = Column(
        Enum(
            ReminderChannel,
            name="reminderchannel",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ReminderChannel.EMAIL,
    )
    status = Column(
        Enum(
            ReminderStatus,
            name="reminderstatus",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ReminderStatus.PENDING,
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    hours_before = Column(Integer, nullable=False, default=24)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    appointment = relationship("Appointment", back_populates="reminders")

    def __repr__(self):
        return f"<AppointmentReminder(id={self.id}, appointment_id={self.appointment_id}, status={self.status})>"

    @property
    def can_retry(self) -> bool:
        """Check if reminder can be retried."""
        return self.retry_count < self.max_retries

    @property
    def is_due(self) -> bool:
        """Check if reminder is due to be sent."""
        if self.status != ReminderStatus.PENDING:
            return False
        return datetime.now(self.scheduled_time.tzinfo) >= self.scheduled_time
