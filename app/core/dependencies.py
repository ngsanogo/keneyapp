"""
Shared FastAPI dependency utilities.

Provides helpers for authentication, authorization,
and role-based access control across the API.
"""

from collections.abc import Iterable as IterableABC
from typing import Callable, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token, oauth2_scheme
from app.models.user import User, UserRole


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Retrieve the currently authenticated user from the JWT access token.

    Args:
        token: Bearer token supplied via Authorization header.
        db: Database session dependency.

    Returns:
        Authenticated `User` instance.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload:
        raise unauthorized

    username: Optional[str] = payload.get("sub")
    if not username:
        raise unauthorized

    tenant_id = payload.get("tenant_id")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise unauthorized

    if tenant_id is not None and user.tenant_id != tenant_id:
        raise unauthorized

    if not user.tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is inactive",
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensure the current user account is active.

    Args:
        current_user: Authenticated user dependency.

    Returns:
        Active `User` instance.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return current_user


def require_roles(*roles: Union[UserRole, IterableABC[UserRole]]) -> Callable:
    """
    Factory returning a dependency that enforces role-based access control.

    Args:
        *allowed_roles: Collection of roles permitted to access the route.

    Returns:
        Dependency callable that yields the current user when authorized.
    """

    allowed: set[UserRole] = set()

    for entry in roles:
        if isinstance(entry, UserRole):
            allowed.add(entry)
        else:
            allowed.update(role for role in entry)

    def role_guard(
        request: Request,
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        """
        Verify the current user has one of the required roles.

        Args:
            request: Incoming FastAPI request (also used for audit logging).
            current_user: Active user resolved from the token.

        Returns:
            Authorized `User` instance.
        """
        if not allowed:
            return current_user

        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this operation",
            )

        return current_user

    return role_guard


__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_roles",
]
