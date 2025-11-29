"""
French Healthcare Integration Models
Supports INS, CPS, DMP, and MSSanté compliance
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class INSStatus(str, Enum):
    """INS verification status"""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


class CPSType(str, Enum):
    """Type de Carte de Professionnel de Santé"""

    CPS = "cps"  # Physical card
    E_CPS = "e_cps"  # Electronic CPS
    CPF = "cpf"  # Carte de Professionnel en Formation


class PatientINS(Base):
    """
    INS (Identifiant National de Santé) for patients
    Follows ANS (Agence du Numérique en Santé) specifications
    """

    __tablename__ = "patient_ins"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Patient reference
    patient_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # INS Components (Format: 1 YY MM RR DDD KKK CC)
    # Example: 1 84 12 75 123 456 78
    ins_number = Column(
        String(15), nullable=False, unique=True, index=True
    )  # Full INS (13 digits)
    nir_key = Column(String(2), nullable=True)  # Clé de contrôle NIR
    oid = Column(String(50), nullable=True)  # OID de l'INS (1.2.250.1.213.1.4.8)

    # Verification details
    status = Column(SQLEnum(INSStatus), nullable=False, default=INSStatus.PENDING)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_method = Column(
        String(50), nullable=True
    )  # teleservice_ins, carte_vitale, etc.
    verification_operator_id = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Identity traits (from INS teleservice response)
    birth_name = Column(String(100), nullable=True)  # Nom de naissance
    first_names = Column(String(200), nullable=True)  # Prénoms (ordre état civil)
    birth_date = Column(DateTime(timezone=True), nullable=True)
    birth_location = Column(String(200), nullable=True)  # Lieu de naissance
    birth_location_code = Column(String(10), nullable=True)  # Code INSEE
    gender_code = Column(String(1), nullable=True)  # 1=M, 2=F

    # Expiration and renewal
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_check_at = Column(DateTime(timezone=True), nullable=True)

    # Audit
    tenant_id = Column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
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
    patient = relationship("Patient", back_populates="ins_record")
    verification_operator = relationship(
        "User", foreign_keys=[verification_operator_id]
    )
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<PatientINS(patient_id={self.patient_id}, ins={self.ins_number[:6]}***, status={self.status})>"

    @property
    def is_valid(self) -> bool:
        """Check if INS is currently valid"""
        if self.status != INSStatus.VERIFIED:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True


class HealthcareProfessionalCPS(Base):
    """
    CPS/e-CPS (Carte de Professionnel de Santé) credentials
    For Pro Santé Connect authentication
    """

    __tablename__ = "healthcare_professional_cps"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # User reference (healthcare professional)
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # CPS identification
    cps_type = Column(SQLEnum(CPSType), nullable=False, default=CPSType.E_CPS)
    cps_number = Column(
        String(20), nullable=False, unique=True, index=True
    )  # Numéro CPS (8 digits)
    rpps_number = Column(
        String(11), nullable=True, index=True
    )  # Répertoire Partagé des Professionnels de Santé
    adeli_number = Column(
        String(9), nullable=True, index=True
    )  # ADELI (old identification)

    # Professional details (from RPPS)
    profession_code = Column(
        String(10), nullable=True
    )  # Code profession (ex: 10 = Médecin)
    profession_category = Column(String(50), nullable=True)  # Catégorie professionnelle
    specialty_code = Column(String(10), nullable=True)  # Code spécialité
    specialty_label = Column(String(200), nullable=True)  # Libellé spécialité

    # Practice location
    practice_structure_id = Column(String(50), nullable=True)  # FINESS/SIRET
    practice_structure_name = Column(String(200), nullable=True)

    # Pro Santé Connect integration
    psc_sub = Column(
        String(100), nullable=True, unique=True
    )  # Subject identifier from Pro Santé Connect
    psc_token_endpoint = Column(String(500), nullable=True)
    psc_last_login = Column(DateTime(timezone=True), nullable=True)

    # Card validity
    issue_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Audit
    tenant_id = Column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
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
    user = relationship("User", back_populates="cps_credential")
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<HealthcareProfessionalCPS(user_id={self.user_id}, cps={self.cps_number}, rpps={self.rpps_number})>"

    @property
    def is_valid(self) -> bool:
        """Check if CPS is currently valid"""
        if not self.is_active:
            return False
        if self.expiry_date and self.expiry_date < datetime.utcnow():
            return False
        return True


class DMPIntegration(Base):
    """
    DMP (Dossier Médical Partagé) integration tracking
    Records DMP access and document exchanges
    """

    __tablename__ = "dmp_integration"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Patient reference
    patient_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # DMP details
    dmp_id = Column(
        String(50), nullable=True, unique=True, index=True
    )  # INS-based DMP identifier
    dmp_consent = Column(Boolean, nullable=False, default=False)
    dmp_consent_date = Column(DateTime(timezone=True), nullable=True)
    dmp_access_mode = Column(
        String(20), nullable=True
    )  # normal, urgence, bris_de_glace

    # Document exchange tracking
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    documents_sent_count = Column(Integer, nullable=False, default=0)
    documents_received_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)

    # Audit
    tenant_id = Column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
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
    patient = relationship("Patient", back_populates="dmp_record")
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<DMPIntegration(patient_id={self.patient_id}, dmp_id={self.dmp_id}, consent={self.dmp_consent})>"


class MSSanteMessage(Base):
    """
    MSSanté (Messagerie Sécurisée de Santé) message tracking
    Secure health messaging compliant with French regulations
    """

    __tablename__ = "mssante_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Message references
    internal_message_id = Column(
        PGUUID(as_uuid=True), ForeignKey("messages.id"), nullable=True, index=True
    )
    mssante_message_id = Column(String(100), nullable=True, unique=True, index=True)

    # Sender/Receiver (MSSanté addresses: prenom.nom@medecin.mssante.fr)
    sender_mssante_address = Column(String(200), nullable=False)
    receiver_mssante_address = Column(String(200), nullable=False)

    # Message details
    subject = Column(String(500), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, sent, delivered, read, failed
    error_message = Column(Text, nullable=True)

    # Attachments
    has_attachments = Column(Boolean, nullable=False, default=False)
    attachment_count = Column(Integer, nullable=False, default=0)

    # Audit
    tenant_id = Column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
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
    internal_message = relationship("Message", foreign_keys=[internal_message_id])
    tenant = relationship("Tenant")

    def __repr__(self):
        return f"<MSSanteMessage(id={self.id}, status={self.status}, from={self.sender_mssante_address})>"
