"""
Main FastAPI application entry point for KeneyApp.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import (
    http_exception_handler as fastapi_http_exception_handler,
)
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.tracing import setup_tracing, instrument_app
from app.core.errors import validation_exception_handler, generic_exception_handler

# Ensure all models are imported and registered before metadata operations
from app import models as app_models  # noqa: F401
from app.core.database import engine, Base
from app.core.rate_limit import limiter
import os
from app.core.middleware import MetricsMiddleware, SecurityHeadersMiddleware
from app.core.logging_middleware import CorrelationIdMiddleware
from app.core.metrics import metrics_endpoint
from app.routers import (
    auth,
    patients,
    appointments,
    prescriptions,
    dashboard,
    users,
    fhir,
    oauth,
    tenants,
    messages,
    documents,
    shares,
    terminology,
    subscriptions,
)
from app.graphql.schema import create_graphql_router
from app.fhir.utils import operation_outcome


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Initialize database tables (skip in tests to avoid external DB connects)
    import os

    if os.getenv("TESTING", "false").lower() not in {"1", "true", "yes"}:
        Base.metadata.create_all(bind=engine)

    # Configure or disable rate limiting based on current environment
    enable_rl = os.getenv("ENABLE_RATE_LIMITING", "true").lower() in {"1", "true", "yes"}
    if enable_rl:
        app.state.disable_rate_limit = False
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    else:
        app.state.disable_rate_limit = True
        # Ensure limiter is disabled in app state and remove any handler
        if hasattr(app.state, "limiter"):
            try:
                delattr(app.state, "limiter")
            except Exception:
                pass
        try:
            app.exception_handlers.pop(RateLimitExceeded, None)  # type: ignore[arg-type]
        except Exception:
            pass
    yield
    # Shutdown: cleanup if needed


# Wire up OpenTelemetry tracing: call setup_tracing() at startup and instrument_app(app) after FastAPI app creation.
setup_tracing()

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
