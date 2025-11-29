"""Lab catalog endpoints (test types).

Follows KeneyApp conventions: RBAC, tenancy, rate limits, caching, audit.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.cache import cache_clear_pattern, cache_get, cache_set
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.models.lab import LabTestType
from app.models.user import User, UserRole
from app.schemas.lab import LabTestTypeCreate, LabTestTypeResponse, LabTestTypeUpdate

LIST_KEY = "labtests:list"
DETAIL_KEY = "labtests:detail"
LIST_TTL = 120
DETAIL_TTL = 300
DASHBOARD_PATTERN = "dashboard:*"

router = APIRouter(prefix="/lab-test-types", tags=["lab"])


@router.post(
    "/", response_model=LabTestTypeResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("10/minute")
def create_lab_test_type(
    payload: LabTestTypeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
):
    # Uniqueness per tenant
    exists = (
        db.query(LabTestType)
        .filter(
            LabTestType.tenant_id == current_user.tenant_id,
            LabTestType.code == payload.code,
        )
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Code already exists"
        )

    entity = LabTestType(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)

    log_audit_event(
        db,
        action="CREATE",
        resource_type="lab_test_type",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        resource_id=entity.id,
        details={"code": entity.code},
        request=request,
    )

    data = LabTestTypeResponse.model_validate(entity).model_dump(mode="json")
    cache_set(
        f"{DETAIL_KEY}:{current_user.tenant_id}:{entity.id}", data, expire=DETAIL_TTL
    )
    cache_clear_pattern(f"{LIST_KEY}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_PATTERN)
    return data


@router.get("/", response_model=List[LabTestTypeResponse])
@limiter.limit("60/minute")
def list_lab_test_types(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    key = f"{LIST_KEY}:{current_user.tenant_id}:{skip}:{limit}"
    cached = cache_get(key)
    if cached is not None:
        return cached

    items = (
        db.query(LabTestType)
        .filter(LabTestType.tenant_id == current_user.tenant_id)
        .offset(skip)
        .limit(min(100, max(1, limit)))
        .all()
    )
    data = [
        LabTestTypeResponse.model_validate(x).model_dump(mode="json") for x in items
    ]
    cache_set(key, data, expire=LIST_TTL)
    return data


@router.get("/{id}", response_model=LabTestTypeResponse)
@limiter.limit("120/minute")
def get_lab_test_type(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            [UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]
        )
    ),
):
    key = f"{DETAIL_KEY}:{current_user.tenant_id}:{id}"
    cached = cache_get(key)
    if cached is not None:
        return cached

    entity = (
        db.query(LabTestType)
        .filter(LabTestType.id == id, LabTestType.tenant_id == current_user.tenant_id)
        .first()
    )
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    data = LabTestTypeResponse.model_validate(entity).model_dump(mode="json")
    cache_set(key, data, expire=DETAIL_TTL)
    return data


@router.put("/{id}", response_model=LabTestTypeResponse)
@limiter.limit("10/minute")
def update_lab_test_type(
    id: int,
    payload: LabTestTypeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR])),
):
    entity = (
        db.query(LabTestType)
        .filter(LabTestType.id == id, LabTestType.tenant_id == current_user.tenant_id)
        .first()
    )
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(entity, k, v)
    db.commit()
    db.refresh(entity)

    log_audit_event(
        db,
        action="UPDATE",
        resource_type="lab_test_type",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        resource_id=entity.id,
        details={"code": entity.code},
        request=request,
    )

    data = LabTestTypeResponse.model_validate(entity).model_dump(mode="json")
    cache_set(
        f"{DETAIL_KEY}:{current_user.tenant_id}:{entity.id}", data, expire=DETAIL_TTL
    )
    cache_clear_pattern(f"{LIST_KEY}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_PATTERN)
    return data


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def delete_lab_test_type(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    entity = (
        db.query(LabTestType)
        .filter(LabTestType.id == id, LabTestType.tenant_id == current_user.tenant_id)
        .first()
    )
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    db.delete(entity)
    db.commit()

    log_audit_event(
        db,
        action="DELETE",
        resource_type="lab_test_type",
        status="success",
        user_id=current_user.id,
        username=current_user.username,
        resource_id=id,
        request=request,
    )

    cache_clear_pattern(f"{LIST_KEY}:{current_user.tenant_id}:*")
    cache_clear_pattern(f"{DETAIL_KEY}:{current_user.tenant_id}:{id}")
    cache_clear_pattern(DASHBOARD_PATTERN)
    return None
