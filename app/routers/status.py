from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_current_active_user
from app.core.metrics import app_status_checks_total
from app.core.rate_limit import limiter
from app.core.audit import log_audit_event
from app.core.config import settings


router = APIRouter(prefix="/status", tags=["status"])

_started_at = datetime.utcnow()


@router.get("", dependencies=[Depends(get_current_active_user)])
@limiter.limit("100/minute")
def get_status(request: Request) -> Dict[str, str]:
    """Return lightweight app status for authenticated users.

    Includes version, environment, and approximate uptime.
    """
    app_status_checks_total.labels(tenant_id=getattr(request.state, "tenant_id", "unknown")).inc()

    uptime_seconds = int((datetime.utcnow() - _started_at).total_seconds())

    response = {
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": str(uptime_seconds),
    }

    log_audit_event(
        request=request,
        action="read",
        resource="status",
        details={"message": "status check"},
    )

    return response
