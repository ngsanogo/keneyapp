"""
Dashboard router for real-time health metrics and statistics.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.cache import cache_get, cache_set
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.user import User, UserRole

DASHBOARD_STATS_CACHE_KEY = "dashboard:stats"
DASHBOARD_STATS_TTL_SECONDS = 120

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
@limiter.limit("30/minute")
def get_dashboard_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
):
    """
    Get real-time dashboard statistics.

    Args:
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user requesting dashboard data

    Returns:
        Dictionary containing various health metrics and statistics
    """
    cache_key = f"{DASHBOARD_STATS_CACHE_KEY}:{current_user.tenant_id}"
    cached_stats = cache_get(cache_key)
    if cached_stats is not None:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="dashboard",
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={"operation": "stats", "cached": True},
            request=request,
        )
        return cached_stats
    # Total counts
    total_patients = (
        db.query(func.count(Patient.id))
        .filter(Patient.tenant_id == current_user.tenant_id)
        .scalar()
    )
    total_appointments = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.tenant_id == current_user.tenant_id)
        .scalar()
    )
    total_prescriptions = (
        db.query(func.count(Prescription.id))
        .filter(Prescription.tenant_id == current_user.tenant_id)
        .scalar()
    )

    # Today's appointments
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time(), tzinfo=timezone.utc)

    today_appointments = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.tenant_id == current_user.tenant_id,
            Appointment.appointment_date >= today_start,
            Appointment.appointment_date <= today_end,
        )
        .scalar()
    )

    # Appointments by status
    scheduled_appointments = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.tenant_id == current_user.tenant_id,
            Appointment.status == AppointmentStatus.SCHEDULED,
        )
        .scalar()
    )

    completed_appointments = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.tenant_id == current_user.tenant_id,
            Appointment.status == AppointmentStatus.COMPLETED,
        )
        .scalar()
    )

    cancelled_appointments = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.tenant_id == current_user.tenant_id,
            Appointment.status == AppointmentStatus.CANCELLED,
        )
        .scalar()
    )

    # Recent activity (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Assuming we'd have a created_at field
    recent_patients = (
        db.query(func.count(Patient.id))
        .filter(
            Patient.tenant_id == current_user.tenant_id,
            Patient.created_at >= week_ago,
        )
        .scalar()
    )

    recent_appointments = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.tenant_id == current_user.tenant_id,
            Appointment.created_at >= week_ago,
        )
        .scalar()
    )

    recent_prescriptions = (
        db.query(func.count(Prescription.id))
        .filter(
            Prescription.tenant_id == current_user.tenant_id,
            Prescription.created_at >= week_ago,
        )
        .scalar()
    )

    stats = {
        "total_patients": total_patients,
        "total_appointments": total_appointments,
        "total_prescriptions": total_prescriptions,
        "today_appointments": today_appointments,
        "appointments_by_status": {
            "scheduled": scheduled_appointments,
            "completed": completed_appointments,
            "cancelled": cancelled_appointments,
        },
        "recent_activity": {
            "patients": recent_patients,
            "appointments": recent_appointments,
            "prescriptions": recent_prescriptions,
        },
    }

    cache_set(cache_key, stats, expire=DASHBOARD_STATS_TTL_SECONDS)

    log_audit_event(
        db=db,
        action="READ",
        resource_type="dashboard",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"operation": "stats", "cached": False},
        request=request,
    )

    return stats
