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
DASHBOARD_STATS_TTL_SECONDS = 300

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
    tenant_id = current_user.tenant_id
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Time windows
    today_start = datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc)
    today_end = datetime.combine(now.date(), datetime.max.time(), tzinfo=timezone.utc)

    # Aggregate patient counts in one round-trip
    patient_counts = (
        db.query(
            func.count().filter(Patient.tenant_id == tenant_id).label("total"),
            func.count()
            .filter(Patient.tenant_id == tenant_id, Patient.created_at >= week_ago)
            .label("recent"),
        )
        .select_from(Patient)
        .one()
    )

    # Aggregate appointment stats in one round-trip
    appointment_counts = (
        db.query(
            func.count().filter(Appointment.tenant_id == tenant_id).label("total"),
            func.count()
            .filter(
                Appointment.tenant_id == tenant_id,
                Appointment.appointment_date >= today_start,
                Appointment.appointment_date <= today_end,
            )
            .label("today"),
            func.count()
            .filter(Appointment.tenant_id == tenant_id, Appointment.status == AppointmentStatus.SCHEDULED)
            .label("scheduled"),
            func.count()
            .filter(Appointment.tenant_id == tenant_id, Appointment.status == AppointmentStatus.COMPLETED)
            .label("completed"),
            func.count()
            .filter(Appointment.tenant_id == tenant_id, Appointment.status == AppointmentStatus.CANCELLED)
            .label("cancelled"),
            func.count()
            .filter(Appointment.tenant_id == tenant_id, Appointment.created_at >= week_ago)
            .label("recent"),
        )
        .select_from(Appointment)
        .one()
    )

    # Aggregate prescription stats in one round-trip
    prescription_counts = (
        db.query(
            func.count().filter(Prescription.tenant_id == tenant_id).label("total"),
            func.count()
            .filter(Prescription.tenant_id == tenant_id, Prescription.created_at >= week_ago)
            .label("recent"),
        )
        .select_from(Prescription)
        .one()
    )

    stats = {
        "total_patients": patient_counts.total,
        "total_appointments": appointment_counts.total,
        "total_prescriptions": prescription_counts.total,
        "today_appointments": appointment_counts.today,
        "appointments_by_status": {
            "scheduled": appointment_counts.scheduled,
            "completed": appointment_counts.completed,
            "cancelled": appointment_counts.cancelled,
        },
        "recent_activity": {
            "patients": patient_counts.recent,
            "appointments": appointment_counts.recent,
            "prescriptions": prescription_counts.recent,
        },
        "activity_window_days": 7,
        "generated_at": now.isoformat(),
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
