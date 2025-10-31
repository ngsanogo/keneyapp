"""
Business metrics collection service.

This module provides functions to collect and update business KPIs for monitoring.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.metrics import (
    daily_active_patients,
    appointment_completion_rate,
    prescription_fulfillment_rate,
    appointment_no_show_rate,
    appointments_by_status,
    prescriptions_by_status,
    patients_by_risk_level,
)
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.audit_log import AuditLog


def collect_daily_active_patients(db: Session) -> int:
    """
    Count unique patients with activity today.

    Args:
        db: Database session

    Returns:
        Number of active patients today
    """
    today = datetime.utcnow().date()

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
    today = datetime.utcnow().date()
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
                Appointment.appointment_date >= today, Appointment.status == "completed"
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
                Appointment.status == "completed",
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
                Appointment.status == "completed",
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
            and_(Appointment.appointment_date >= today, Appointment.status == "no_show")
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
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)

    # Prescriptions by status
    status_counts = (
        db.query(Prescription.status, func.count(Prescription.id))
        .group_by(Prescription.status)
        .all()
    )

    for status, count in status_counts:
        prescriptions_by_status.labels(status=status).set(count)

    # Fulfillment rate - daily
    daily_total = (
        db.query(func.count(Prescription.id))
        .filter(Prescription.created_at >= today)
        .scalar()
        or 0
    )

    daily_fulfilled = (
        db.query(func.count(Prescription.id))
        .filter(
            and_(Prescription.created_at >= today, Prescription.status == "completed")
        )
        .scalar()
        or 0
    )

    daily_rate = (daily_fulfilled / daily_total * 100) if daily_total > 0 else 0
    prescription_fulfillment_rate.labels(time_period="day").set(daily_rate)

    # Fulfillment rate - weekly
    weekly_total = (
        db.query(func.count(Prescription.id))
        .filter(Prescription.created_at >= week_ago)
        .scalar()
        or 0
    )

    weekly_fulfilled = (
        db.query(func.count(Prescription.id))
        .filter(
            and_(
                Prescription.created_at >= week_ago, Prescription.status == "completed"
            )
        )
        .scalar()
        or 0
    )

    weekly_rate = (weekly_fulfilled / weekly_total * 100) if weekly_total > 0 else 0
    prescription_fulfillment_rate.labels(time_period="week").set(weekly_rate)

    return {
        "daily_fulfillment_rate": daily_rate,
        "weekly_fulfillment_rate": weekly_rate,
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
        "timestamp": datetime.utcnow().isoformat(),
        "daily_active_patients": collect_daily_active_patients(db),
        "appointment_metrics": collect_appointment_metrics(db),
        "prescription_metrics": collect_prescription_metrics(db),
        "patient_risk_metrics": collect_patient_risk_metrics(db),
    }

    return metrics
