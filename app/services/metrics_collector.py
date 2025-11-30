"""
Business metrics collection service.

This module provides functions to collect and update business KPIs for monitoring.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.metrics import (
    appointment_completion_rate,
    appointment_no_show_rate,
    appointments_by_status,
    daily_active_patients,
    patients_by_risk_level,
    prescription_fulfillment_rate,
    prescriptions_by_status,
)
from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.models.prescription import Prescription


def collect_daily_active_patients(db: Session) -> int:
    """
    Count unique patients with activity today.

    Args:
        db: Database session

    Returns:
        Number of active patients today
    """
    today = datetime.now(timezone.utc).date()

    # Count patients with appointments or prescriptions today
    active_count = (
        db.query(func.count(func.distinct(AuditLog.user_id)))
        .filter(and_(AuditLog.timestamp >= today, AuditLog.resource_type == "patient"))
        .scalar()
        or 0
    )

    daily_active_patients.set(active_count)
    return active_count


def collect_appointment_metrics(db: Session) -> Dict[str, Any]:
    """
    Collect appointment-related metrics.

    Args:
        db: Database session

    Returns:
        Dictionary with appointment metrics
    """
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Appointments by status
    status_counts = (
        db.query(Appointment.status, func.count(Appointment.id))
        .group_by(Appointment.status)
        .all()
    )

    for status, count in status_counts:
        appointments_by_status.labels(status=status).set(count)

    # Completion rate - daily
    daily_scheduled = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.appointment_date >= today)
        .scalar()
        or 0
    )

    daily_completed = (
        db.query(func.count(Appointment.id))
        .filter(
            and_(
                Appointment.appointment_date >= today,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
        )
        .scalar()
        or 0
    )

    daily_rate = (daily_completed / daily_scheduled * 100) if daily_scheduled > 0 else 0
    appointment_completion_rate.labels(time_period="day").set(daily_rate)

    # Completion rate - weekly
    weekly_scheduled = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.appointment_date >= week_ago)
        .scalar()
        or 0
    )

    weekly_completed = (
        db.query(func.count(Appointment.id))
        .filter(
            and_(
                Appointment.appointment_date >= week_ago,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
        )
        .scalar()
        or 0
    )

    weekly_rate = (
        (weekly_completed / weekly_scheduled * 100) if weekly_scheduled > 0 else 0
    )
    appointment_completion_rate.labels(time_period="week").set(weekly_rate)

    # Completion rate - monthly
    monthly_scheduled = (
        db.query(func.count(Appointment.id))
        .filter(Appointment.appointment_date >= month_ago)
        .scalar()
        or 0
    )

    monthly_completed = (
        db.query(func.count(Appointment.id))
        .filter(
            and_(
                Appointment.appointment_date >= month_ago,
                Appointment.status == AppointmentStatus.COMPLETED,
            )
        )
        .scalar()
        or 0
    )

    monthly_rate = (
        (monthly_completed / monthly_scheduled * 100) if monthly_scheduled > 0 else 0
    )
    appointment_completion_rate.labels(time_period="month").set(monthly_rate)

    # No-show rate
    daily_no_show = (
        db.query(func.count(Appointment.id))
        .filter(
            and_(
                Appointment.appointment_date >= today,
                Appointment.status == AppointmentStatus.NO_SHOW,
            )
        )
        .scalar()
        or 0
    )

    daily_no_show_rate = (
        (daily_no_show / daily_scheduled * 100) if daily_scheduled > 0 else 0
    )
    appointment_no_show_rate.labels(time_period="day").set(daily_no_show_rate)

    return {
        "daily_completion_rate": daily_rate,
        "weekly_completion_rate": weekly_rate,
        "monthly_completion_rate": monthly_rate,
        "daily_no_show_rate": daily_no_show_rate,
    }


def collect_prescription_metrics(db: Session) -> Dict[str, Any]:
    """
    Collect prescription-related metrics.

    Args:
        db: Database session

    Returns:
        Dictionary with prescription metrics
    """
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)

    # Total prescriptions created daily
    daily_total = (
        db.query(func.count(Prescription.id))
        .filter(Prescription.created_at >= datetime.combine(today, datetime.min.time()))
        .scalar()
        or 0
    )

    # Total prescriptions created weekly
    weekly_total = (
        db.query(func.count(Prescription.id))
        .filter(
            Prescription.created_at >= datetime.combine(week_ago, datetime.min.time())
        )
        .scalar()
        or 0
    )

    # Count prescriptions by refill status (has refills = active, no refills = completed)
    active_prescriptions = (
        db.query(func.count(Prescription.id)).filter(Prescription.refills > 0).scalar()
        or 0
    )

    completed_prescriptions = (
        db.query(func.count(Prescription.id)).filter(Prescription.refills == 0).scalar()
        or 0
    )

    # Update Prometheus metrics
    prescriptions_by_status.labels(status="active").set(active_prescriptions)
    prescriptions_by_status.labels(status="completed").set(completed_prescriptions)

    # Calculate active prescription rate (prescriptions with remaining refills)
    # Note: This is a simplified metric. True fulfillment tracking would require
    # additional status fields in the Prescription model.
    total_prescriptions = active_prescriptions + completed_prescriptions
    active_rate = (
        (active_prescriptions / total_prescriptions * 100)
        if total_prescriptions > 0
        else 0
    )

    # Update metrics with active rate (renamed from fulfillment rate for clarity)
    prescription_fulfillment_rate.labels(time_period="day").set(active_rate)
    prescription_fulfillment_rate.labels(time_period="week").set(active_rate)

    return {
        "daily_fulfillment_rate": active_rate,
        "weekly_fulfillment_rate": active_rate,
        "daily_total": daily_total,
        "weekly_total": weekly_total,
        "active_prescriptions": active_prescriptions,
        "completed_prescriptions": completed_prescriptions,
    }


def collect_patient_risk_metrics(db: Session) -> Dict[str, int]:
    """
    Collect patient risk level distribution.

    Note: This is a placeholder. In a real implementation, you would have
    a risk assessment algorithm based on patient data.

    Args:
        db: Database session

    Returns:
        Dictionary with risk level counts
    """
    # Placeholder implementation
    # In production, this would analyze patient data to determine risk levels
    total_patients = db.query(func.count(Patient.id)).scalar() or 0

    # Example distribution (replace with actual risk assessment)
    low_risk = int(total_patients * 0.7)
    medium_risk = int(total_patients * 0.25)
    high_risk = total_patients - low_risk - medium_risk

    patients_by_risk_level.labels(risk_level="low").set(low_risk)
    patients_by_risk_level.labels(risk_level="medium").set(medium_risk)
    patients_by_risk_level.labels(risk_level="high").set(high_risk)

    return {
        "low": low_risk,
        "medium": medium_risk,
        "high": high_risk,
    }


def collect_all_business_metrics(db: Session) -> Dict[str, Any]:
    """
    Collect all business metrics.

    This function should be called periodically (e.g., via Celery beat task)
    to update all business KPI metrics.

    Args:
        db: Database session

    Returns:
        Dictionary with all collected metrics
    """
    metrics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "daily_active_patients": collect_daily_active_patients(db),
        "appointment_metrics": collect_appointment_metrics(db),
        "prescription_metrics": collect_prescription_metrics(db),
        "patient_risk_metrics": collect_patient_risk_metrics(db),
    }

    return metrics
