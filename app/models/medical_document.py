"""
Medical document model for storing patient files, images, and reports.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentType(str, enum.Enum):
    """Medical document types."""

    LAB_RESULT = "lab_result"
    IMAGING = "imaging"  # X-ray, CT, MRI, etc.
    PRESCRIPTION = "prescription"
    CONSULTATION_NOTE = "consultation_note"
    VACCINATION_RECORD = "vaccination_record"
    INSURANCE = "insurance"
    ID_DOCUMENT = "id_document"
    OTHER = "other"


class DocumentFormat(str, enum.Enum):
    """Supported document formats."""

    PDF = "pdf"
    JPEG = "jpeg"
    PNG = "png"
    DICOM = "dicom"  # Medical imaging standard
    DOCX = "docx"
    TXT = "txt"


class DocumentStatus(str, enum.Enum):
    """Document processing status."""

    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class MedicalDocument(Base):
    """
    Medical documents storage with support for various file types.
    Supports local filesystem or cloud storage (S3, Azure Blob).
    """

    __tablename__ = "medical_documents"

    id = Column(Integer, primary_key=True, index=True)

    # Document metadata
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    document_format = Column(SQLEnum(DocumentFormat), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Size in bytes

    # Storage location
    storage_path = Column(String(1000), nullable=False)  # Local path or S3 key
    storage_type = Column(String(50), default="local")  # 'local', 's3', 'azure'
    checksum = Column(String(64), nullable=False)  # SHA-256 hash for integrity

    # Processing status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADING, nullable=False)
    processing_error = Column(Text, nullable=True)

    # OCR and metadata extraction
    ocr_text = Column(Text, nullable=True)  # Extracted text from OCR
    extracted_metadata = Column(Text, nullable=True)  # JSON metadata

    # Associations
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Optional associations
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)

    # Document description and tags
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array of tags

    # Security and privacy
    is_sensitive = Column(Boolean, default=True)  # PHI by default
    encryption_key_id = Column(String(255), nullable=True)  # Reference to encryption key

    # Multi-tenancy
    tenant_id = Column(String(255), nullable=False, index=True)

    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    patient = relationship("Patient", back_populates="documents")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    appointment = relationship("Appointment", foreign_keys=[appointment_id])
    prescription = relationship("Prescription", foreign_keys=[prescription_id])

    def __repr__(self):
        return f"<MedicalDocument {self.id}: {self.original_filename}>"
