"""
OAuth2/OIDC Authentication Router for KeneyApp.
Provides endpoints for third-party authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.oauth import get_oauth_authorization_url, handle_oauth_callback
from app.core.rate_limit import limiter
from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import Token

router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.get("/authorize/{provider}")
@limiter.limit("10/minute")
async def oauth_authorize(
    provider: str,
    request: Request,
    redirect_uri: Optional[str] = Query(None),
):
    """
    Initiate OAuth authorization flow.
    
    Args:
        provider: OAuth provider (google, microsoft, okta)
        request: Request context
        redirect_uri: Optional redirect URI
        
    Returns:
        Authorization URL and state
    """
    if provider not in ['google', 'microsoft', 'okta']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    result = await get_oauth_authorization_url(provider, redirect_uri)
    return result


@router.get("/callback/{provider}", response_model=Token)
@limiter.limit("10/minute")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Handle OAuth callback and authenticate user.
    
    Args:
        provider: OAuth provider
        code: Authorization code
        state: State for CSRF protection
        request: Request context
        db: Database session
        
    Returns:
        JWT access token
    """
    # Handle OAuth callback and get user info
    user_info = await handle_oauth_callback(provider, code, state)
    
    # Check if user exists
    email = user_info.get('email')
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by OAuth provider"
        )
    
    user = db.query(User).filter(User.email == email).first()
    
    # Create user if doesn't exist (auto-registration)
    if not user:
        # Generate username from email
        username = email.split('@')[0]
        
        # Ensure unique username
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create new user with OAuth
        user = User(
            email=email,
            username=username,
            full_name=user_info.get('name', email),
            role=UserRole.RECEPTIONIST,  # Default role for OAuth users
            hashed_password=get_password_hash('oauth-' + str(datetime.now(timezone.utc))),
            is_active=True,
            password_changed_at=datetime.now(timezone.utc),
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        log_audit_event(
            db=db,
            action="CREATE",
            resource_type="user",
            resource_id=user.id,
            status="success",
            username=user.username,
            user_id=user.id,
            details={
                "oauth_provider": provider,
                "registration_method": "oauth"
            },
            request=request,
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is locked"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
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
        details={
            "oauth_provider": provider,
            "authentication_method": "oauth"
        },
        request=request,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
