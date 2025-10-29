"""
Dashboard router for real-time health metrics and statistics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get real-time dashboard statistics.

    Args:
        db: Database session

    Returns:
        Dictionary containing various health metrics and statistics
    """
    # Total counts
    total_patients = db.query(func.count(Patient.id)).scalar()
    total_appointments = db.query(func.count(Appointment.id)).scalar()
    total_prescriptions = db.query(func.count(Prescription.id)).scalar()

    # Today's appointments
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(
        today, datetime.min.time(), tzinfo=timezone.utc
    )
    today_end = datetime.combine(
        today, datetime.max.time(), tzinfo=timezone.utc
    )

    today_appointments = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.appointment_date >= today_start,
            Appointment.appointment_date <= today_end,
        )
        .scalar()
    )

    # Appointments by status
    scheduled_appointments = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.status == AppointmentStatus.SCHEDULED)
        .scalar()
    )

    completed_appointments = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.status == AppointmentStatus.COMPLETED)
        .scalar()
    )

    cancelled_appointments = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.status == AppointmentStatus.CANCELLED)
        .scalar()
    )

    # Recent activity (last 7 days)
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Assuming we'd have a created_at field
    recent_patients = db.query(func.count(Patient.id)).scalar()

    recent_appointments = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.appointment_date >= week_ago)
        .scalar()
    )

    recent_prescriptions = (
        db.query(func.count(Prescription.id))
        .filter(Prescription.prescribed_date >= week_ago)
        .scalar()
    )

    return {
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
