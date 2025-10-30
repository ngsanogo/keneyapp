"""
Patient management router for CRUD operations on patient records.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.cache import cache_clear_pattern, cache_get, cache_set
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.metrics import patient_operations_total
from app.core.rate_limit import limiter
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.tasks import generate_patient_report

logger = logging.getLogger(__name__)

PATIENT_LIST_CACHE_PREFIX = "patients:list"
PATIENT_DETAIL_CACHE_PREFIX = "patients:detail"
PATIENT_LIST_TTL_SECONDS = 120
PATIENT_DETAIL_TTL_SECONDS = 300
DASHBOARD_CACHE_PATTERN = "dashboard:*"

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def create_patient(
    patient_data: PatientCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])
    ),
):
    """
    Create a new patient record.

    Args:
        patient_data: Patient information
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the operation

    Returns:
        Created patient record
    """
    # Check if email already exists
    if patient_data.email:
        existing = (
            db.query(Patient)
            .filter(
                Patient.email == patient_data.email,
                Patient.tenant_id == current_user.tenant_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    db_patient = Patient(
        **patient_data.model_dump(),
        tenant_id=current_user.tenant_id,
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    log_audit_event(
        db=db,
        action="CREATE",
        resource_type="patient",
        resource_id=db_patient.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"patient_email": db_patient.email},
        request=request,
    )

    # Cache management
    cache_set(
        f"{PATIENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{db_patient.id}",
        PatientResponse.model_validate(db_patient).model_dump(mode="json"),
        expire=PATIENT_DETAIL_TTL_SECONDS,
    )
    cache_clear_pattern(f"{PATIENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)

    patient_operations_total.labels(operation="create").inc()

    # Trigger background patient report generation
    try:
        generate_patient_report.delay(db_patient.id)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to queue patient report generation: %s", exc)

    return db_patient


@router.get("/", response_model=List[PatientResponse])
@limiter.limit("60/minute")
def get_patients(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """
    Retrieve a list of patients with pagination.

    Args:
        request: Incoming request for auditing
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user performing the read

    Returns:
        List of patient records
    """
    cache_key = f"{PATIENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:{skip}:{limit}"
    cached_patients = cache_get(cache_key)
    if cached_patients is not None:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="patient",
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={"operation": "list", "skip": skip, "limit": limit, "cached": True},
            request=request,
        )
        return cached_patients

    patients = (
        db.query(Patient)
        .filter(Patient.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    serialized_patients = [
        PatientResponse.model_validate(patient).model_dump(mode="json")
        for patient in patients
    ]

    cache_set(cache_key, serialized_patients, expire=PATIENT_LIST_TTL_SECONDS)

    log_audit_event(
        db=db,
        action="READ",
        resource_type="patient",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "operation": "list",
            "skip": skip,
            "limit": limit,
            "cached": False,
        },
        request=request,
    )

    return serialized_patients


@router.get("/{patient_id}", response_model=PatientResponse)
@limiter.limit("120/minute")
def get_patient(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """
    Retrieve a specific patient by ID.

    Args:
        patient_id: Patient ID
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the read

    Returns:
        Patient record
    """
    cache_key = f"{PATIENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{patient_id}"
    cached_patient = cache_get(cache_key)
    if cached_patient is not None:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="patient",
            resource_id=patient_id,
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={"cached": True},
            request=request,
        )
        return cached_patient

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not patient:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="patient",
            resource_id=patient_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "not_found"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )

    log_audit_event(
        db=db,
        action="READ",
        resource_type="patient",
        resource_id=patient.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        request=request,
    )
    serialized_patient = PatientResponse.model_validate(patient).model_dump(mode="json")
    cache_set(cache_key, serialized_patient, expire=PATIENT_DETAIL_TTL_SECONDS)
    return serialized_patient


@router.put("/{patient_id}", response_model=PatientResponse)
@limiter.limit("10/minute")
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
):
    """
    Update a patient record.

    Args:
        patient_id: Patient ID
        patient_data: Updated patient information
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the operation

    Returns:
        Updated patient record
    """
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not patient:
        log_audit_event(
            db=db,
            action="UPDATE",
            resource_type="patient",
            resource_id=patient_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "not_found"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )

    # Update only provided fields
    update_data = patient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="patient",
        resource_id=patient.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"updated_fields": list(update_data.keys())},
        request=request,
    )

    serialized_patient = PatientResponse.model_validate(patient).model_dump(mode="json")
    cache_set(
        f"{PATIENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{patient.id}",
        serialized_patient,
        expire=PATIENT_DETAIL_TTL_SECONDS,
    )
    cache_clear_pattern(f"{PATIENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)

    patient_operations_total.labels(operation="update").inc()

    try:
        generate_patient_report.delay(patient.id)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to queue patient report generation: %s", exc)

    return serialized_patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def delete_patient(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Delete a patient record.

    Args:
        patient_id: Patient ID
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the operation
    """
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id,
            Patient.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not patient:
        log_audit_event(
            db=db,
            action="DELETE",
            resource_type="patient",
            resource_id=patient_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "not_found"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found"
        )

    db.delete(patient)
    db.commit()

    log_audit_event(
        db=db,
        action="DELETE",
        resource_type="patient",
        resource_id=patient.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        request=request,
    )

    cache_clear_pattern(f"{PATIENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)
    cache_clear_pattern(
        f"{PATIENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{patient_id}"
    )

    patient_operations_total.labels(operation="delete").inc()
