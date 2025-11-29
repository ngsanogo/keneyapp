"""Administrative user management endpoints."""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import (
    UserPasswordReset,
    UserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
@limiter.limit("60/minute")
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
) -> List[User]:
    """Return the full user directory (admin only)."""

    query = db.query(User)
    if current_admin.role != UserRole.SUPER_ADMIN:
        query = query.filter(User.tenant_id == current_admin.tenant_id)
    return query.order_by(User.id).all()


@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit("60/minute")
def get_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
) -> User:
    """Retrieve a single user."""

    query = db.query(User).filter(User.id == user_id)
    if current_admin.role != UserRole.SUPER_ADMIN:
        query = query.filter(User.tenant_id == current_admin.tenant_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/status", response_model=UserResponse)
@limiter.limit("30/minute")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
) -> User:
    """Update activation or lock status for a user."""

    query = db.query(User).filter(User.id == user_id)
    if current_admin.role != UserRole.SUPER_ADMIN:
        query = query.filter(User.tenant_id == current_admin.tenant_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.is_active is not None:
        user.is_active = payload.is_active  # type: ignore[assignment]

    if payload.is_locked is not None:
        user.is_locked = payload.is_locked  # type: ignore[assignment]
        if not payload.is_locked:
            user.failed_login_attempts = 0  # type: ignore[assignment]

    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="user",
        resource_id=int(user.id),  # type: ignore[arg-type]
        status="success",
        user_id=int(current_admin.id),  # type: ignore[arg-type]
        username=str(current_admin.username),  # type: ignore[arg-type]
        details={"operation": "status_update", "target": user.username},
        request=request,
    )

    return user


@router.patch("/{user_id}/role", response_model=UserResponse)
@limiter.limit("30/minute")
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """Assign a new role to a user."""

    query = db.query(User).filter(User.id == user_id)
    if current_admin.role != UserRole.SUPER_ADMIN:
        query = query.filter(User.tenant_id == current_admin.tenant_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = payload.role
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="user",
        resource_id=user.id,
        status="success",
        user_id=current_admin.id,
        username=current_admin.username,
        details={"operation": "role_update", "role": payload.role.value},
        request=request,
    )

    return user


@router.post("/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def reset_user_password(
    user_id: int,
    payload: UserPasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """Reset a user's password and require re-login."""

    query = db.query(User).filter(User.id == user_id)
    if current_admin.role != UserRole.SUPER_ADMIN:
        query = query.filter(User.tenant_id == current_admin.tenant_id)
    user = query.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = get_password_hash(payload.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    user.is_locked = False
    db.commit()

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="user",
        resource_id=user.id,
        status="success",
        user_id=current_admin.id,
        username=current_admin.username,
        details={"operation": "reset_password", "target": user.username},
        request=request,
    )

    return None
