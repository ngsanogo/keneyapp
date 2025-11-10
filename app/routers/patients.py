"""
Patient management router for CRUD operations on patient records.

Refactored to use service layer for business logic while keeping
HTTP/platform concerns (audit, cache, metrics, FHIR events) in router.
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
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.fhir.converters import fhir_converter
from app.services.subscription_events import publish_event
from app.services.patient_security import (
    serialize_patient_dict,
    serialize_patient_collection,
)
from app.services.patient_service import PatientService
from app.exceptions import (
    PatientNotFoundError,
    DuplicateResourceError,
)

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
    service = PatientService(db)

    try:
        db_patient = service.create_patient(patient_data, current_user.tenant_id)
        db.commit()
    except DuplicateResourceError as exc:
        log_audit_event(
            db=db,
            action="CREATE",
            resource_type="patient",
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "duplicate_email", "email": patient_data.email},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.detail),
        )

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
    serialized_patient = serialize_patient_dict(db_patient)

    cache_set(
        f"{PATIENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{db_patient.id}",
        serialized_patient,
        expire=PATIENT_DETAIL_TTL_SECONDS,
    )
    cache_clear_pattern(f"{PATIENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)

    patient_operations_total.labels(operation="create").inc()

    # Publish FHIR Subscription event (Patient create)
    try:
        fhir_res = fhir_converter.patient_to_fhir(db_patient)
        publish_event(db, current_user.tenant_id, "Patient", fhir_res)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish patient create event: %s", exc)

    return serialized_patient


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

    service = PatientService(db)
    patients = service.list_patients(current_user.tenant_id, skip=skip, limit=limit)
    serialized_patients = serialize_patient_collection(patients)

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

    service = PatientService(db)
    try:
        patient = service.get_by_id(patient_id, current_user.tenant_id)
    except PatientNotFoundError:
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
    serialized_patient = serialize_patient_dict(patient)
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
    service = PatientService(db)
    try:
        patient = service.update_patient(
            patient_id, patient_data, current_user.tenant_id
        )
        db.commit()
    except PatientNotFoundError:
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
    except DuplicateResourceError as exc:
        log_audit_event(
            db=db,
            action="UPDATE",
            resource_type="patient",
            resource_id=patient_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "duplicate_email"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.detail),
        )

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="patient",
        resource_id=patient.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "updated_fields": list(patient_data.model_dump(exclude_unset=True).keys())
        },
        request=request,
    )

    serialized_patient = serialize_patient_dict(patient)
    cache_set(
        f"{PATIENT_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{patient.id}",
        serialized_patient,
        expire=PATIENT_DETAIL_TTL_SECONDS,
    )
    cache_clear_pattern(f"{PATIENT_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)

    patient_operations_total.labels(operation="update").inc()

    # Publish FHIR Subscription event (Patient update)
    try:
        fhir_res = fhir_converter.patient_to_fhir(patient)
        publish_event(db, current_user.tenant_id, "Patient", fhir_res)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish patient update event: %s", exc)

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
    service = PatientService(db)
    try:
        service.delete_patient(patient_id, current_user.tenant_id)
        db.commit()
    except PatientNotFoundError:
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

    log_audit_event(
        db=db,
        action="DELETE",
        resource_type="patient",
        resource_id=patient_id,
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

    # Publish FHIR Subscription event (Patient delete)
    try:
        publish_event(
            db,
            current_user.tenant_id,
            "Patient",
            {"resourceType": "Patient", "id": str(patient_id), "deleted": True},
        )
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish patient delete event: %s", exc)
