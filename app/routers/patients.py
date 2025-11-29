"""
Patient management router for CRUD operations on patient records.

Refactored to use service layer for business logic while keeping
HTTP/platform concerns (audit, cache, metrics, FHIR events) in router.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.metrics import patient_operations_total
from app.core.rate_limit import limiter
from app.exceptions import DuplicateResourceError, PatientNotFoundError
from app.fhir.converters import fhir_converter
from app.models.user import User, UserRole
from app.schemas.bulk_operations import BulkDeleteRequest, BulkOperationResult
from app.schemas.common import (
    FilterParams,
    PaginatedResponse,
    PaginationParams,
    SortParams,
)
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.schemas.patient_filters import PatientAdvancedFilters
from app.services.cache_service import cache_service
from app.services.export_service import ExportService
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
    cache_service.set(cache_key, serialized_patient, ttl=PATIENT_DETAIL_TTL_SECONDS)
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


@router.post("/search/advanced", response_model=PaginatedResponse[PatientResponse])
@limiter.limit("50/minute")
def advanced_patient_search(
    filters: PatientAdvancedFilters,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """
    Advanced patient search with multiple filter criteria.

    Supports filtering by:
    - Demographics (gender, age range, date of birth)
    - Location (city, country)
    - Medical flags (allergies, medical history)
    - Date ranges (created, updated)
    - Text search across multiple fields

    Args:
        filters: Advanced filter parameters
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of matching patients
    """
    service = PatientService(db)

    # Execute advanced search
    patients, total = service.list_patients_advanced(
        tenant_id=current_user.tenant_id,
        search=filters.search,
        gender=filters.gender.value if filters.gender else None,
        min_age=filters.min_age,
        max_age=filters.max_age,
        date_of_birth_from=filters.date_of_birth_from,
        date_of_birth_to=filters.date_of_birth_to,
        city=filters.city,
        country=filters.country,
        has_allergies=filters.has_allergies,
        has_medical_history=filters.has_medical_history,
        created_from=filters.created_from,
        created_to=filters.created_to,
        updated_from=filters.updated_from,
        updated_to=filters.updated_to,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
        skip=filters.skip,
        limit=filters.limit,
    )

    # Decrypt and serialize results
    serialized_patients = serialize_patient_collection(patients)

    # Audit log for advanced search
    log_audit_event(
        db=db,
        action="SEARCH",
        resource_type="patient",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "search_type": "advanced",
            "filters_applied": len(
                [
                    k
                    for k, v in filters.model_dump(exclude_unset=True).items()
                    if v is not None and k not in ["page", "page_size", "sort_by", "sort_order"]
                ]
            ),
            "results_count": len(patients),
        },
        request=request,
    )

    patient_operations_total.labels(operation="search_advanced").inc()

    return PaginatedResponse.create(
        items=serialized_patients,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
    )


@router.post("/bulk/delete", response_model=BulkOperationResult)
@limiter.limit("5/minute")
def bulk_delete_patients(
    bulk_request: BulkDeleteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """
    Bulk delete multiple patients (Admin only).

    Args:
        bulk_request: Request containing patient IDs and confirmation
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Result of bulk operation with success/failure counts
    """
    if not bulk_request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required for bulk delete operation",
        )

    if len(bulk_request.patient_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 patients can be deleted at once",
        )

    service = PatientService(db)
    successful = 0
    failed = 0
    errors = []

    for patient_id in bulk_request.patient_ids:
        try:
            patient = service.get_by_id(patient_id, current_user.tenant_id)
            db.delete(patient)
            successful += 1

            # Clear cache for deleted patient
            cache_service.delete(
                cache_service.generate_key(
                    "patients:detail", current_user.tenant_id, patient_id
                )
            )
        except PatientNotFoundError:
            failed += 1
            errors.append(
                {"patient_id": patient_id, "error": "Patient not found or access denied"}
            )
        except Exception as exc:
            failed += 1
            errors.append({"patient_id": patient_id, "error": str(exc)})

    if successful > 0:
        db.commit()
        # Invalidate list caches
        cache_service.delete_pattern(f"patients:list:{current_user.tenant_id}:*")
        cache_service.delete_pattern("dashboard:*")

    # Audit log
    log_audit_event(
        db=db,
        action="BULK_DELETE",
        resource_type="patient",
        status="partial" if failed > 0 else "success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "total_requested": len(bulk_request.patient_ids),
            "successful": successful,
            "failed": failed,
        },
        request=request,
    )

    patient_operations_total.labels(operation="bulk_delete").inc()

    return BulkOperationResult(
        success=failed == 0,
        total=len(bulk_request.patient_ids),
        successful=successful,
        failed=failed,
        errors=errors,
        message=f"Successfully deleted {successful} patients. {failed} failed."
        if failed > 0
        else f"Successfully deleted {successful} patients.",
    )


@router.get("/export/{format}")
@limiter.limit("10/minute")
def export_patients(
    format: str,
    request: Request,
    include_sensitive: bool = False,
    search: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    """
    Export patient data in various formats (CSV, PDF, JSON).

    Args:
        format: Export format (csv, pdf, json)
        request: Incoming request for auditing
        include_sensitive: Include sensitive medical data (requires special permission)
        search: Optional search filter
        db: Database session
        current_user: Authenticated user

    Returns:
        File download response in requested format
    """
    if format not in ["csv", "pdf", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Supported formats: csv, pdf, json",
        )

    # Only admins and doctors can export sensitive data
    if include_sensitive and current_user.role not in [
        UserRole.ADMIN,
        UserRole.DOCTOR,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to export sensitive data",
        )

    service = PatientService(db)
    export_service = ExportService()

    # Get patients with optional search filter
    patients, _ = service.list_patients_advanced(
        tenant_id=current_user.tenant_id,
        search=search,
        limit=1000,  # Max export limit
    )

    # Serialize and sanitize data
    serialized_patients = serialize_patient_collection(patients)

    # Remove sensitive fields if not authorized
    if not include_sensitive:
        for patient in serialized_patients:
            patient.pop("medical_history", None)
            patient.pop("allergies", None)
            patient.pop("emergency_contact", None)
            patient.pop("emergency_phone", None)

    # Generate export file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "csv":
        content = export_service.export_to_csv(
            serialized_patients,
            columns=[
                "id",
                "first_name",
                "last_name",
                "date_of_birth",
                "gender",
                "email",
                "phone",
                "address",
            ],
        )
        media_type = "text/csv"
        filename = f"patients_export_{timestamp}.csv"

    elif format == "json":
        content = export_service.export_to_json(serialized_patients)
        media_type = "application/json"
        filename = f"patients_export_{timestamp}.json"

    elif format == "pdf":
        content = export_service.export_patients_to_pdf(
            serialized_patients, title="Patient Records Report"
        )
        media_type = "application/pdf"
        filename = f"patients_report_{timestamp}.pdf"

    # Audit log
    log_audit_event(
        db=db,
        action="EXPORT",
        resource_type="patient",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "format": format,
            "count": len(serialized_patients),
            "include_sensitive": include_sensitive,
        },
        request=request,
    )

    patient_operations_total.labels(operation="export").inc()

    return Response(
        content=content if isinstance(content, bytes) else content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
