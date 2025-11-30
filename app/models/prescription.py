"""
Prescription model for managing patient prescriptions and medications.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.tenant import Tenant


class Prescription(Base):
    """Prescription model for digital prescription management."""

    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medication_name = Column(String, nullable=False)

    # ATC (Anatomical Therapeutic Chemical) classification code
    atc_code = Column(String(50), index=True)
    atc_display = Column(String(500))

    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    instructions = Column(Text)
    prescribed_date = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    refills = Column(Integer, default=0)
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
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("User", back_populates="prescriptions")
    tenant = relationship(Tenant, back_populates="prescriptions")
    # refill_requests relationship removed in minimal backend scope

    @property
    def is_active(self) -> bool:
        """Check if prescription is still active based on prescribed date and duration."""
        if not self.prescribed_date or not self.duration:
            return True
        try:
            duration_days = int("".join(filter(str.isdigit, self.duration)))
            expiry_date = self.prescribed_date + timedelta(days=duration_days)
            return datetime.now(timezone.utc) < expiry_date
        except (ValueError, AttributeError):
            return True
