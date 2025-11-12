"""
Prescription management router for digital prescription handling.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.cache import cache_clear_pattern, cache_get, cache_set
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.metrics import prescription_created_total
from app.core.rate_limit import limiter
from app.fhir.converters import fhir_converter
from app.models.prescription import Prescription
from app.models.user import User, UserRole
from app.schemas.prescription import PrescriptionCreate, PrescriptionResponse
from app.services.subscription_events import publish_event
from app.tasks import check_prescription_interactions

logger = logging.getLogger(__name__)

PRESCRIPTION_LIST_CACHE_PREFIX = "prescriptions:list"
PRESCRIPTION_DETAIL_CACHE_PREFIX = "prescriptions:detail"
PRESCRIPTION_PATIENT_CACHE_PREFIX = "prescriptions:patient"
DASHBOARD_CACHE_PATTERN = "dashboard:*"
PRESCRIPTION_LIST_TTL_SECONDS = 90
PRESCRIPTION_DETAIL_TTL_SECONDS = 180

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])


@router.post(
    "/",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("20/minute")
def create_prescription(
    prescription_data: PrescriptionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
):
    """
    Create a new prescription.

    Args:
        prescription_data: Prescription information
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user issuing the prescription

    Returns:
        Created prescription
    """
    db_prescription = Prescription(
        **prescription_data.model_dump(),
        tenant_id=current_user.tenant_id,
    )
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)

    cache_set(
        f"{PRESCRIPTION_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{db_prescription.id}",
        PrescriptionResponse.model_validate(db_prescription).model_dump(mode="json"),
        expire=PRESCRIPTION_DETAIL_TTL_SECONDS,
    )
    cache_clear_pattern(f"{PRESCRIPTION_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(
        f"{PRESCRIPTION_PATIENT_CACHE_PREFIX}:{current_user.tenant_id}:{db_prescription.patient_id}"
    )
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)

    prescription_created_total.inc()

    try:
        check_prescription_interactions.delay(
            prescription_id=db_prescription.id,
            medications=[prescription_data.medication_name],
        )
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to queue prescription interaction check: %s", exc)

    log_audit_event(
        db=db,
        action="CREATE",
        resource_type="prescription",
        resource_id=db_prescription.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "patient_id": db_prescription.patient_id,
            "doctor_id": db_prescription.doctor_id,
            "medication": db_prescription.medication_name,
        },
        request=request,
    )
    # Publish FHIR Subscription event (MedicationRequest create)
    try:
        fhir_res = fhir_converter.prescription_to_fhir(db_prescription)
        publish_event(db, current_user.tenant_id, "MedicationRequest", fhir_res)
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish medicationrequest create event: %s", exc)

    return db_prescription


@router.get("/", response_model=List[PrescriptionResponse])
@limiter.limit("60/minute")
def get_prescriptions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])),
):
    """
    Retrieve a list of prescriptions with pagination.

    Args:
        request: Incoming request for auditing
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Authenticated user performing the read

    Returns:
        List of prescriptions
    """
    cache_key = f"{PRESCRIPTION_LIST_CACHE_PREFIX}:{current_user.tenant_id}:{skip}:{limit}"
    cached = cache_get(cache_key)
    if cached is not None:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="prescription",
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={"operation": "list", "skip": skip, "limit": limit, "cached": True},
            request=request,
        )
        return cached

    prescriptions = (
        db.query(Prescription)
        .filter(Prescription.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    serialized = [
        PrescriptionResponse.model_validate(p).model_dump(mode="json") for p in prescriptions
    ]

    cache_set(cache_key, serialized, expire=PRESCRIPTION_LIST_TTL_SECONDS)

    log_audit_event(
        db=db,
        action="READ",
        resource_type="prescription",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"operation": "list", "skip": skip, "limit": limit, "cached": False},
        request=request,
    )

    return serialized


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
@limiter.limit("90/minute")
def get_prescription(
    prescription_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])),
):
    """
    Retrieve a specific prescription by ID.

    Args:
        prescription_id: Prescription ID
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the read

    Returns:
        Prescription record
    """
    cache_key = f"{PRESCRIPTION_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{prescription_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="prescription",
            resource_id=prescription_id,
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={"cached": True},
            request=request,
        )
        return cached

    prescription = (
        db.query(Prescription)
        .filter(
            Prescription.id == prescription_id,
            Prescription.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not prescription:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="prescription",
            resource_id=prescription_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "not_found"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    log_audit_event(
        db=db,
        action="READ",
        resource_type="prescription",
        resource_id=prescription.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        request=request,
    )
    serialized = PrescriptionResponse.model_validate(prescription).model_dump(mode="json")
    cache_set(
        cache_key,
        serialized,
        expire=PRESCRIPTION_DETAIL_TTL_SECONDS,
    )
    return serialized


@router.get("/patient/{patient_id}", response_model=List[PrescriptionResponse])
@limiter.limit("60/minute")
def get_patient_prescriptions(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])),
):
    """
    Retrieve all prescriptions for a specific patient.

    Args:
        patient_id: Patient ID
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the read

    Returns:
        List of patient's prescriptions
    """
    cache_key = f"{PRESCRIPTION_PATIENT_CACHE_PREFIX}:{current_user.tenant_id}:{patient_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        log_audit_event(
            db=db,
            action="READ",
            resource_type="prescription",
            resource_id=patient_id,
            status="success",
            user_id=current_user.id,
            username=current_user.username,
            details={"operation": "patient_prescriptions", "cached": True},
            request=request,
        )
        return cached

    prescriptions = (
        db.query(Prescription)
        .filter(
            Prescription.patient_id == patient_id,
            Prescription.tenant_id == current_user.tenant_id,
        )
        .all()
    )
    serialized = [
        PrescriptionResponse.model_validate(p).model_dump(mode="json") for p in prescriptions
    ]
    cache_set(cache_key, serialized, expire=PRESCRIPTION_LIST_TTL_SECONDS)

    log_audit_event(
        db=db,
        action="READ",
        resource_type="prescription",
        resource_id=patient_id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"operation": "patient_prescriptions", "cached": False},
        request=request,
    )

    return serialized


@router.delete("/{prescription_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_prescription(
    prescription_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
):
    """
    Delete a prescription.

    Args:
        prescription_id: Prescription ID
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user performing the delete
    """
    prescription = (
        db.query(Prescription)
        .filter(
            Prescription.id == prescription_id,
            Prescription.tenant_id == current_user.tenant_id,
        )
        .first()
    )
    if not prescription:
        log_audit_event(
            db=db,
            action="DELETE",
            resource_type="prescription",
            resource_id=prescription_id,
            status="failure",
            user_id=current_user.id,
            username=current_user.username,
            details={"reason": "not_found"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found",
        )

    db.delete(prescription)
    db.commit()

    log_audit_event(
        db=db,
        action="DELETE",
        resource_type="prescription",
        resource_id=prescription.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        request=request,
    )

    cache_clear_pattern(f"{PRESCRIPTION_LIST_CACHE_PREFIX}:{current_user.tenant_id}:*")
    cache_clear_pattern(
        f"{PRESCRIPTION_DETAIL_CACHE_PREFIX}:{current_user.tenant_id}:{prescription_id}"
    )
    cache_clear_pattern(
        f"{PRESCRIPTION_PATIENT_CACHE_PREFIX}:{current_user.tenant_id}:{prescription.patient_id}"
    )
    cache_clear_pattern(DASHBOARD_CACHE_PATTERN)

    # Publish FHIR Subscription event (MedicationRequest delete)
    try:
        publish_event(
            db,
            current_user.tenant_id,
            "MedicationRequest",
            {
                "resourceType": "MedicationRequest",
                "id": str(prescription_id),
                "deleted": True,
            },
        )
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Failed to publish medicationrequest delete event: %s", exc)
