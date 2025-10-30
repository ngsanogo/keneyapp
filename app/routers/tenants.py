"""
Tenant management router for multi-tenant administration.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.models.tenant import Tenant, TenantModule
from app.models.user import User, UserRole
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantModuleResponse,
    TenantModuleUpsert,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _require_super_admin(
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN)),
) -> User:
    """Ensure the current user is a platform super administrator."""
    return current_user


def _get_tenant_or_404(db: Session, tenant_id: int) -> Tenant:
    """Fetch tenant or raise 404."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
    return tenant


@router.get("/", response_model=List[TenantResponse])
@limiter.limit("30/minute")
def list_tenants(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(_require_super_admin),
):
    """List all registered tenants."""

    return db.query(Tenant).order_by(Tenant.id).all()


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_tenant(
    payload: TenantCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin),
):
    """Create a new tenant."""

    if db.query(Tenant).filter(Tenant.slug == payload.slug).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already in use"
        )

    if db.query(Tenant).filter(Tenant.name == payload.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Name already in use"
        )

    tenant = Tenant(
        name=payload.name,
        slug=payload.slug,
        contact_email=payload.contact_email,
        region=payload.region,
        default_timezone=payload.default_timezone or "UTC",
        is_active=payload.is_active,
        configuration=payload.configuration,
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    log_audit_event(
        db=db,
        action="CREATE",
        resource_type="tenant",
        resource_id=tenant.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "slug": tenant.slug,
            "region": tenant.region,
            "is_active": tenant.is_active,
        },
        request=request,
    )

    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
@limiter.limit("60/minute")
def get_tenant(
    tenant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(_require_super_admin),
):
    """Retrieve a tenant by identifier."""

    return _get_tenant_or_404(db, tenant_id)


@router.patch("/{tenant_id}", response_model=TenantResponse)
@limiter.limit("15/minute")
def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin),
):
    """Update tenant metadata or activation state."""

    tenant = _get_tenant_or_404(db, tenant_id)

    if payload.name and payload.name != tenant.name:
        if db.query(Tenant).filter(Tenant.name == payload.name).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Name already in use"
            )
        tenant.name = payload.name

    if payload.contact_email is not None:
        tenant.contact_email = payload.contact_email

    if payload.region is not None:
        tenant.region = payload.region

    if payload.default_timezone is not None:
        tenant.default_timezone = payload.default_timezone

    if payload.is_active is not None:
        tenant.is_active = payload.is_active

    if payload.configuration is not None:
        tenant.configuration = payload.configuration

    db.commit()
    db.refresh(tenant)

    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="tenant",
        resource_id=tenant.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"updated_fields": list(payload.model_dump(exclude_unset=True).keys())},
        request=request,
    )

    return tenant


@router.get(
    "/{tenant_id}/modules",
    response_model=List[TenantModuleResponse],
)
@limiter.limit("60/minute")
def list_tenant_modules(
    tenant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(_require_super_admin),
):
    """List module configurations for a tenant."""

    tenant = _get_tenant_or_404(db, tenant_id)
    return (
        db.query(TenantModule)
        .filter(TenantModule.tenant_id == tenant.id)
        .order_by(TenantModule.module_key)
        .all()
    )


@router.put(
    "/{tenant_id}/modules/{module_key}",
    response_model=TenantModuleResponse,
)
@limiter.limit("30/minute")
def upsert_tenant_module(
    tenant_id: int,
    module_key: str,
    payload: TenantModuleUpsert,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin),
):
    """Create or update a tenant module configuration."""

    tenant = _get_tenant_or_404(db, tenant_id)

    module = (
        db.query(TenantModule)
        .filter(
            TenantModule.tenant_id == tenant.id,
            TenantModule.module_key == module_key,
        )
        .first()
    )

    created = False
    if not module:
        module = TenantModule(
            tenant_id=tenant.id,
            module_key=module_key,
            is_enabled=payload.is_enabled if payload.is_enabled is not None else True,
            configuration=payload.configuration or {},
        )
        db.add(module)
        created = True
    else:
        if payload.is_enabled is not None:
            module.is_enabled = payload.is_enabled
        if payload.configuration is not None:
            module.configuration = payload.configuration

    db.commit()
    db.refresh(module)

    log_audit_event(
        db=db,
        action="CREATE" if created else "UPDATE",
        resource_type="tenant_module",
        resource_id=module.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={
            "tenant_id": tenant.id,
            "module_key": module_key,
            "is_enabled": module.is_enabled,
            "created": created,
        },
        request=request,
    )

    return module


@router.delete(
    "/{tenant_id}/modules/{module_key}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@limiter.limit("20/minute")
def delete_tenant_module(
    tenant_id: int,
    module_key: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_super_admin),
):
    """Remove a tenant module configuration."""

    tenant = _get_tenant_or_404(db, tenant_id)
    module = (
        db.query(TenantModule)
        .filter(
            TenantModule.tenant_id == tenant.id,
            TenantModule.module_key == module_key,
        )
        .first()
    )

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module configuration not found",
        )

    db.delete(module)
    db.commit()

    log_audit_event(
        db=db,
        action="DELETE",
        resource_type="tenant_module",
        resource_id=module.id,
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        details={"tenant_id": tenant.id, "module_key": module_key},
        request=request,
    )

    return None
