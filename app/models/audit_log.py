"""
Audit log model for GDPR/HIPAA compliance.
Tracks all critical actions in the system.
"""

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking all critical system actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    user_id = Column(Integer, nullable=True)  # Nullable for anonymous actions
    username = Column(String, nullable=True)
    action = Column(String, nullable=False, index=True)  # CREATE, READ, UPDATE, DELETE
    resource_type = Column(
        String, nullable=False, index=True
    )  # patient, appointment, prescription, etc.
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Additional context
    status = Column(String, nullable=False)  # success, failure
