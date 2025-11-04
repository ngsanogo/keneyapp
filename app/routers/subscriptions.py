"""FHIR Subscriptions (minimal) - webhook channel only.

Endpoints:
- POST /subscriptions: create a subscription
- GET /subscriptions: list subscriptions
- GET /subscriptions/{id}: get details

Notes: Minimal FHIR-like shape; persistence via SQLAlchemy model.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.dependencies import require_roles
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionStatus
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_subscription(
    payload: SubscriptionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR]))
):
    # Minimal validation: criteria must start with supported resource
    SUPPORTED = ("Patient", "Appointment", "MedicationRequest")
    if not any(payload.criteria.startswith(rt) for rt in SUPPORTED):
        raise HTTPException(status_code=400, detail="Unsupported criteria resource type")
    sub = Subscription(
        tenant_id=current_user.tenant_id,
        status=SubscriptionStatus.requested,
        reason=payload.reason,
        criteria=payload.criteria,
        endpoint=str(payload.endpoint),
        payload=payload.payload,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/", response_model=List[SubscriptionResponse])
@limiter.limit("60/minute")
def list_subscriptions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR]))
):
    return (
        db.query(Subscription)
        .filter(Subscription.tenant_id == current_user.tenant_id)
        .order_by(Subscription.id.asc())
        .all()
    )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
@limiter.limit("60/minute")
def get_subscription(
    subscription_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.DOCTOR]))
):
    sub = (
        db.query(Subscription)
        .filter(Subscription.id == subscription_id, Subscription.tenant_id == current_user.tenant_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub
