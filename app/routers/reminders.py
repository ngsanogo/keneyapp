"""
Appointment reminder router for managing automated notifications.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.models.user import User, UserRole
from app.schemas.reminder import (
    ReminderBulkCreate,
    ReminderResponse,
    ReminderStats,
)
from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post(
    "/bulk",
    response_model=List[ReminderResponse],
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def create_bulk_reminders(
    reminder_data: ReminderBulkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST])
    ),
):
    """
    Create multiple reminders for an appointment.

    Creates reminders at specified intervals before the appointment
    across multiple delivery channels.

    Args:
        reminder_data: Reminder configuration
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user

    Returns:
        List of created reminders
    """
    try:
        reminder_service = ReminderService(db)
        reminders = reminder_service.create_reminders_for_appointment(
            appointment_id=reminder_data.appointment_id,
            tenant_id=current_user.tenant_id,
            channels=reminder_data.channels,
            hours_before=reminder_data.hours_before,
        )

        log_audit_event(
            db=db,
            request=request,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            action="CREATE",
            resource_type="appointment_reminder",
            resource_id=reminder_data.appointment_id,
            details={
                "count": len(reminders),
                "channels": [c.value for c in reminder_data.channels],
                "hours_before": reminder_data.hours_before,
            },
        )

        return [ReminderResponse.model_validate(r) for r in reminders]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create reminders",
        )


@router.get(
    "/appointment/{appointment_id}",
    response_model=List[ReminderResponse],
)
@limiter.limit("100/minute")
def get_appointment_reminders(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST])
    ),
):
    """
    Get all reminders for a specific appointment.

    Args:
        appointment_id: ID of the appointment
        request: Incoming request
        db: Database session
        current_user: Authenticated user

    Returns:
        List of reminders
    """
    reminder_service = ReminderService(db)
    reminders = reminder_service.get_reminders_for_appointment(
        appointment_id=appointment_id,
        tenant_id=current_user.tenant_id,
    )

    return [ReminderResponse.model_validate(r) for r in reminders]


@router.post(
    "/process",
    response_model=ReminderStats,
)
@limiter.limit("5/minute")
def process_due_reminders(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """
    Process all due reminders (Admin only).

    This endpoint is typically called by a scheduled task,
    but can be manually triggered by administrators.

    Args:
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated admin user

    Returns:
        Statistics about processed reminders
    """
    reminder_service = ReminderService(db)
    results = reminder_service.process_due_reminders(tenant_id=current_user.tenant_id)

    log_audit_event(
        db=db,
        request=request,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="PROCESS",
        resource_type="appointment_reminder",
        resource_id=None,
        details=results,
    )

    return ReminderStats(**results, pending=0, cancelled=0)


@router.delete(
    "/appointment/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("10/minute")
def cancel_appointment_reminders(
    appointment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST])
    ),
):
    """
    Cancel all pending reminders for an appointment.

    Args:
        appointment_id: ID of the appointment
        request: Incoming request for auditing
        db: Database session
        current_user: Authenticated user

    Returns:
        204 No Content
    """
    reminder_service = ReminderService(db)
    count = reminder_service.cancel_reminders_for_appointment(
        appointment_id=appointment_id,
        tenant_id=current_user.tenant_id,
    )

    log_audit_event(
        db=db,
        request=request,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        action="DELETE",
        resource_type="appointment_reminder",
        resource_id=appointment_id,
        details={"cancelled_count": count},
    )

    return None
