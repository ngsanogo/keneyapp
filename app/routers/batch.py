"""
Batch operations router for bulk patient management with PHI encryption
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.audit import log_audit_event
from app.core.metrics import patient_operations_total
from app.core.cache import cache_clear_pattern
from app.models.user import User
from app.models.patient import Patient
from app.schemas.patient import PatientCreate
from app.services.patient_security import encrypt_patient_payload, serialize_patient_dict

router = APIRouter(prefix="/batch", tags=["batch"])


def _validate_batch_size(patients: List[PatientCreate]) -> None:
    """Validate batch has correct size."""
    if not patients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Batch must contain at least 1 patient"
        )

    if len(patients) > 100:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Batch size limited to 100 patients",
        )


def _check_duplicate_emails_in_batch(patients: List[PatientCreate]) -> None:
    """Check for duplicate emails within the batch."""
    emails_in_batch = set()
    for idx, patient_data in enumerate(patients):
        if patient_data.email:
            if patient_data.email.lower() in emails_in_batch:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duplicate email in batch: {patient_data.email} (position {idx})",
                )
            emails_in_batch.add(patient_data.email.lower())


def _check_existing_patient(
    db: Session,
    email: str | None,
    tenant_id: int,
    idx: int,
) -> None:
    """Check if patient with email already exists."""
    if email:
        existing = (
            db.query(Patient)
            .filter(
                Patient.email == email,
                Patient.tenant_id == tenant_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Patient with email {email} already exists (position {idx})",
            )


@router.post(
    "/patients",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple patients atomically",
)
async def batch_create_patients(
    patients: List[PatientCreate],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create multiple patients in a single atomic transaction.

    - All patients must be valid or the entire operation fails (rollback)
    - PHI fields are automatically encrypted
    - Audit log created for each patient
    - Cache invalidated on success

    Validation:
    - Rejects empty batches (400)
    - Limits batch size to 100 items
    - Validates all fields before processing
    - Checks for duplicate emails within batch
    """
    _validate_batch_size(patients)
    _check_duplicate_emails_in_batch(patients)

    created_patients = []

    try:
        for idx, patient_data in enumerate(patients):
            _check_existing_patient(db, patient_data.email, current_user.tenant_id, idx)

            # Encrypt PHI fields
            patient_dict = patient_data.model_dump()
            patient_dict["tenant_id"] = current_user.tenant_id
            encrypted_data = encrypt_patient_payload(patient_dict)

            # Create patient with encrypted data
            patient = Patient(**encrypted_data)
            db.add(patient)
            created_patients.append(patient)

        # Commit all at once (atomic)
        db.commit()

        # Refresh and log after successful commit
        response_patients = []
        for idx, patient in enumerate(created_patients):
            db.refresh(patient)

            # Audit logging with sanitized details
            log_audit_event(
                db=db,
                user_id=current_user.id,
                action="CREATE",
                resource_type="Patient",
                resource_id=patient.id,
                details={
                    "batch_operation": True,
                    "batch_position": idx,
                    "batch_total": len(patients),
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "tenant_id": str(current_user.tenant_id),
                },
                request=request,
            )

            # Metrics
            patient_operations_total.labels(operation="create").inc()

            # Serialize with decryption for response
            response_patients.append(serialize_patient_dict(patient))

        # Invalidate caches
        cache_clear_pattern(f"patients:list:{current_user.tenant_id}:*")
        cache_clear_pattern("dashboard:*")

        return {
            "created": len(response_patients),
            "total": len(patients),
            "patients": response_patients,
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Batch create failed: {str(e)}"
        )


def _get_and_validate_patient(
    db: Session,
    patient_id: int | None,
    tenant_id: int,
    idx: int,
) -> Patient:
    """Get patient and validate ownership."""
    if not patient_id:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Each update must include an 'id' field",
        )

    patient = (
        db.query(Patient)
        .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
        .first()
    )

    if not patient:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {patient_id} not found"
        )

    return patient


@router.put("/patients", response_model=dict, summary="Update multiple patients atomically")
async def batch_update_patients(
    updates: List[dict],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update multiple patients in a single atomic transaction.

    Each update dict must contain 'id' and fields to update.
    - PHI fields are automatically encrypted
    - Tenant isolation enforced
    - Audit log created for each update
    """
    updated_patients = []

    try:
        for idx, update_data in enumerate(updates):
            patient_id = update_data.pop("id", None)
            patient = _get_and_validate_patient(db, patient_id, current_user.tenant_id, idx)

            # Encrypt sensitive fields if present
            if any(
                k in update_data
                for k in [
                    "medical_history",
                    "allergies",
                    "address",
                    "emergency_contact",
                    "emergency_phone",
                ]
            ):
                encrypted_data = encrypt_patient_payload(update_data)
                update_data = encrypted_data

            # Update patient fields
            for key, value in update_data.items():
                if hasattr(patient, key):
                    setattr(patient, key, value)

            updated_patients.append(patient)

        # Commit all updates atomically
        db.commit()

        # Refresh, log, and serialize
        response_patients = []
        for idx, patient in enumerate(updated_patients):
            db.refresh(patient)

            log_audit_event(
                db=db,
                user_id=current_user.id,
                action="UPDATE",
                resource_type="Patient",
                resource_id=patient.id,
                details={
                    "batch_operation": True,
                    "batch_position": idx,
                    "batch_total": len(updates),
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "tenant_id": str(current_user.tenant_id),
                },
                request=request,
            )

            patient_operations_total.labels(operation="update").inc()

            response_patients.append(serialize_patient_dict(patient))

        # Invalidate caches
        cache_clear_pattern(f"patients:list:{current_user.tenant_id}:*")
        for patient in updated_patients:
            cache_clear_pattern(f"patients:detail:{current_user.tenant_id}:{patient.id}")
        cache_clear_pattern("dashboard:*")

        return {"updated": len(response_patients), "patients": response_patients}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Batch update failed: {str(e)}"
        )


@router.delete("/patients", response_model=dict, summary="Delete multiple patients atomically")
async def batch_delete_patients(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    patient_ids: List[str] = Query(..., description="List of patient IDs to delete"),
):
    """
    Delete multiple patients in a single atomic transaction.

    - Tenant isolation enforced
    - Audit log created for each deletion
    - Returns count of deleted patients
    """
    deleted_count = 0

    try:
        for idx, patient_id in enumerate(patient_ids):
            patient = (
                db.query(Patient)
                .filter(Patient.id == patient_id, Patient.tenant_id == current_user.tenant_id)
                .first()
            )

            if patient:
                # Store name before deletion
                patient_name = f"{patient.first_name} {patient.last_name}"

                db.delete(patient)
                deleted_count += 1

                log_audit_event(
                    db=db,
                    user_id=current_user.id,
                    action="DELETE",
                    resource_type="Patient",
                    resource_id=patient.id,
                    details={
                        "batch_operation": True,
                        "batch_position": idx,
                        "batch_total": len(patient_ids),
                        "patient_name": patient_name,
                        "tenant_id": str(current_user.tenant_id),
                    },
                    request=request,
                )

                patient_operations_total.labels(operation="delete").inc()

                # Clear cache for deleted patient
                cache_clear_pattern(f"patients:detail:{current_user.tenant_id}:{patient_id}")

        # Commit all deletions atomically
        db.commit()

        # Invalidate list caches
        cache_clear_pattern(f"patients:list:{current_user.tenant_id}:*")
        cache_clear_pattern("dashboard:*")

        return {"deleted": deleted_count, "requested": len(patient_ids)}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Batch delete failed: {str(e)}"
        )
