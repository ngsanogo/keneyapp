# New Resource Scaffold (Backend)

Use this brief template to add a new REST resource that matches KeneyApp patterns (RBAC, tenancy, PHI, caching, audit, metrics).

## Tiny contract

- Inputs: JSON body validated by Pydantic schemas (Create/Update). Tenant inferred from token.
- Outputs: Response schema with decrypted PHI when applicable.
- Errors: 400 for validation/conflicts, 401/403 for auth/RBAC, 404 for not found, 429 for rate limit.
- Success: 201 on create, 200 on read/update, 204 on delete.

## 1) Define Pydantic schemas

Create `app/schemas/<resource>.py`:

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class <Resource>Create(BaseModel):
    # required fields (no tenant_id here)
    name: str
    description: Optional[str] = None

class <Resource>Update(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class <Resource>Response(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
```

## 2) Define SQLAlchemy model

Create `app/models/<resource>.py` with tenant scoping and timestamps:

```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from app.core.database import Base

class <Resource>(Base):
    __tablename__ = "<resources>"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
```

Add Alembic migration:

```bash
alembic revision --autogenerate -m "add <resources>"
alembic upgrade head
```

## 3) Router with RBAC, rate limits, audit, caching

Create `app/routers/<resources>.py`:

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.core.rate_limit import limiter
from app.core.audit import log_audit_event
from app.core.cache import cache_get, cache_set, cache_clear_pattern
from app.models.user import User, UserRole
from app.models.<resource> import <Resource>
from app.schemas.<resource> import <Resource>Create, <Resource>Update, <Resource>Response

LIST_KEY = "<resources>:list"
DETAIL_KEY = "<resources>:detail"
LIST_TTL = 120
DETAIL_TTL = 300
DASHBOARD_PATTERN = "dashboard:*"

router = APIRouter(prefix="/<resources>", tags=["<resources>"])

@router.post("/", response_model=<Resource>Response, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_<resource>(
    payload: <Resource>Create,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR]))
):
    entity = <Resource>(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)

    log_audit_event(db, "CREATE", "<resource>", entity.id, "success", current_user.id, current_user.username, request=request)

    data = <Resource>Response.model_validate(entity).model_dump(mode="json")
    cache_set(f"{DETAIL_KEY}:{current_user.tenant_id}:{entity.id}", data, expire=DETAIL_TTL)
    cache_clear_pattern(f"{LIST_KEY}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_PATTERN)
    return data

@router.get("/", response_model=List[<Resource]Response])
@limiter.limit("60/minute")
def list_<resources>(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]))
):
    key = f"{LIST_KEY}:{current_user.tenant_id}:{skip}:{limit}"
    if (cached := cache_get(key)) is not None:
        return cached

    items = (db.query(<Resource>)
               .filter(<Resource>.tenant_id == current_user.tenant_id)
               .offset(skip).limit(min(100, max(1, limit))).all())
    data = [<Resource>Response.model_validate(x).model_dump(mode="json") for x in items]
    cache_set(key, data, expire=LIST_TTL)
    return data

@router.get("/{id}", response_model=<Resource>Response)
@limiter.limit("120/minute")
def get_<resource>(id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST]))):
    key = f"{DETAIL_KEY}:{current_user.tenant_id}:{id}"
    if (cached := cache_get(key)) is not None:
        return cached

    entity = (db.query(<Resource>)
                .filter(<Resource>.id == id, <Resource>.tenant_id == current_user.tenant_id)
                .first())
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    data = <Resource>Response.model_validate(entity).model_dump(mode="json")
    cache_set(key, data, expire=DETAIL_TTL)
    return data

@router.put("/{id}", response_model=<Resource>Response)
@limiter.limit("10/minute")
def update_<resource>(id: int, payload: <Resource>Update, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR]))):
    entity = (db.query(<Resource>)
                .filter(<Resource>.id == id, <Resource>.tenant_id == current_user.tenant_id)
                .first())
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(entity, k, v)
    db.commit(); db.refresh(entity)

    log_audit_event(db, "UPDATE", "<resource>", entity.id, "success", current_user.id, current_user.username, request=request)

    data = <Resource>Response.model_validate(entity).model_dump(mode="json")
    cache_set(f"{DETAIL_KEY}:{current_user.tenant_id}:{entity.id}", data, expire=DETAIL_TTL)
    cache_clear_pattern(f"{LIST_KEY}:{current_user.tenant_id}:*")
    cache_clear_pattern(DASHBOARD_PATTERN)
    return data

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
def delete_<resource>(id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.ADMIN))):
    entity = (db.query(<Resource>)
                .filter(<Resource>.id == id, <Resource>.tenant_id == current_user.tenant_id)
                .first())
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    db.delete(entity); db.commit()
    log_audit_event(db, "DELETE", "<resource>", id, "success", current_user.id, current_user.username, request=request)

    cache_clear_pattern(f"{LIST_KEY}:{current_user.tenant_id}:*")
    cache_clear_pattern(f"{DETAIL_KEY}:{current_user.tenant_id}:{id}")
    cache_clear_pattern(DASHBOARD_PATTERN)
```

Register in `app/main.py`:

```python
from app.routers import <resources>
app.include_router(<resources>.router, prefix=settings.API_V1_PREFIX)
```

## 4) Metrics

- Add counter/gauge in `app/core/metrics.py` if this resource needs KPIs.
- Bump counters in router after successful mutations (see `patient_operations_total`).

## 5) Tests (minimal)

Create `tests/test_<resources>.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_requires_auth():
    assert client.get("/api/v1/<resources>/").status_code in (401, 403)
```

## 6) PHI handling (if applicable)

- Use `app/services/patient_security.py` patterns to encrypt/decrypt fields.
- Never log PHI; rely on audit + correlation IDs.
