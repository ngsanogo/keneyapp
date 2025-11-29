"""
Analytics API endpoints for dashboard metrics and charts
"""

from datetime import datetime, timedelta
from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.dependencies import get_db, require_roles
from app.core.rate_limit import limiter
from app.core.audit import log_audit_event
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.schemas.analytics import (
    DashboardMetrics,
    PatientTrendResponse,
    AppointmentStatsResponse,
    GenderDistributionResponse,
)
from fastapi import Request

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
@limiter.limit("100/minute")
async def get_dashboard_metrics(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST])
    ),
):
    """Get key dashboard metrics with change percentages"""
    tenant_id = current_user.tenant_id

    # Calculate date ranges
    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Total patients and change
    total_patients = (
        db.query(func.count(Patient.id)).filter(Patient.tenant_id == tenant_id).scalar() or 0
    )

    last_month_patients = (
        db.query(func.count(Patient.id))
        .filter(
            and_(
                Patient.tenant_id == tenant_id,
                Patient.created_at < month_start,
            )
        )
        .scalar()
        or 0
    )

    patients_change = (
        ((total_patients - last_month_patients) / last_month_patients * 100)
        if last_month_patients > 0
        else 0
    )

    # Appointments today
    appointments_today = (
        db.query(func.count(Appointment.id))
        .filter(
            and_(
                Appointment.tenant_id == tenant_id,
                func.date(Appointment.appointment_date) == today,
            )
        )
        .scalar()
        or 0
    )

    # Active doctors
    active_doctors = (
        db.query(func.count(User.id))
        .filter(
            and_(
                User.tenant_id == tenant_id,
                User.role == UserRole.DOCTOR,
                User.is_active.is_(True),
            )
        )
        .scalar()
        or 0
    )

    # Audit log
    log_audit_event(
        db=db,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="READ",
        resource_type="analytics_metrics",
        details={"metric_type": "dashboard_overview"},
        request=request,
    )

    return DashboardMetrics(
        total_patients=total_patients,
        patients_change=round(patients_change, 1),
        appointments_today=appointments_today,
        appointments_change=0,  # Placeholder
        active_doctors=active_doctors,
        doctors_change=0,  # Placeholder
        monthly_revenue=0,  # Placeholder for future implementation
        revenue_change=0,
    )


@router.get("/patient-trend", response_model=PatientTrendResponse)
@limiter.limit("100/minute")
async def get_patient_trend(
    request: Request,
    period: str = "30d",
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST])
    ),
):
    """Get patient registration trend over time"""
    tenant_id = current_user.tenant_id

    # Parse period
    days = int(period.rstrip("d")) if period.endswith("d") else 30
    start_date = datetime.now() - timedelta(days=days)

    # Query daily patient counts
    results = (
        db.query(
            func.date(Patient.created_at).label("date"),
            func.count(Patient.id).label("count"),
        )
        .filter(
            and_(
                Patient.tenant_id == tenant_id,
                Patient.created_at >= start_date,
            )
        )
        .group_by(func.date(Patient.created_at))
        .order_by(func.date(Patient.created_at))
        .all()
    )

    # Fill in missing dates with zero counts
    date_range = [start_date.date() + timedelta(days=i) for i in range(days + 1)]
    result_dict = {result.date: result.count for result in results}

    labels = [date.strftime("%Y-%m-%d") for date in date_range]
    values = [result_dict.get(date, 0) for date in date_range]

    log_audit_event(
        db=db,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="READ",
        resource_type="analytics_patient_trend",
        details={"period": period, "data_points": len(labels)},
        request=request,
    )

    return PatientTrendResponse(labels=labels, values=values)


@router.get("/appointments", response_model=AppointmentStatsResponse)
@limiter.limit("100/minute")
async def get_appointment_stats(
    request: Request,
    period: str = "7d",
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST])
    ),
):
    """Get appointment statistics by status"""
    tenant_id = current_user.tenant_id

    days = int(period.rstrip("d")) if period.endswith("d") else 7
    start_date = datetime.now() - timedelta(days=days)

    date_range = [start_date.date() + timedelta(days=i) for i in range(days + 1)]
    labels = [date.strftime("%Y-%m-%d") for date in date_range]

    # Query appointments grouped by date and status
    results = (
        db.query(
            func.date(Appointment.appointment_date).label("date"),
            Appointment.status,
            func.count(Appointment.id).label("count"),
        )
        .filter(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.appointment_date >= start_date,
            )
        )
        .group_by(func.date(Appointment.appointment_date), Appointment.status)
        .all()
    )

    # Organize data by status
    data_by_status: Dict[str, Dict] = {
        "completed": {},
        "pending": {},
        "cancelled": {},
    }

    for result in results:
        status_key = result.status.lower() if result.status else "pending"
        if status_key in data_by_status:
            data_by_status[status_key][result.date] = result.count

    # Fill in missing dates
    completed = [data_by_status["completed"].get(date, 0) for date in date_range]
    pending = [data_by_status["pending"].get(date, 0) for date in date_range]
    cancelled = [data_by_status["cancelled"].get(date, 0) for date in date_range]

    log_audit_event(
        db=db,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="READ",
        resource_type="analytics_appointments",
        details={"period": period, "data_points": len(labels)},
        request=request,
    )

    return AppointmentStatsResponse(
        labels=labels,
        completed=completed,
        pending=pending,
        cancelled=cancelled,
    )


@router.get("/gender-distribution", response_model=GenderDistributionResponse)
@limiter.limit("100/minute")
async def get_gender_distribution(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST])
    ),
):
    """Get patient gender distribution"""
    tenant_id = current_user.tenant_id

    results = (
        db.query(
            Patient.gender,
            func.count(Patient.id).label("count"),
        )
        .filter(Patient.tenant_id == tenant_id)
        .group_by(Patient.gender)
        .all()
    )

    labels = []
    values = []

    for result in results:
        gender = result.gender or "Other"
        labels.append(gender.capitalize())
        values.append(result.count)

    log_audit_event(
        db=db,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="READ",
        resource_type="analytics_gender_distribution",
        details={"categories": len(labels)},
        request=request,
    )

    return GenderDistributionResponse(labels=labels, values=values)
