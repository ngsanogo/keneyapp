from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.core.audit import log_audit_event
from app.core.cache import cache_get, cache_set, cache_clear_pattern
from app.core.metrics import patient_operations_total
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.services.appointment_service import AppointmentService
from app.models.user import UserRole


router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/", response_model=List[AppointmentResponse])
@limiter.limit("100/minute")
def list_appointments(
    request: Request,
    patient_id: Optional[int] = None,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])(current_user)
    tenant_id = current_user.tenant_id

    cache_key = f"appointments:list:{tenant_id}:{patient_id or 'all'}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    service = AppointmentService(db)
    items = service.list(tenant_id=tenant_id, patient_id=patient_id)
    cache_set(cache_key, items, ttl_seconds=120)

    log_audit_event(
        action="read",
        resource="appointments",
        request=request,
        user_id=current_user.id,
        tenant_id=tenant_id,
        details={"patient_id": patient_id} if patient_id else {"list": True},
    )
    return items


@router.get("/{appointment_id}", response_model=AppointmentResponse)
@limiter.limit("100/minute")
def get_appointment(
    request: Request,
    appointment_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])(current_user)
    tenant_id = current_user.tenant_id
    cache_key = f"appointments:detail:{tenant_id}:{appointment_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    service = AppointmentService(db)
    try:
        appt = service.get_by_id(appointment_id, tenant_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Appointment not found")

    cache_set(cache_key, appt, ttl_seconds=300)
    log_audit_event(
        action="read",
        resource="appointments",
        request=request,
        user_id=current_user.id,
        tenant_id=tenant_id,
        details={"appointment_id": appointment_id},
    )
    return appt


@router.post("/", response_model=AppointmentResponse, status_code=201)
@limiter.limit("10/minute")
def create_appointment(
    request: Request,
    payload: AppointmentCreate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST])(current_user)
    tenant_id = current_user.tenant_id
    service = AppointmentService(db)
    appt = service.create(payload.model_dump(), tenant_id)

    cache_clear_pattern(f"appointments:list:{tenant_id}:*")
    cache_clear_pattern("dashboard:*")

    patient_operations_total.labels(action="create", tenant_id=str(tenant_id)).inc()
    log_audit_event(
        action="create",
        resource="appointments",
        request=request,
        user_id=current_user.id,
        tenant_id=tenant_id,
        details={"appointment_id": appt.id, "patient_id": appt.patient_id},
    )
    return appt


@router.put("/{appointment_id}", response_model=AppointmentResponse)
@limiter.limit("10/minute")
def update_appointment(
    request: Request,
    appointment_id: int,
    payload: AppointmentUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST])(current_user)
    tenant_id = current_user.tenant_id
    service = AppointmentService(db)
    appt = service.update(appointment_id, payload.model_dump(exclude_unset=True), tenant_id)

    cache_clear_pattern(f"appointments:detail:{tenant_id}:{appointment_id}")
    cache_clear_pattern(f"appointments:list:{tenant_id}:*")
    cache_clear_pattern("dashboard:*")

    patient_operations_total.labels(action="update", tenant_id=str(tenant_id)).inc()
    log_audit_event(
        action="update",
        resource="appointments",
        request=request,
        user_id=current_user.id,
        tenant_id=tenant_id,
        details={"appointment_id": appointment_id},
    )
    return appt


@router.delete("/{appointment_id}", status_code=204)
@limiter.limit("10/minute")
def delete_appointment(
    request: Request,
    appointment_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    require_roles([UserRole.ADMIN, UserRole.DOCTOR])(current_user)
    tenant_id = current_user.tenant_id
    service = AppointmentService(db)
    service.delete(appointment_id, tenant_id)

    cache_clear_pattern(f"appointments:detail:{tenant_id}:{appointment_id}")
    cache_clear_pattern(f"appointments:list:{tenant_id}:*")
    cache_clear_pattern("dashboard:*")

    patient_operations_total.labels(action="delete", tenant_id=str(tenant_id)).inc()
    log_audit_event(
        action="delete",
        resource="appointments",
        request=request,
        user_id=current_user.id,
        tenant_id=tenant_id,
        details={"appointment_id": appointment_id},
    )
    return None


"""
Appointment management router for scheduling and tracking appointments.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.cache import cache_clear_pattern, cache_get, cache_set
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.metrics import appointment_bookings_total
from app.core.rate_limit import limiter
from app.fhir.converters import fhir_converter
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.services.subscription_events import publish_event
from app.tasks import send_appointment_reminder

logger = logging.getLogger(__name__)

APPOINTMENT_LIST_CACHE_PREFIX = "appointments:list"
APPOINTMENT_DETAIL_CACHE_PREFIX = "appointments:detail"
DASHBOARD_CACHE_PATTERN = "dashboard:*"
APPOINTMENT_LIST_TTL_SECONDS = 60
APPOINTMENT_DETAIL_TTL_SECONDS = 180

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
def create_appointment(
    appointment_data: AppointmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST])
    ),
):
    """
    Create a new appointment.

    Args:
        appointment_data: Appointment information
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user creating the appointment

    Returns:
        Created appointment
    """
    db_appointment = Appointment(
        **appointment_data.model_dump(),
        tenant_id=current_user.tenant_id,
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)

    cache_set(
        f"{APPOINTMENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{db_appointment.id}",
        AppointmentResponse.model_validate(db_appointment).model_dump(mode="json"),
        expire=APPOINTMENT_DETAIL_TTL_SECONDS,
    )
    cache_clear_pattern(f"{APPOINTMENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)

    # Track metrics
    appointment_bookings_total.labels(status=db_appointment.status.value).inc()

    # Queue reminder notifications (best effort)
    try:
        patient = db.query(Patient).filter(Patient.id == db_appointment.patient_id).first()
        patient_email = patient.email if patient else None
        send_appointment_reminder.delay(
            appointment_id=db_appointment.id,
            patient_email=patient_email or "",
        )
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to queue appointment reminder: %s", exc)

    log_audit_event(
        db=db,
        action="CREATE",
        resource_type="appointment",
        resource_id=db_appointment.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "patient_id": db_appointment.patient_id,
            "doctor_id": db_appointment.doctor_id,
            "appointment_date": db_appointment.appointment_date.isoformat(),
        },
        request=request,
    )

    # Publish FHIR Subscription event (Appointment create)
    try:
        fhir_res = fhir_converter.appointment_to_fhir(db_appointment)
        publish_event(db, current_user.tenant_id, "Appointment", fhir_res)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish appointment create event: %s", exc)

    return db_appointment


@router.get("/", response_model=List[AppointmentResponse])
@limiter.limit("60/minute")
def get_appointments(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[AppointmentStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST])
    ),
):
    """
    Retrieve a list of appointments with pagination.

    Args:
        request: Incoming request for auditing
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Optional appointment status to filter by
        db: Database session
        current_user: Authenticated user performing the read

    Returns:
        List of appointments
    """
    status_key = status_filter.value if status_filter else "all"
    cache_key = (
        f"{APPOINTMENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:{skip}:{limit}:{status_key}"
    )
    cached_appointments = cache_get(cache_key)
    if cached_appointments is not None:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="appointment",
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "operation": "list",
                "skip": skip,
                "limit": limit,
                "status": status_key,
                "cached": True,
            },
            request=request,
        )
        return cached_appointments

    query = db.query(Appointment).filter(Appointment.tenant_id == current_user.tenant_id)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    appointments = query.offset(skip).limit(limit).all()
    serialized_appointments = [
        AppointmentResponse.model_validate(appt).model_dump(mode="json") for appt in appointments
    ]

    cache_set(cache_key, serialized_appointments, expire=APPOINTMENT_LIST_TTL_SECONDS)

    log_audit_event(
        db=db,
        action="READ",
        resource_type="appointment",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "operation": "list",
            "skip": skip,
            "limit": limit,
            "status": status_key,
            "cached": False,
        },
        request=request,
    )

    return serialized_appointments


@router.get("/{appointment_id}", response_model=AppointmentResponse)
@limiter.limit("120/minute")
def get_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST])
    ),
):
    """
    Retrieve a specific appointment by ID.

    Args:
        appointment_id: Appointment ID
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the read

    Returns:
        Appointment record
    """
    cache_key = f"{APPOINTMENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{appointment_id}"
    cached_appointment = cache_get(cache_key)
    if cached_appointment is not None:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="appointment",
            resource_id=appointment_id,
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={"cached": True},
            request=request,
        )
        return cached_appointment

    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not appointment:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="appointment",
            resource_id=appointment_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "not_found"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    log_audit_event(
        db=db,
        action="READ",
        resource_type="appointment",
        resource_id=appointment.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        request=request,
    )
    serialized = AppointmentResponse.model_validate(appointment).model_dump(mode="json")
    cache_set(
        cache_key,
        serialized,
        expire=APPOINTMENT_DETAIL_TTL_SECONDS,
    )
    return serialized


@router.put("/{appointment_id}", response_model=AppointmentResponse)
@limiter.limit("15/minute")
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
):
    """
    Update an appointment.

    Args:
        appointment_id: Appointment ID
        appointment_data: Updated appointment information
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the update

    Returns:
        Updated appointment
    """
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not appointment:
        log_audit_event(
            db=db,
            action="UPDATE",
            resource_type="appointment",
            resource_id=appointment_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "not_found"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    # Update only provided fields
    update_data = appointment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="appointment",
        resource_id=appointment.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"updated_fields": list(update_data.keys())},
        request=request,
    )

    serialized = AppointmentResponse.model_validate(appointment).model_dump(mode="json")
    cache_set(
        f"{APPOINTMENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{appointment.id}",
        serialized,
        expire=APPOINTMENT_DETAIL_TTL_SECONDS,
    )
    cache_clear_pattern(f"{APPOINTMENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)

    # Publish FHIR Subscription event (Appointment update)
    try:
        fhir_res = fhir_converter.appointment_to_fhir(appointment)
        publish_event(db, current_user.tenant_id, "Appointment", fhir_res)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish appointment update event: %s", exc)

    return serialized


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_appointment(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Delete an appointment.

    Args:
        appointment_id: Appointment ID
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the delete
    """
    appointment = (
        db.query(Appointment)
        .filter(
            Appointment.id == appointment_id,
            Appointment.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not appointment:
        log_audit_event(
            db=db,
            action="DELETE",
            resource_type="appointment",
            resource_id=appointment_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "not_found"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )

    db.delete(appointment)
    db.commit()

    log_audit_event(
        db=db,
        action="DELETE",
        resource_type="appointment",
        resource_id=appointment.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        request=request,
    )

    cache_clear_pattern(f"{APPOINTMENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)
    cache_clear_pattern(
        f"{APPOINTMENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{appointment_id}"
    )

    # Publish FHIR Subscription event (Appointment delete)
    try:
        publish_event(
            db,
            current_user.tenant_id,
            "Appointment",
            {"resourceType": "Appointment", "id": str(appointment_id), "deleted": True},
        )
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish appointment delete event: %s", exc)
