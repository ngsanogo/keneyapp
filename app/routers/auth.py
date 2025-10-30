"""Authentication router for user login and registration."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.rate_limit import limiter
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.core.config import settings
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.user import (
    ChangePasswordRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    UserCreate,
    UserResponse,
    Token,
)
from app.services.mfa import (
    generate_mfa_secret,
    generate_provisioning_uri,
    verify_totp,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        request: Incoming request for audit context
        db: Database session

    Returns:
        Created user information
    """
    # Check if user already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    tenant = db.query(Tenant).filter(Tenant.id == user_data.tenant_id).first()
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or inactive tenant",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    now = datetime.now(timezone.utc)
    db_user = User(
        tenant_id=tenant.id,
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        role=user_data.role,
        hashed_password=hashed_password,
        password_changed_at=now,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    log_audit_event(
        db=db,
        action="CREATE",
        resource_type="user",
        resource_id=db_user.id,
        status="success",
        username=db_user.username,
        user_id=db_user.id,
        details={"role": db_user.role.value, "tenant_id": tenant.id},
        request=request,
    )

    return db_user


@router.post("/login", response_model=Token)
@limiter.limit("15/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    otp: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Login user and return JWT access token.

    Args:
        request: Incoming request for audit context
        form_data: OAuth2 login form with username and password
        db: Database session

    Returns:
        JWT access token
    """
    # Authenticate user
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    if not user.tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is inactive",
        )

    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account locked due to failed login attempts",
        )

    if not verify_password(form_data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            user.is_locked = True
        db.commit()

        log_audit_event(
            db=db,
            action="LOGIN",
            resource_type="user",
            resource_id=user.id,
            status="failure",
            username=user.username,
            user_id=user.id,
            details={
                "reason": "invalid_credentials",
                "attempts": user.failed_login_attempts,
            },
            request=request,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.mfa_enabled and not verify_totp(user.mfa_secret, otp):
        log_audit_event(
            db=db,
            action="LOGIN",
            resource_type="user",
            resource_id=user.id,
            status="failure",
            username=user.username,
            user_id=user.id,
            details={"reason": "invalid_mfa"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid multi-factor authentication code",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user.failed_login_attempts = 0
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
        },
        expires_delta=access_token_expires,
    )

    log_audit_event(
        db=db,
        action="LOGIN",
        resource_type="user",
        resource_id=user.id,
        status="success",
        username=user.username,
        user_id=user.id,
        request=request,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
@limiter.limit("30/minute")
def read_current_user(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve details for the current authenticated user.

    Args:
        current_user: Dependency providing the active user.

    Returns:
        User information suitable for frontend consumption.
    """
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Allow the current user to change their password."""

    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid current password")

    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)
    db.commit()

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="user",
        resource_id=current_user.id,
        status="success",
        username=current_user.username,
        user_id=current_user.id,
        details={"operation": "change_password"},
        request=request,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/mfa/setup", response_model=MFASetupResponse)
@limiter.limit("10/minute")
def setup_mfa(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate and persist a new MFA secret for the user."""

    secret = generate_mfa_secret()
    current_user.mfa_secret = secret
    current_user.mfa_enabled = False
    db.commit()

    return MFASetupResponse(
        secret=secret,
        provisioning_uri=generate_provisioning_uri(secret, current_user.username),
    )


@router.post("/mfa/activate", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def activate_mfa(
    payload: MFAVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Activate MFA for the user after validating the provided code."""

    if not current_user.mfa_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA has not been initiated")

    if not verify_totp(current_user.mfa_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    current_user.mfa_enabled = True
    db.commit()

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="user",
        resource_id=current_user.id,
        status="success",
        username=current_user.username,
        user_id=current_user.id,
        details={"operation": "mfa_enable"},
        request=request,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def disable_mfa(
    payload: MFAVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Disable MFA for the user (requires a valid code)."""

    if not current_user.mfa_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")

    if not verify_totp(current_user.mfa_secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="user",
        resource_id=current_user.id,
        status="success",
        username=current_user.username,
        user_id=current_user.id,
        details={"operation": "mfa_disable"},
        request=request,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
