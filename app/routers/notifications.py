"""
Notification management router for user notifications and preferences.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_roles
from app.core.rate_limit import limiter
from app.models.notification import NotificationChannel, NotificationType
from app.models.user import User, UserRole
from app.schemas.common import PaginatedResponse
from app.schemas.notification import (
    NotificationMarkRead,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    NotificationSendRequest,
    NotificationSendResponse,
    NotificationStats,
)
from app.services.notification_service import EnhancedNotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
@limiter.limit("100/minute")
def get_notifications(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    type: Optional[NotificationType] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get user notifications with pagination and filters.

    Args:
        page: Page number
        page_size: Items per page
        unread_only: Filter unread notifications only
        type: Filter by notification type
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of notifications
    """
    service = EnhancedNotificationService(db)

    skip = (page - 1) * page_size
    notifications, total = service.get_user_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        unread_only=unread_only,
        notification_type=type,
    )

    log_audit_event(
        db=db,
        action="READ",
        resource_type="notification",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"count": len(notifications), "unread_only": unread_only},
        request=request,
    )

    return PaginatedResponse.create(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=NotificationStats)
@limiter.limit("100/minute")
def get_notification_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get notification statistics for current user.

    Returns:
        Notification statistics including total, unread counts, and breakdowns
    """
    service = EnhancedNotificationService(db)
    stats = service.get_notification_stats(current_user.id)

    log_audit_event(
        db=db,
        action="READ",
        resource_type="notification",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"operation": "stats"},
        request=request,
    )

    return NotificationStats(**stats)


@router.post("/mark-read", status_code=status.HTTP_200_OK)
@limiter.limit("50/minute")
def mark_notifications_read(
    mark_read: NotificationMarkRead,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Mark notifications as read.

    Args:
        mark_read: Notification IDs to mark as read
        request: Incoming request
        db: Database session
        current_user: Authenticated user

    Returns:
        Success response with count of marked notifications
    """
    service = EnhancedNotificationService(db)

    count = service.mark_as_read(mark_read.notification_ids, current_user.id)
    db.commit()

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="notification",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"marked_read": count},
        request=request,
    )

    return {"success": True, "marked_read": count}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
@limiter.limit("100/minute")
def get_notification_preferences(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get user notification preferences.

    Returns:
        User's notification preferences
    """
    service = EnhancedNotificationService(db)
    prefs = service.get_user_preferences(current_user.id)

    if not prefs:
        # Create default preferences
        prefs = service.create_default_preferences(
            current_user.id, current_user.tenant_id
        )
        db.commit()

    log_audit_event(
        db=db,
        action="READ",
        resource_type="notification_preference",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        request=request,
    )

    return NotificationPreferenceResponse.model_validate(prefs)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
@limiter.limit("20/minute")
def update_notification_preferences(
    preferences: NotificationPreferenceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update user notification preferences.

    Args:
        preferences: Updated preference settings
        request: Incoming request
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated notification preferences
    """
    service = EnhancedNotificationService(db)

    try:
        prefs = service.update_preferences(current_user.id, preferences.model_dump())
        db.commit()
    except ValueError as e:
        # Create default preferences if they don't exist
        prefs = service.create_default_preferences(
            current_user.id, current_user.tenant_id
        )
        for key, value in preferences.model_dump().items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        db.commit()

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="notification_preference",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        request=request,
    )

    return NotificationPreferenceResponse.model_validate(prefs)


@router.post("/send", response_model=NotificationSendResponse)
@limiter.limit("10/minute")
def send_bulk_notifications(
    send_request: NotificationSendRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
):
    """
    Send notifications to multiple users (Admin/Doctor only).

    Args:
        send_request: Notification send request with user IDs, channels, and content
        request: Incoming request
        db: Database session
        current_user: Authenticated admin/doctor user

    Returns:
        Send result with success/failure counts
    """
    service = EnhancedNotificationService(db)

    total_requested = len(send_request.user_ids)
    notifications_created = 0
    notifications_sent = 0
    failures = 0
    errors = []

    # Get users in same tenant
    users = (
        db.query(User)
        .filter(
            User.id.in_(send_request.user_ids), User.tenant_id == current_user.tenant_id
        )
        .all()
    )

    if len(users) != total_requested:
        logger.warning(
            f"Some users not found or in different tenant. Requested: {total_requested}, Found: {len(users)}"
        )

    for user in users:
        try:
            results = service.send_notification(
                user=user,
                notification_type=send_request.type,
                channels=send_request.channels,
                title=send_request.title,
                message=send_request.message,
                action_url=send_request.action_url,
                resource_type=send_request.resource_type,
                resource_id=send_request.resource_id,
                respect_preferences=send_request.respect_preferences,
            )

            notifications_created += len(results)
            notifications_sent += sum(
                1 for n in results.values() if n.status.value in ["sent", "delivered"]
            )

        except Exception as e:
            logger.error(f"Failed to send notification to user {user.id}: {e}")
            failures += 1
            errors.append({"user_id": user.id, "error": str(e)})

    db.commit()

    log_audit_event(
        db=db,
        action="SEND_BULK",
        resource_type="notification",
        status="success" if failures == 0 else "partial",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "total_requested": total_requested,
            "notifications_created": notifications_created,
            "notifications_sent": notifications_sent,
            "failures": failures,
        },
        request=request,
    )

    return NotificationSendResponse(
        success=failures == 0,
        total_requested=total_requested,
        notifications_created=notifications_created,
        notifications_sent=notifications_sent,
        failures=failures,
        errors=errors,
    )
