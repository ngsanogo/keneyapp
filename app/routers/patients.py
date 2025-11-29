"""
Patient management router for CRUD operations on patient records.

Refactored to use service layer for business logic while keeping
HTTP/platform concerns (audit, cache, metrics, FHIR events) in router.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.metrics import patient_operations_total
from app.core.rate_limit import limiter
from app.exceptions import DuplicateResourceError, PatientNotFoundError
from app.fhir.converters import fhir_converter
from app.models.user import User, UserRole
from app.schemas.common import (
    FilterParams,
    PaginatedResponse,
    PaginationParams,
    SortParams,
)
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services.cache_service import cache_service
from app.services.patient_security import (
    serialize_patient_collection,
    serialize_patient_dict,
)
from app.services.patient_service import PatientService
from app.services.subscription_events import publish_event

logger = logging.getLogger(__name__)

PATIENT_LIST_TTL_SECONDS = 120
PATIENT_DETAIL_TTL_SECONDS = 300

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

    cache_key = cache_service.generate_key(
        "patients:detail", current_user.tenant_id, db_patient.id
    )
    cache_service.set(cache_key, serialized_patient, ttl=PATIENT_DETAIL_TTL_SECONDS)
    
    # Invalidate list caches
    cache_service.delete_pattern(f"patients:list:{current_user.tenant_id}:*")
    cache_service.delete_pattern("dashboard:*")

    patient_operations_total.labels(operation="create").inc()

    # Publish FHIR Subscription event (Patient create)
    try:
        fhir_res = fhir_converter.patient_to_fhir(db_patient)
        publish_event(db, current_user.tenant_id, "Patient", fhir_res)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish patient create event: %s", exc)

    return serialized_patient


@router.get("/", response_model=PaginatedResponse[PatientResponse])
@limiter.limit("100/minute")
def get_patients(
    request: Request,
    pagination: PaginationParams = Depends(),
    sort: SortParams = Depends(),
    filters: FilterParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """
    Retrieve a list of patients with pagination, sorting, and filtering.

    Args:
        request: Incoming request for auditing
        pagination: Pagination parameters (page, page_size)
        sort: Sorting parameters (sort_by, sort_order)
        filters: Filter parameters (search, date_from, date_to)
        db: Database session
        current_user: Authenticated user performing the read

    Returns:
        Paginated list of patient records
    """
    # Generate cache key including all parameters
    cache_key = cache_service.generate_key(
        "patients:list",
        current_user.tenant_id,
        pagination.page,
        pagination.page_size,
        sort.sort_by,
        sort.sort_order,
        filters.search,
        filters.date_from,
        filters.date_to,
    )
    
    # Try cache first
    cached_result = cache_service.get(cache_key)
    if cached_result:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="patient",
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={
                "operation": "list",
                "page": pagination.page,
                "page_size": pagination.page_size,
                "cached": True,
            },
            request=request,
        )
        return cached_result

    service = PatientService(db)
    
    # Get filtered and sorted patients
    patients, total = service.list_patients_paginated(
        tenant_id=current_user.tenant_id,
        skip=pagination.skip,
        limit=pagination.limit,
        search=filters.search,
        sort_by=sort.sort_by,
        sort_order=sort.sort_order,
        date_from=filters.date_from,
        date_to=filters.date_to,
    )
    
    # Serialize patients (decrypt PHI)
    serialized_patients = serialize_patient_collection(patients)
    
    # Create paginated response
    result = PaginatedResponse.create(
        items=serialized_patients,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    
    # Cache result
    cache_service.set(cache_key, result, ttl=PATIENT_LIST_TTL_SECONDS)

    log_audit_event(
        db=db,
        action="READ",
        resource_type="patient",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "operation": "list",
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
            "cached": False,
        },
        request=request,
    )

    patient_operations_total.labels(operation="list").inc()
    
    return result


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
    cache_key = cache_service.generate_key(
        "patients:detail", current_user.tenant_id, patient_id
    )
    cached_patient = cache_service.get(cache_key)
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
    cache_service.set(
        cache_key, serialized_patient, ttl=PATIENT_DETAIL_TTL_SECONDS
    )
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
    cache_key = cache_service.generate_key(
        "patients:detail", current_user.tenant_id, patient.id
    )
    cache_service.set(cache_key, serialized_patient, ttl=PATIENT_DETAIL_TTL_SECONDS)
    cache_service.delete_pattern(f"patients:list:{current_user.tenant_id}:*")
    cache_service.delete_pattern("dashboard:*")

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

    cache_service.delete_pattern(f"patients:list:{current_user.tenant_id}:*")
    cache_service.delete_pattern("dashboard:*")
    cache_service.delete(
        cache_service.generate_key(
            "patients:detail", current_user.tenant_id, patient_id
        )
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
