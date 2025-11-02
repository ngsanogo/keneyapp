"""
Laboratory test result model.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class LabResult(Base):
    """Lab test result scoped by tenant and patient."""

    __tablename__ = "lab_results"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    test_name = Column(String(255), nullable=False, index=True)
    result_value = Column(String(255), nullable=False)
    units = Column(String(50), nullable=True)
    reference_range = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="final")  # e.g., pending|final|corrected
    notes = Column(Text, nullable=True)

    collected_at = Column(DateTime(timezone=True), nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    patient = relationship("Patient", back_populates="lab_results")
