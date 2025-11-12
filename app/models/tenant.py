"""
Tenant and module management models for multi-tenant support.
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Tenant(Base):
    """Tenant model representing an organization using the platform."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    contact_email = Column(String, nullable=True)
    region = Column(String, nullable=True)
    default_timezone = Column(String, nullable=True, default="UTC")
    is_active = Column(Boolean, nullable=False, default=True)
    configuration = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    patients = relationship("Patient", back_populates="tenant", cascade="all, delete-orphan")
    appointments = relationship(
        "Appointment", back_populates="tenant", cascade="all, delete-orphan"
    )
    prescriptions = relationship(
        "Prescription", back_populates="tenant", cascade="all, delete-orphan"
    )
    modules = relationship("TenantModule", back_populates="tenant", cascade="all, delete-orphan")


class TenantModule(Base):
    """Tenant-specific module activation and configuration."""

    __tablename__ = "tenant_modules"
    __table_args__ = (UniqueConstraint("tenant_id", "module_key", name="uq_tenant_module"),)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    module_key = Column(String, nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)
    configuration = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    tenant = relationship("Tenant", back_populates="modules")
