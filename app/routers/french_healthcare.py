"""
French Healthcare Router
Endpoints for INS verification, Pro Santé Connect, DMP, and MSSanté integration
"""
import secrets
from typing import Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.cache import cache_clear_pattern, cache_get, cache_set
from app.core.dependencies import get_current_active_user, get_db, require_roles
from app.core.metrics import patient_operations_total
from app.core.rate_limit import limiter
from app.models.french_healthcare import INSStatus
from app.models.user import User, UserRole
from app.services.ins_service import INSService
from app.services.pro_sante_connect import ProSanteConnectService

router = APIRouter(prefix="/french-healthcare", tags=["French Healthcare"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class INSVerificationRequest(BaseModel):
    """Request to verify patient INS"""
    patient_id: UUID
    ins_number: str = Field(..., description="13-digit INS number")
    birth_name: str = Field(..., description="Nom de naissance")
    first_names: str = Field(..., description="Prénoms (ordre état civil)")
    birth_date: str = Field(..., description="Date de naissance (YYYY-MM-DD)")
    birth_location: Optional[str] = Field(None, description="Lieu de naissance")


class INSVerificationResponse(BaseModel):
    """INS verification result"""
    success: bool
    status: str
    ins_number: str
    verified_at: Optional[str]
    expires_at: Optional[str]
    message: str
    identity_traits: Optional[Dict] = None


class PSCAuthorizationResponse(BaseModel):
    """Pro Santé Connect authorization URL"""
    authorization_url: str
    state: str


class PSCCallbackRequest(BaseModel):
    """Pro Santé Connect callback data"""
    code: str
    state: str


class PSCAuthenticationResponse(BaseModel):
    """PSC authentication result"""
    access_token: str
    token_type: str = "bearer"
    user: Dict
    cps_details: Dict


# ============================================================================
# INS Endpoints
# ============================================================================

@router.post(
    "/ins/verify",
    response_model=INSVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify patient INS",
    description="Verify patient INS (Identifiant National de Santé) with ANS Teleservice"
)
@limiter.limit("10/minute")
async def verify_patient_ins(
    request: Request,
    data: INSVerificationRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])),
    db: Session = Depends(get_db)
):
    """
    Verify patient INS with ANS Teleservice.
    
    **Authorization**: Admin, Doctor, Nurse
    **Rate Limit**: 10 requests per minute
    """
    from datetime import datetime
    
    ins_service = INSService(db)
    
    # Parse birth date
    try:
        birth_date = datetime.strptime(data.birth_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid birth date format. Use YYYY-MM-DD"
        )
    
    # Verify and store INS
    try:
        ins_record, verification_success = await ins_service.verify_and_store_ins(
            patient_id=data.patient_id,
            ins_number=data.ins_number,
            birth_name=data.birth_name,
            first_names=data.first_names,
            birth_date=birth_date,
            tenant_id=current_user.tenant_id,
            operator_id=current_user.id,
            birth_location=data.birth_location,
            request=request
        )
        
        # Clear patient cache
        cache_clear_pattern(f"patients:detail:{current_user.tenant_id}:{data.patient_id}")
        cache_clear_pattern(f"patients:list:{current_user.tenant_id}:*")
        
        # Metrics
        patient_operations_total.labels(
            action="ins_verification",
            tenant_id=str(current_user.tenant_id)
        ).inc()
        
        message = "INS verified successfully" if verification_success else "INS verification pending or failed"
        
        return INSVerificationResponse(
            success=verification_success,
            status=ins_record.status.value,
            ins_number=ins_record.ins_number,
            verified_at=ins_record.verified_at.isoformat() if ins_record.verified_at else None,
            expires_at=ins_record.expires_at.isoformat() if ins_record.expires_at else None,
            message=message,
            identity_traits={
                "birth_name": ins_record.birth_name,
                "first_names": ins_record.first_names,
                "birth_date": ins_record.birth_date.isoformat() if ins_record.birth_date else None,
                "birth_location": ins_record.birth_location,
                "gender_code": ins_record.gender_code
            } if ins_record.birth_name else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"INS verification error: {str(e)}"
        )


@router.get(
    "/ins/patient/{patient_id}",
    response_model=INSVerificationResponse,
    summary="Get patient INS record",
    description="Retrieve patient's INS verification record"
)
@limiter.limit("30/minute")
async def get_patient_ins_record(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST])),
    db: Session = Depends(get_db)
):
    """
    Get patient's INS record.
    
    **Authorization**: All authenticated users
    **Rate Limit**: 30 requests per minute
    """
    ins_service = INSService(db)
    ins_record = ins_service.get_patient_ins(patient_id)
    
    if not ins_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No INS record found for this patient"
        )
    
    # Audit log
    log_audit_event(
        db=db,
        request=request,
        action="read_ins",
        resource_type="patient_ins",
        resource_id=str(ins_record.id),
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        details={"patient_id": str(patient_id)}
    )
    
    return INSVerificationResponse(
        success=ins_record.is_valid,
        status=ins_record.status.value,
        ins_number=ins_record.ins_number,
        verified_at=ins_record.verified_at.isoformat() if ins_record.verified_at else None,
        expires_at=ins_record.expires_at.isoformat() if ins_record.expires_at else None,
        message=f"INS status: {ins_record.status.value}",
        identity_traits={
            "birth_name": ins_record.birth_name,
            "first_names": ins_record.first_names,
            "birth_date": ins_record.birth_date.isoformat() if ins_record.birth_date else None,
            "birth_location": ins_record.birth_location,
            "gender_code": ins_record.gender_code
        } if ins_record.birth_name else None
    )


# ============================================================================
# Pro Santé Connect Endpoints
# ============================================================================

@router.get(
    "/psc/authorize",
    response_model=PSCAuthorizationResponse,
    summary="Get Pro Santé Connect authorization URL",
    description="Generate authorization URL for PSC OAuth2 flow"
)
@limiter.limit("10/minute")
async def get_psc_authorization_url(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generate Pro Santé Connect authorization URL.
    
    **Rate Limit**: 10 requests per minute
    **Note**: This endpoint is public (no authentication required for login initiation)
    """
    psc_service = ProSanteConnectService(db)
    
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in cache (5 minutes)
    cache_set(f"psc:state:{state}", "valid", ttl=300)
    
    try:
        authorization_url = psc_service.get_authorization_url(state)
        return PSCAuthorizationResponse(
            authorization_url=authorization_url,
            state=state
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PSC authorization URL: {str(e)}"
        )


@router.post(
    "/psc/callback",
    response_model=PSCAuthenticationResponse,
    summary="Pro Santé Connect callback",
    description="Handle PSC OAuth2 callback and authenticate user"
)
@limiter.limit("10/minute")
async def psc_callback(
    request: Request,
    data: PSCCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Handle Pro Santé Connect OAuth2 callback.
    
    **Rate Limit**: 10 requests per minute
    **Note**: This endpoint is public (completes authentication flow)
    """
    # Verify state (CSRF protection)
    stored_state = cache_get(f"psc:state:{data.state}")
    if not stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter"
        )
    
    # Default tenant (in production, extract from state or session)
    from app.models.tenant import Tenant
    default_tenant = db.query(Tenant).filter(Tenant.slug == "default").first()
    if not default_tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default tenant not found"
        )
    
    psc_service = ProSanteConnectService(db)
    
    try:
        user, cps_record, access_token = await psc_service.authenticate_with_psc(
            code=data.code,
            tenant_id=default_tenant.id
        )
        
        # Audit log
        log_audit_event(
            db=db,
            request=request,
            action="psc_login",
            resource_type="user",
            resource_id=str(user.id),
            user_id=user.id,
            tenant_id=user.tenant_id,
            details={
                "rpps": cps_record.rpps_number,
                "cps_type": cps_record.cps_type.value
            }
        )
        
        return PSCAuthenticationResponse(
            access_token=access_token,
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value
            },
            cps_details={
                "cps_number": cps_record.cps_number,
                "rpps_number": cps_record.rpps_number,
                "profession_category": cps_record.profession_category,
                "specialty_label": cps_record.specialty_label,
                "cps_type": cps_record.cps_type.value
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PSC authentication failed: {str(e)}"
        )


@router.get(
    "/psc/me",
    summary="Get my CPS details",
    description="Retrieve current user's CPS/RPPS information"
)
@limiter.limit("30/minute")
async def get_my_cps_details(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get authenticated user's CPS details.
    
    **Authorization**: Authenticated user
    **Rate Limit**: 30 requests per minute
    """
    psc_service = ProSanteConnectService(db)
    cps_record = psc_service.get_cps_by_user_id(current_user.id)
    
    if not cps_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No CPS record found for this user"
        )
    
    return {
        "cps_number": cps_record.cps_number,
        "rpps_number": cps_record.rpps_number,
        "adeli_number": cps_record.adeli_number,
        "cps_type": cps_record.cps_type.value,
        "profession_code": cps_record.profession_code,
        "profession_category": cps_record.profession_category,
        "specialty_code": cps_record.specialty_code,
        "specialty_label": cps_record.specialty_label,
        "practice_structure_name": cps_record.practice_structure_name,
        "is_valid": cps_record.is_valid,
        "expiry_date": cps_record.expiry_date.isoformat() if cps_record.expiry_date else None,
        "psc_last_login": cps_record.psc_last_login.isoformat() if cps_record.psc_last_login else None
    }


# ============================================================================
# DMP Endpoints (Placeholder - requires DMP API implementation)
# ============================================================================

@router.get(
    "/dmp/status",
    summary="DMP integration status",
    description="Get DMP (Dossier Médical Partagé) integration status (Coming soon)"
)
async def dmp_status():
    """
    DMP integration status endpoint.
    
    **Status**: Coming soon
    **Requires**: DMP API credentials and ANS certification
    """
    return {
        "status": "not_configured",
        "message": "DMP integration coming soon. Requires ANS certification and DMP API credentials.",
        "documentation": "https://esante.gouv.fr/produits-services/dmp"
    }


# ============================================================================
# MSSanté Endpoints (Placeholder - requires MSSanté setup)
# ============================================================================

@router.get(
    "/mssante/status",
    summary="MSSanté integration status",
    description="Get MSSanté (Messagerie Sécurisée de Santé) integration status (Coming soon)"
)
async def mssante_status():
    """
    MSSanté integration status endpoint.
    
    **Status**: Coming soon
    **Requires**: MSSanté account and SMTP gateway configuration
    """
    return {
        "status": "not_configured",
        "message": "MSSanté integration coming soon. Requires certified MSSanté account.",
        "documentation": "https://esante.gouv.fr/produits-services/mssante"
    }
