"""
Prescription model for managing patient prescriptions and medications.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Prescription(Base):
    """Prescription model for digital prescription management."""
    
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    instructions = Column(Text)
    prescribed_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    refills = Column(Integer, default=0)
    
    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("User", back_populates="prescriptions")
