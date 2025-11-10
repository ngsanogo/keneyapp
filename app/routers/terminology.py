"""Terminology API endpoints.

Provides simple validation and translation endpoints for medical codes.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.dependencies import require_roles
from app.models.user import User, UserRole
from app.services.terminology import validate_code, translate_code


router = APIRouter(prefix="/terminology", tags=["terminology"])


@router.get("/validate")
@limiter.limit("120/minute")
def validate_code_endpoint(
    request: Request,
    system: str = Query(
        ...,
        description="Code system e.g., loinc, icd11, snomed_ct, atc, cpt, ccam, dicom",
    ),
    code: str = Query(..., description="Code value"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST
        )
    ),
) -> Dict[str, Any]:
    """Validate a medical code."""
    return validate_code(db, system=system, code=code)


@router.post("/translate")
@limiter.limit("60/minute")
def translate_code_endpoint(
    request: Request,
    payload: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN, UserRole.DOCTOR, UserRole.NURSE, UserRole.RECEPTIONIST
        )
    ),
) -> Dict[str, Any]:
    """Translate a code from one system to another.

    Body Example:
    {
      "system_from": "icd11",
      "code_from": "2E65",
      "system_to": "snomed_ct"
    }
    """
    return translate_code(
        db,
        system_from=payload.get("system_from", ""),
        code_from=payload.get("code_from", ""),
        system_to=payload.get("system_to", ""),
    )
