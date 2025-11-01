"""
Patient model for healthcare record management.
"""

import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Text,
    Enum,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.tenant import Tenant


class Gender(str, enum.Enum):
    """Gender options for patient records."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Patient(Base):
    """Patient model for storing patient information and medical history."""

    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_patients_tenant_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender: Gender = Column(Enum(Gender), nullable=False)  # type: ignore[assignment]
    email = Column(String, index=True)
    phone = Column(String, nullable=False)
    address = Column(Text)
    medical_history = Column(Text)
    allergies = Column(Text)
    blood_type = Column(String(5))
    emergency_contact = Column(String)
    emergency_phone = Column(String)
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
    appointments = relationship("Appointment", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    tenant = relationship(Tenant, back_populates="patients")
