"""
Audit logging utilities for GDPR/HIPAA compliance.
"""

from typing import Optional, Dict, Any, List
from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_audit_event(
    db: Session,
    action: str,
    resource_type: str,
    status: str = "success",
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    request: Optional[Request] = None,
) -> None:
    """
    Log an audit event to the database.

    Args:
        db: Database session
        action: Action performed (CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, etc.)
        resource_type: Type of resource affected
        status: Status of the action (success, failure)
        user_id: ID of the user performing the action
        username: Username of the user
        resource_id: ID of the affected resource
        details: Additional contextual information
        request: FastAPI request object for IP and user agent
    """
    ip_address = None
    user_agent = None

    if request:
        # Extract client IP address
        ip_address = request.client.host if request.client else None
        # Extract user agent
        user_agent = request.headers.get("user-agent")

    audit_log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        status=status,
    )

    db.add(audit_log)
    db.commit()


def get_audit_logs(
    db: Session,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
) -> List[AuditLog]:
    """
    Retrieve audit logs with optional filtering.

    Args:
        db: Database session
        user_id: Filter by user ID
        resource_type: Filter by resource type
        action: Filter by action
        limit: Maximum number of records to return

    Returns:
        List of audit log entries
    """
    query = db.query(AuditLog)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if action:
        query = query.filter(AuditLog.action == action)

    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
