"""
Main FastAPI application entry point for KeneyApp.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import (
    http_exception_handler as fastapi_http_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Ensure all models are imported and registered before metadata operations
from app import models as app_models  # noqa: F401
from app.core.config import (
    is_rate_limiting_enabled,
    settings,
    validate_production_settings,
)
from app.core.database import Base, engine
from app.core.errors import generic_exception_handler, validation_exception_handler
from app.core.logging_middleware import CorrelationIdMiddleware
from app.core.metrics import metrics_endpoint
from app.core.middleware import MetricsMiddleware, SecurityHeadersMiddleware
from app.core.rate_limit import limiter
from app.core.tracing import instrument_app, setup_tracing
from app.core.validation import RequestValidationMiddleware
from app.fhir.utils import operation_outcome
from app.graphql.schema import create_graphql_router
from app.routers import (
    appointments,
    auth,
    dashboard,
    documents,
    fhir,
    french_healthcare,
    lab,
    messages,
    oauth,
    patients,
    prescriptions,
    shares,
    subscriptions,
    tenants,
    terminology,
    users,
    websocket,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Initialize database tables (skip in tests to avoid external DB connects)
    import os

    # Production validation is done in validate_production_settings() call below and in Settings.model_post_init()

    if os.getenv("TESTING", "false").lower() not in {"1", "true", "yes"}:
        Base.metadata.create_all(bind=engine)

    # Configure or disable rate limiting based on configured settings
    rate_limiting_enabled = is_rate_limiting_enabled()
    app.state.disable_rate_limit = not rate_limiting_enabled

    if rate_limiting_enabled:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    else:
        app.state.limiter = None
        app.exception_handlers.pop(RateLimitExceeded, None)  # type: ignore[arg-type]
    yield
    # Shutdown: cleanup if needed


# Wire up OpenTelemetry tracing: call setup_tracing() at startup and instrument_app(app) after FastAPI app creation.
setup_tracing()

# Ensure critical production safeguards are enforced before serving requests.
validate_production_settings(settings)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Healthcare Data Management Platform - GDPR/HIPAA Compliant",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

instrument_app(app)

# Add custom middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RequestValidationMiddleware, max_request_size=10 * 1024 * 1024
)  # 10 MB

if str(settings.ENVIRONMENT).lower() == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(patients.router, prefix=settings.API_V1_PREFIX)
app.include_router(appointments.router, prefix=settings.API_V1_PREFIX)
app.include_router(prescriptions.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(fhir.router, prefix=settings.API_V1_PREFIX)
app.include_router(oauth.router, prefix=settings.API_V1_PREFIX)
app.include_router(tenants.router, prefix=settings.API_V1_PREFIX)
app.include_router(messages.router, prefix=settings.API_V1_PREFIX)
app.include_router(documents.router, prefix=settings.API_V1_PREFIX)
app.include_router(shares.router, prefix=settings.API_V1_PREFIX)
app.include_router(terminology.router, prefix=settings.API_V1_PREFIX)
app.include_router(subscriptions.router, prefix=settings.API_V1_PREFIX)
app.include_router(lab.router, prefix=settings.API_V1_PREFIX)
app.include_router(french_healthcare.router, prefix=settings.API_V1_PREFIX)

# Include WebSocket router (no prefix, handles /ws endpoints)
app.include_router(websocket.router)

# Include GraphQL router
graphql_router = create_graphql_router()
app.include_router(graphql_router, prefix="/graphql")

# Structured error handlers (non-FHIR). Keep FHIR HTTPException behavior below.
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/")
def root():
    """Root endpoint returning API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return metrics_endpoint()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return FHIR OperationOutcome for errors under the FHIR path; otherwise default handler.

    This preserves existing behavior for non-FHIR routes while aligning FHIR errors
    to HL7 FHIR OperationOutcome.
    """
    try:
        fhir_prefix = f"{settings.API_V1_PREFIX}/fhir"
        if str(request.url.path).startswith(fhir_prefix):
            code_map = {
                400: "invalid",
                401: "unauthorized",
                403: "forbidden",
                404: "not-found",
                405: "not-supported",
                409: "conflict",
                412: "precondition-failed",
                415: "unsupported",
                422: "processing",
                429: "throttled",
            }
            code = code_map.get(exc.status_code, "processing")
            detail = exc.detail if isinstance(exc.detail, str) else None
            return JSONResponse(
                status_code=exc.status_code,
                content=operation_outcome(code, detail),
            )
    except Exception:
        # On any handler error, fallback to default behavior
        pass

    return await fastapi_http_exception_handler(request, exc)
