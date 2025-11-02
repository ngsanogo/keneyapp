"""
Medical record sharing model for controlled access.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
import secrets

from app.core.database import Base


class ShareScope(str, enum.Enum):
    """Scope of medical record sharing."""
    FULL_RECORD = "full_record"  # Complete medical history
    APPOINTMENTS_ONLY = "appointments_only"
    PRESCRIPTIONS_ONLY = "prescriptions_only"
    DOCUMENTS_ONLY = "documents_only"
    CUSTOM = "custom"  # Custom selection


class ShareStatus(str, enum.Enum):
    """Status of sharing link."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    USED = "used"


class MedicalRecordShare(Base):
    """
    Secure temporary sharing of medical records.
    Allows patients to share their records with external healthcare providers.
    """
    __tablename__ = "medical_record_shares"

    id = Column(Integer, primary_key=True, index=True)
    
    # Patient who is sharing
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Shared by user (could be patient or authorized representative)
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Sharing details
    share_token = Column(String(255), unique=True, nullable=False, index=True)
    scope = Column(SQLEnum(ShareScope), nullable=False)
    custom_resources = Column(Text, nullable=True)  # JSON for custom scope
    
    # Access control
    recipient_email = Column(String(255), nullable=True)  # Optional: restrict to email
    recipient_name = Column(String(255), nullable=True)
    access_pin = Column(String(10), nullable=True)  # Optional PIN for extra security
    
    # Status and validity
    status = Column(SQLEnum(ShareStatus), default=ShareStatus.ACTIVE, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Usage tracking
    access_count = Column(Integer, default=0, nullable=False)
    max_access_count = Column(Integer, nullable=True)  # Limit number of accesses
    last_accessed_at = Column(DateTime, nullable=True)
    last_accessed_ip = Column(String(50), nullable=True)
    
    # Purpose and notes
    purpose = Column(Text, nullable=True)  # Reason for sharing
    notes = Column(Text, nullable=True)  # Additional notes
    
    # Patient consent
    consent_given = Column(Boolean, default=True, nullable=False)
    consent_date = Column(DateTime, nullable=False)
    
    # Multi-tenancy
    tenant_id = Column(String(255), nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id])
    shared_by = relationship("User", foreign_keys=[shared_by_user_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_user_id])

    @staticmethod
    def generate_token() -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_pin() -> str:
        """Generate random 6-digit PIN."""
        return str(secrets.randbelow(1000000)).zfill(6)
    
    def is_valid(self) -> bool:
        """Check if share is still valid."""
        if self.status != ShareStatus.ACTIVE:
            return False
        
        if self.expires_at < datetime.now(timezone.utc):
            return False
        
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        
        return True
    
    def __repr__(self):
        return f"<MedicalRecordShare {self.id} for Patient {self.patient_id}>"
