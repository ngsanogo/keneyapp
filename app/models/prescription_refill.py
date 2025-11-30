"""
Prescription refill request model for patient self-service.
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


class RefillRequestStatus(str, enum.Enum):
    """Status of prescription refill requests."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class PrescriptionRefillRequest(Base):
    """Prescription refill request model."""

    __tablename__ = "prescription_refill_requests"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    prescription_id = Column(
        Integer, ForeignKey("prescriptions.id"), nullable=False, index=True
    )
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(
        Enum(
            RefillRequestStatus,
            name="refillrequeststatus",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=RefillRequestStatus.PENDING,
        index=True,
    )

    reason = Column(Text, nullable=True)
    patient_notes = Column(Text, nullable=True)
    pharmacy_name = Column(String(200), nullable=True)
    pharmacy_phone = Column(String(20), nullable=True)

    # Response fields
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    denial_reason = Column(Text, nullable=True)

    # New prescription ID if dosage/medication changed
    new_prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)

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
    prescription = relationship(
        "Prescription",
        foreign_keys=[prescription_id],
        back_populates="refill_requests",
    )
    new_prescription = relationship(
        "Prescription",
        foreign_keys=[new_prescription_id],
    )
    patient = relationship("Patient", back_populates="refill_requests")
    doctor = relationship("User", foreign_keys=[doctor_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<PrescriptionRefillRequest(id={self.id}, status={self.status})>"

    @property
    def can_be_cancelled(self) -> bool:
        """Check if request can be cancelled."""
        return self.status in [
            RefillRequestStatus.PENDING,
            RefillRequestStatus.APPROVED,
        ]

    @property
    def can_be_reviewed(self) -> bool:
        """Check if request can be reviewed."""
        return self.status == RefillRequestStatus.PENDING

    @property
    def days_since_request(self) -> int:
        """Calculate days since request was created."""
        delta = datetime.now(self.created_at.tzinfo) - self.created_at
        return delta.days
