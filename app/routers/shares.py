"""
API routes for medical record sharing with temporary secure links.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.medical_record_share import (
    ShareAccessRequest,
    ShareCreate,
    SharedMedicalRecord,
    ShareResponse,
    ShareSummary,
)
from app.services import share_service

router = APIRouter(prefix="/shares", tags=["shares"])


@router.post("/", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
async def create_medical_record_share(
    request: Request,
    share: ShareCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a temporary secure share link for medical records.

    **Access:** All authenticated users (for their own patients)

    **Rate limit:** 10 shares per hour

    **Features:**
    - Temporary access (1 hour to 30 days)
    - Optional PIN protection
    - Limited access count
    - Email restriction
    - Customizable data scope

    **Scopes:**
    - `full_record`: Complete medical history
    - `appointments_only`: Only appointments
    - `prescriptions_only`: Only prescriptions
    - `documents_only`: Only documents
    - `custom`: Custom selection

    **Security:**
    - Secure random tokens
    - Patient consent required
    - All accesses are audit logged
    - Automatic expiration

    **Returns:** Share details including access token and PIN (if enabled)
    """
    share_record = share_service.create_share(
        db=db,
        share_data=share,
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        request=request,
    )

    return share_record


@router.get("/", response_model=List[ShareSummary])
@limiter.limit("60/minute")
async def get_my_shares(
    request: Request,
    patient_id: Optional[int] = None,
    active_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get all shares created by current user.

    **Access:** All authenticated users

    **Rate limit:** 60 requests per minute

    **Query Parameters:**
    - `patient_id`: Filter by patient
    - `active_only`: Only show active shares
    """
    shares = share_service.get_user_shares(
        db=db,
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        patient_id=patient_id,
        active_only=active_only,
    )

    return shares


@router.post("/access", response_model=SharedMedicalRecord)
@limiter.limit("20/hour")
async def access_shared_record(
    request: Request, access_request: ShareAccessRequest, db: Session = Depends(get_db)
):
    """
    Access a shared medical record using token and optional PIN.

    **Public endpoint** - No authentication required

    **Rate limit:** 20 accesses per hour per IP

    **Security:**
    - Token and PIN validation
    - Expiration check
    - Access count limits
    - IP logging for audit

    **Returns:** Medical record data based on share scope

    **Errors:**
    - 404: Share not found or invalid PIN
    - 403: Share expired, revoked, or max accesses reached
    """
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Validate and record access
    share = share_service.validate_and_access_share(
        db=db,
        token=access_request.token,
        pin=access_request.pin,
        ip_address=client_ip,
        request=request,
    )

    # Get medical record data
    record = share_service.get_shared_medical_record(db, share)

    return record


@router.get("/{share_id}", response_model=ShareResponse)
@limiter.limit("60/minute")
async def get_share_details(
    request: Request,
    share_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get details of a specific share.

    **Access:** Share creator only

    **Rate limit:** 60 requests per minute
    """
    share = (
        db.query(share_service.MedicalRecordShare)
        .filter(
            share_service.MedicalRecordShare.id == share_id,
            share_service.MedicalRecordShare.shared_by_user_id == current_user.id,
            share_service.MedicalRecordShare.tenant_id == str(current_user.tenant_id),
        )
        .first()
    )

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or access denied",
        )

    # Don't expose PIN in GET requests
    share.access_pin = None

    return share


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def revoke_share(
    request: Request,
    share_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Revoke a share link.

    **Access:** Share creator only

    **Rate limit:** 30 requests per minute

    **Note:** Revoked shares cannot be reactivated. Create a new share if needed.
    """
    success = share_service.revoke_share(
        db=db,
        share_id=share_id,
        user_id=current_user.id,
        tenant_id=str(current_user.tenant_id),
        request=request,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or access denied",
        )

    return None
