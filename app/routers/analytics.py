"""
Analytics API endpoints for dashboard metrics and charts
"""

from datetime import datetime, timedelta, date
from typing import Dict, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case

from app.core.dependencies import get_db, require_roles
from app.core.rate_limit import limiter
from app.core.audit import log_audit_event
from app.models.user import User, UserRole
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription
from app.schemas.analytics import (
    DashboardMetrics,
    PatientTrendResponse,
    AppointmentStatsResponse,
    GenderDistributionResponse,
    CustomPeriodMetrics,
    DateRangeParams,
    AgeDistributionResponse,
    TopConditionsResponse,
    DoctorPerformanceResponse,
)
from fastapi import Request

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
@limiter.limit("100/minute")
async def get_dashboard_metrics(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """Get key dashboard metrics with change percentages"""
    tenant_id = current_user.tenant_id

    # Calculate date ranges
    today = datetime.now().date()
    month_start = today.replace(day=1)

    # Total patients and change
    total_patients = (
        db.query(func.count(Patient.id)).filter(Patient.tenant_id == tenant_id).scalar()
        or 0
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
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
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
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
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
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
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


@router.get("/custom-period", response_model=CustomPeriodMetrics)
@limiter.limit("100/minute")
async def get_custom_period_metrics(
    request: Request,
    date_from: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """
    Get comprehensive metrics for a custom date range.

    Supports flexible date ranges:
    - Both dates: Exact range
    - Only date_from: From date to now
    - Only date_to: 30 days before date_to to date_to
    - Neither: Last 30 days (default)
    """
    tenant_id = current_user.tenant_id
    date_params = DateRangeParams(date_from=date_from, date_to=date_to)
    start_dt, end_dt = date_params.get_date_range()

    # Total patients in system
    total_patients = (
        db.query(func.count(Patient.id)).filter(Patient.tenant_id == tenant_id).scalar()
        or 0
    )

    # New patients in period
    new_patients = (
        db.query(func.count(Patient.id))
        .filter(
            and_(
                Patient.tenant_id == tenant_id,
                Patient.created_at >= start_dt,
                Patient.created_at <= end_dt,
            )
        )
        .scalar()
        or 0
    )

    # Appointments in period
    appointments_query = db.query(Appointment).filter(
        and_(
            Appointment.tenant_id == tenant_id,
            Appointment.appointment_date >= start_dt,
            Appointment.appointment_date <= end_dt,
        )
    )

    total_appointments = appointments_query.count()
    completed_appointments = appointments_query.filter(
        Appointment.status == AppointmentStatus.COMPLETED
    ).count()
    cancelled_appointments = appointments_query.filter(
        Appointment.status == AppointmentStatus.CANCELLED
    ).count()
    pending_appointments = appointments_query.filter(
        Appointment.status == AppointmentStatus.SCHEDULED
    ).count()

    # Prescriptions in period
    total_prescriptions = (
        db.query(func.count(Prescription.id))
        .filter(
            and_(
                Prescription.tenant_id == tenant_id,
                Prescription.created_at >= start_dt,
                Prescription.created_at <= end_dt,
            )
        )
        .scalar()
        or 0
    )

    # Unique doctors seen
    unique_doctors = (
        db.query(func.count(func.distinct(Appointment.doctor_id)))
        .filter(
            and_(
                Appointment.tenant_id == tenant_id,
                Appointment.appointment_date >= start_dt,
                Appointment.appointment_date <= end_dt,
            )
        )
        .scalar()
        or 0
    )

    log_audit_event(
        db=db,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="READ",
        resource_type="analytics_custom_period",
        details={
            "period_start": start_dt.date().isoformat(),
            "period_end": end_dt.date().isoformat(),
        },
        request=request,
    )

    return CustomPeriodMetrics(
        period_start=start_dt.date(),
        period_end=end_dt.date(),
        total_patients=total_patients,
        new_patients=new_patients,
        total_appointments=total_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments,
        pending_appointments=pending_appointments,
        total_prescriptions=total_prescriptions,
        unique_doctors_seen=unique_doctors,
    )


@router.get("/age-distribution", response_model=AgeDistributionResponse)
@limiter.limit("100/minute")
async def get_age_distribution(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """Get patient age distribution in ranges."""
    tenant_id = current_user.tenant_id

    # Get all patients with DOB
    patients = (
        db.query(Patient.date_of_birth)
        .filter(
            and_(
                Patient.tenant_id == tenant_id,
                Patient.date_of_birth.isnot(None),
            )
        )
        .all()
    )

    # Calculate age ranges
    age_ranges = {
        "0-10": 0,
        "11-20": 0,
        "21-30": 0,
        "31-40": 0,
        "41-50": 0,
        "51-60": 0,
        "61-70": 0,
        "71-80": 0,
        "81+": 0,
    }

    from datetime import date as date_type

    today = date_type.today()

    for patient in patients:
        if patient.date_of_birth:
            age = (
                today.year
                - patient.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (patient.date_of_birth.month, patient.date_of_birth.day)
                )
            )

            if age <= 10:
                age_ranges["0-10"] += 1
            elif age <= 20:
                age_ranges["11-20"] += 1
            elif age <= 30:
                age_ranges["21-30"] += 1
            elif age <= 40:
                age_ranges["31-40"] += 1
            elif age <= 50:
                age_ranges["41-50"] += 1
            elif age <= 60:
                age_ranges["51-60"] += 1
            elif age <= 70:
                age_ranges["61-70"] += 1
            elif age <= 80:
                age_ranges["71-80"] += 1
            else:
                age_ranges["81+"] += 1

    labels = list(age_ranges.keys())
    values = list(age_ranges.values())

    log_audit_event(
        db=db,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="READ",
        resource_type="analytics_age_distribution",
        details={"total_patients": sum(values)},
        request=request,
    )

    return AgeDistributionResponse(labels=labels, values=values)


@router.get("/doctor-performance", response_model=DoctorPerformanceResponse)
@limiter.limit("100/minute")
async def get_doctor_performance(
    request: Request,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """
    Get doctor performance metrics (Admin only).

    Includes:
    - Total appointments per doctor
    - Completion rate
    - Average rating (placeholder for future implementation)
    """
    tenant_id = current_user.tenant_id
    date_params = DateRangeParams(date_from=date_from, date_to=date_to)
    start_dt, end_dt = date_params.get_date_range()

    # Query appointments grouped by doctor
    doctor_stats = (
        db.query(
            User.full_name,
            func.count(Appointment.id).label("total_appointments"),
            func.sum(
                case((Appointment.status == AppointmentStatus.COMPLETED, 1), else_=0)
            ).label("completed_appointments"),
        )
        .join(Appointment, Appointment.doctor_id == User.id)
        .filter(
            and_(
                User.tenant_id == tenant_id,
                User.role == UserRole.DOCTOR,
                Appointment.appointment_date >= start_dt,
                Appointment.appointment_date <= end_dt,
            )
        )
        .group_by(User.id, User.full_name)
        .all()
    )

    doctor_names = []
    appointments_count = []
    completion_rate = []
    average_rating = []

    for stat in doctor_stats:
        doctor_names.append(stat.full_name)
        appointments_count.append(stat.total_appointments)

        rate = (
            (stat.completed_appointments / stat.total_appointments * 100)
            if stat.total_appointments > 0
            else 0
        )
        completion_rate.append(round(rate, 1))
        average_rating.append(4.5)  # Placeholder for future rating system

    log_audit_event(
        db=db,
        user_id=current_user.id,
        tenant_id=tenant_id,
        action="READ",
        resource_type="analytics_doctor_performance",
        details={
            "period_start": start_dt.date().isoformat(),
            "period_end": end_dt.date().isoformat(),
            "doctors_count": len(doctor_names),
        },
        request=request,
    )

    return DoctorPerformanceResponse(
        doctor_names=doctor_names,
        appointments_count=appointments_count,
        completion_rate=completion_rate,
        average_rating=average_rating,
    )
