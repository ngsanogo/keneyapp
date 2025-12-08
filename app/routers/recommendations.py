"""
Recommendation API endpoints for intelligent healthcare suggestions
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.models.user import User, UserRole
from app.schemas.recommendation import (
    AppointmentSlotRecommendation,
    MedicationInteractionWarning,
    PatientCareRecommendation,
    ResourceOptimizationRecommendation,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/patient/{patient_id}/care", response_model=List[PatientCareRecommendation])
@limiter.limit("50/minute")
async def get_patient_care_recommendations(
    patient_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])),
):
    """
    Get AI-powered care recommendations for a specific patient.

    Analyzes patient history, appointments, prescriptions, and health data
    to provide actionable recommendations for improved care delivery.
    """
    service = RecommendationService(db)

    try:
        recommendations = service.get_patient_care_recommendations(
            patient_id=patient_id, tenant_id=current_user.tenant_id
        )

        log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="READ",
            resource_type="patient_recommendations",
            resource_id=patient_id,
            details={"recommendation_count": len(recommendations)},
            request=request,
        )

        return recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


@router.get(
    "/appointments/slots/{doctor_id}",
    response_model=List[AppointmentSlotRecommendation],
)
@limiter.limit("50/minute")
async def get_appointment_slot_recommendations(
    doctor_id: int,
    date: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST])
    ),
):
    """
    Get recommended appointment slots for a doctor on a specific date.

    Analyzes existing schedule, typical patterns, and optimal time distribution
    to recommend the best appointment slots.
    """
    try:
        target_date = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DD).",
        )

    service = RecommendationService(db)

    try:
        recommendations = service.get_appointment_slot_recommendations(
            doctor_id=doctor_id, date=target_date, tenant_id=current_user.tenant_id
        )

        log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="READ",
            resource_type="appointment_slot_recommendations",
            details={
                "doctor_id": doctor_id,
                "date": date,
                "slots_available": len(recommendations),
            },
            request=request,
        )

        return recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate slot recommendations: {str(e)}",
        )


@router.get(
    "/medications/interactions/{patient_id}",
    response_model=List[MedicationInteractionWarning],
)
@limiter.limit("50/minute")
async def check_medication_interactions(
    patient_id: int,
    new_medication: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE])),
):
    """
    Check for potential interactions between a new medication and patient's current prescriptions.

    Provides warnings about known drug interactions to prevent adverse events.
    """
    service = RecommendationService(db)

    try:
        warnings = service.get_medication_interaction_warnings(
            patient_id=patient_id,
            new_medication=new_medication,
            tenant_id=current_user.tenant_id,
        )

        log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="READ",
            resource_type="medication_interaction_check",
            resource_id=patient_id,
            details={
                "new_medication": new_medication,
                "warnings_count": len(warnings),
            },
            request=request,
        )

        return warnings

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check medication interactions: {str(e)}",
        )


@router.get(
    "/resources/optimization",
    response_model=List[ResourceOptimizationRecommendation],
)
@limiter.limit("20/minute")
async def get_resource_optimization_recommendations(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """
    Get recommendations for optimizing healthcare resource utilization.

    Analyzes workload distribution, appointment patterns, and resource usage
    to provide actionable optimization suggestions for administrators.
    """
    service = RecommendationService(db)

    try:
        recommendations = service.get_resource_optimization_recommendations(
            tenant_id=current_user.tenant_id
        )

        log_audit_event(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="READ",
            resource_type="resource_optimization_recommendations",
            details={"recommendation_count": len(recommendations)},
            request=request,
        )

        return recommendations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate optimization recommendations: {str(e)}",
        )
