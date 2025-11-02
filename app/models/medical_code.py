"""
Medical coding and terminology models.

Supports international healthcare standards:
- ICD-11: International Classification of Diseases (WHO)
- SNOMED CT: Systematized Nomenclature of Medicine
- LOINC: Logical Observation Identifiers Names and Codes
- ATC: Anatomical Therapeutic Chemical Classification
- CPT: Current Procedural Terminology (US)
- CCAM: Classification Commune des Actes Médicaux (France)
"""

import enum

from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CodeSystem(str, enum.Enum):
    """Standard medical code systems."""

    ICD11 = "icd11"  # International Classification of Diseases 11th Revision
    SNOMED_CT = "snomed_ct"  # SNOMED Clinical Terms
    LOINC = "loinc"  # Logical Observation Identifiers Names and Codes
    ATC = "atc"  # Anatomical Therapeutic Chemical Classification
    CPT = "cpt"  # Current Procedural Terminology (US)
    CCAM = "ccam"  # Classification Commune des Actes Médicaux (France)
    DICOM = "dicom"  # Digital Imaging and Communications in Medicine


class MedicalCode(Base):
    """
    Reference table for medical codes and terminologies.

    Stores standardized medical codes for diagnoses, procedures,
    medications, and observations according to international standards.
    """

    __tablename__ = "medical_codes"

    id = Column(Integer, primary_key=True, index=True)
    code_system = Column(
        Enum(CodeSystem, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True
    )
    code = Column(String(50), nullable=False, index=True)
    display = Column(String(500), nullable=False)
    definition = Column(Text)

    # Additional metadata
    parent_code = Column(String(50))  # For hierarchical code systems
    is_active = Column(Integer, default=1)  # Active status

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<MedicalCode {self.code_system.value}:{self.code}>"


class Condition(Base):
    """
    Patient conditions/diagnoses with ICD-11 and SNOMED CT coding.

    Represents a clinical condition, problem, diagnosis, or other event
    that requires tracking for the patient.
    """

    __tablename__ = "conditions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Clinical description
    clinical_status = Column(String(20), default="active")  # active, resolved, etc.
    verification_status = Column(String(20), default="confirmed")
    severity = Column(String(20))  # mild, moderate, severe

    # Coded diagnosis (ICD-11)
    icd11_code = Column(String(50), index=True)
    icd11_display = Column(String(500))

    # Additional SNOMED CT coding
    snomed_code = Column(String(50), index=True)
    snomed_display = Column(String(500))

    # Clinical information
    notes = Column(Text)
    onset_date = Column(DateTime)
    abatement_date = Column(DateTime)

    recorded_by_id = Column(Integer, ForeignKey("users.id"))
    recorded_date = Column(DateTime(timezone=True), server_default=func.now())

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
    patient = relationship("Patient", backref="conditions")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id])
    tenant = relationship("Tenant", backref="conditions")


class Observation(Base):
    """
    Clinical observations and laboratory results with LOINC coding.

    Represents measurements and simple assertions made about a patient,
    such as vital signs, laboratory test results, etc.
    """

    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Observation status
    status = Column(
        String(20), default="final"
    )  # registered, preliminary, final, amended

    # LOINC coding for observation type
    loinc_code = Column(String(50), nullable=False, index=True)
    loinc_display = Column(String(500), nullable=False)

    # Observation value
    value_quantity = Column(String(50))  # Numeric value
    value_unit = Column(String(50))  # Unit of measure
    value_string = Column(Text)  # Text value for non-numeric observations

    # Reference ranges
    reference_range_low = Column(String(50))
    reference_range_high = Column(String(50))
    interpretation = Column(String(50))  # normal, high, low, critical

    # Observation context
    effective_datetime = Column(DateTime, nullable=False)
    issued_datetime = Column(DateTime(timezone=True), server_default=func.now())

    performer_id = Column(Integer, ForeignKey("users.id"))
    notes = Column(Text)

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
    patient = relationship("Patient", backref="observations")
    performer = relationship("User", foreign_keys=[performer_id])
    tenant = relationship("Tenant", backref="observations")


class Procedure(Base):
    """
    Medical procedures with CPT/CCAM coding.

    Represents an activity performed on a patient for diagnostic or
    therapeutic purposes (surgeries, therapies, counseling, etc.).
    """

    __tablename__ = "procedures"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Procedure status
    status = Column(
        String(20), default="completed"
    )  # preparation, in-progress, completed

    # CPT coding (US)
    cpt_code = Column(String(50), index=True)
    cpt_display = Column(String(500))

    # CCAM coding (France)
    ccam_code = Column(String(50), index=True)
    ccam_display = Column(String(500))

    # SNOMED CT coding (optional additional coding)
    snomed_code = Column(String(50), index=True)
    snomed_display = Column(String(500))

    # Procedure details
    category = Column(String(100))  # surgical, diagnostic, therapeutic, etc.
    notes = Column(Text)
    outcome = Column(String(500))

    # Timing
    performed_datetime = Column(DateTime, nullable=False)
    performed_by_id = Column(Integer, ForeignKey("users.id"))

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
    patient = relationship("Patient", backref="procedures")
    performed_by = relationship("User", foreign_keys=[performed_by_id])
    tenant = relationship("Tenant", backref="procedures")
