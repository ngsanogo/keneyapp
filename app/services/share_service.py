"""
Service for medical record sharing with temporary secure links.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.models.medical_record_share import MedicalRecordShare, ShareScope, ShareStatus
from app.models.patient import Patient
from app.schemas.medical_record_share import ShareCreate, SharedMedicalRecord


def create_share(
    db: Session,
    share_data: ShareCreate,
    user_id: int,
    tenant_id: str,
    request: Optional[Request] = None,
) -> MedicalRecordShare:
    """
    Create a new medical record share with temporary access token.
    """
    # Verify patient exists and belongs to tenant
    patient = (
        db.query(Patient)
        .filter(Patient.id == share_data.patient_id, Patient.tenant_id == tenant_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or access denied",
        )

    # Generate token and optional PIN
    share_token = MedicalRecordShare.generate_token()
    access_pin = MedicalRecordShare.generate_pin() if share_data.require_pin else None

    # Calculate expiry
    expires_at = datetime.now(timezone.utc) + timedelta(hours=share_data.expires_in_hours)

    # Convert custom resources to JSON
    custom_resources_json = None
    if share_data.custom_resources:
        custom_resources_json = json.dumps(share_data.custom_resources)

    # Create share
    share = MedicalRecordShare(
        patient_id=share_data.patient_id,
        shared_by_user_id=user_id,
        share_token=share_token,
        scope=share_data.scope,
        custom_resources=custom_resources_json,
        recipient_email=share_data.recipient_email,
        recipient_name=share_data.recipient_name,
        access_pin=access_pin,
        expires_at=expires_at,
        max_access_count=share_data.max_access_count,
        purpose=share_data.purpose,
        notes=share_data.notes,
        consent_given=True,
        consent_date=datetime.now(timezone.utc),
        tenant_id=tenant_id,
    )

    db.add(share)
    db.commit()
    db.refresh(share)

    # Audit log
    if request:
        log_audit_event(
            db=db,
            user_id=user_id,
            action="CREATE",
            resource_type="medical_record_share",
            resource_id=int(share.id) if share.id else None,
            details={
                "patient_id": share_data.patient_id,
                "scope": share_data.scope.value,
                "recipient": share_data.recipient_email or share_data.recipient_name,
                "expires_in_hours": share_data.expires_in_hours,
            },
            request=request,
        )

    return share


def get_share_by_token(
    db: Session, token: str, pin: Optional[str] = None
) -> Optional[MedicalRecordShare]:
    """Get share by token and validate PIN if required."""
    share = db.query(MedicalRecordShare).filter(MedicalRecordShare.share_token == token).first()

    if not share:
        return None

    # Check if PIN is required and matches
    if share.access_pin and share.access_pin != pin:
        return None

    return share


def validate_and_access_share(
    db: Session,
    token: str,
    pin: Optional[str],
    ip_address: str,
    request: Optional[Request] = None,
) -> MedicalRecordShare:
    """
    Validate share and record access.
    Raises HTTPException if invalid.
    """
    share = get_share_by_token(db, token, pin)

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or invalid PIN",
        )

    if not share.is_valid():
        # Update status if expired
        if share.expires_at < datetime.now(timezone.utc) and share.status == ShareStatus.ACTIVE:
            setattr(share, "status", ShareStatus.EXPIRED)
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Share is {share.status.value}",
        )

    # Record access
    current_count: int = int(share.access_count)
    setattr(share, "access_count", current_count + 1)
    setattr(share, "last_accessed_at", datetime.now(timezone.utc))
    setattr(share, "last_accessed_ip", ip_address)

    # Mark as used if max access reached
    if share.max_access_count and share.access_count >= share.max_access_count:
        setattr(share, "status", ShareStatus.USED)

    db.commit()
    db.refresh(share)

    # Audit log
    if request:
        log_audit_event(
            db=db,
            user_id=int(share.shared_by_user_id),
            action="READ",
            resource_type="medical_record_share",
            resource_id=int(share.id) if share.id else None,
            details={
                "patient_id": share.patient_id,
                "access_count": share.access_count,
                "ip_address": ip_address,
            },
            request=request,
        )

    return share


def get_shared_medical_record(db: Session, share: MedicalRecordShare) -> SharedMedicalRecord:
    """
    Get medical record data based on share scope.
    """
    patient = share.patient

    # Base patient info (limited for privacy)
    patient_data = {
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "date_of_birth": patient.date_of_birth.isoformat(),
        "gender": patient.gender.value,
        "blood_type": patient.blood_type,
        "allergies": patient.allergies,
    }

    record = SharedMedicalRecord(
        patient=patient_data, scope=share.scope, accessed_at=datetime.now(timezone.utc)
    )

    # Add data based on scope
    if share.scope == ShareScope.FULL_RECORD:
        # Include everything
        record.appointments = [
            {
                "id": appt.id,
                "date": appt.appointment_date.isoformat(),
                "reason": appt.reason,
                "status": appt.status,
                "notes": appt.notes,
            }
            for appt in patient.appointments
        ]

        record.prescriptions = [
            {
                "id": presc.id,
                "medication": presc.medication_name,
                "dosage": presc.dosage,
                "start_date": presc.start_date.isoformat(),
                "end_date": presc.end_date.isoformat() if presc.end_date else None,
                "instructions": presc.instructions,
            }
            for presc in patient.prescriptions
        ]

        record.documents = [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "type": doc.document_type.value,
                "date": doc.created_at.isoformat(),
            }
            for doc in patient.documents
            if not doc.deleted_at
        ]

        record.medical_history = patient.medical_history
        record.allergies = patient.allergies
        record.blood_type = patient.blood_type

    elif share.scope == ShareScope.APPOINTMENTS_ONLY:
        record.appointments = [
            {
                "id": appt.id,
                "date": appt.appointment_date.isoformat(),
                "reason": appt.reason,
                "status": appt.status,
            }
            for appt in patient.appointments
        ]

    elif share.scope == ShareScope.PRESCRIPTIONS_ONLY:
        record.prescriptions = [
            {
                "id": presc.id,
                "medication": presc.medication_name,
                "dosage": presc.dosage,
                "start_date": presc.start_date.isoformat(),
            }
            for presc in patient.prescriptions
        ]

    elif share.scope == ShareScope.DOCUMENTS_ONLY:
        record.documents = [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "type": doc.document_type.value,
                "date": doc.created_at.isoformat(),
            }
            for doc in patient.documents
            if not doc.deleted_at
        ]

    return record


def get_user_shares(
    db: Session,
    user_id: int,
    tenant_id: str,
    patient_id: Optional[int] = None,
    active_only: bool = False,
) -> List[MedicalRecordShare]:
    """Get all shares created by user."""
    query = db.query(MedicalRecordShare).filter(
        MedicalRecordShare.shared_by_user_id == user_id,
        MedicalRecordShare.tenant_id == tenant_id,
    )

    if patient_id:
        query = query.filter(MedicalRecordShare.patient_id == patient_id)

    if active_only:
        query = query.filter(MedicalRecordShare.status == ShareStatus.ACTIVE)

    return query.order_by(MedicalRecordShare.created_at.desc()).all()


def revoke_share(
    db: Session,
    share_id: int,
    user_id: int,
    tenant_id: str,
    request: Optional[Request] = None,
) -> bool:
    """Revoke a share."""
    share = (
        db.query(MedicalRecordShare)
        .filter(
            MedicalRecordShare.id == share_id,
            MedicalRecordShare.tenant_id == tenant_id,
            MedicalRecordShare.shared_by_user_id == user_id,
        )
        .first()
    )

    if not share:
        return False

    setattr(share, "status", ShareStatus.REVOKED)
    setattr(share, "revoked_at", datetime.now(timezone.utc))
    setattr(share, "revoked_by_user_id", user_id)
    db.commit()

    # Audit log
    if request:
        log_audit_event(
            db=db,
            user_id=user_id,
            action="DELETE",
            resource_type="medical_record_share",
            resource_id=int(share.id) if share.id else None,
            details={"patient_id": share.patient_id, "revoked": True},
            request=request,
        )

    return True
