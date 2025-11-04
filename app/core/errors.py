"""
Centralized error handlers that produce structured JSON with correlation IDs.

These handlers avoid leaking PHI and keep responses consistent across the API.
FHIR-specific behavior remains in the HTTPException handler defined in main.py.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Optional, Union

from app.core.logging_middleware import get_correlation_id


def _base_error_envelope(
    request: Request,
    *,
    status_code: int,
    error: str,
    message: Optional[str] = None,
    details: Optional[Union[dict, list]] = None,
):
    """Create a consistent error envelope with correlation ID."""
    cid = get_correlation_id(request)
    body = {
        "error": {
            "type": error,
            "message": message or "An error occurred.",
            "details": details,
        },
        "correlation_id": cid,
    }
    return JSONResponse(status_code=status_code, content=body)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return structured 422 for request validation errors with correlation ID."""
    # Convert pydantic/fastapi validation errors into a simpler list
    error_list = exc.errors() if hasattr(exc, "errors") else None
    return _base_error_envelope(
        request,
        status_code=422,
        error="validation_error",
        message="Request validation failed.",
        details=error_list,
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler to ensure a structured response and correlation ID.

    This intentionally returns a 500 with a generic message and no sensitive details.
    """
    return _base_error_envelope(
        request,
        status_code=500,
        error="internal_error",
        message="Unexpected server error. Please contact support with the correlation ID.",
        details=None,
    )
