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
from fastapi.middleware.gzip import GZipMiddleware
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
    # appointments,  # Disabled: missing appointment_service.py
    auth,
    batch,
    dashboard,
    documents,
    fhir,
    lab,
    messages,
    oauth,
    patients,
    prescriptions,
    recommendations,
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

# Add GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

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
# app.include_router(appointments.router, prefix=settings.API_V1_PREFIX)  # Disabled: missing service
app.include_router(batch.router, prefix=settings.API_V1_PREFIX)
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
app.include_router(recommendations.router, prefix=settings.API_V1_PREFIX)
# app.include_router(french_healthcare.router, prefix=settings.API_V1_PREFIX)  # Temporarily disabled

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
    """
    Health check endpoint for monitoring.
    
    Returns basic health status for load balancers and monitoring systems.
    Use /ready for detailed dependency checks.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    }


@app.get("/ready")
def ready_check():
    """
    Readiness endpoint for orchestrators to know when app is ready.
    
    Performs dependency checks (database, cache) to determine if the service
    is ready to accept traffic.
    """
    from app.core.database import SessionLocal
    from app.core.cache import redis_client
    
    checks = {
        "database": False,
        "cache": False,
        "overall": False
    }
    
    # Check database connectivity
    try:
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        checks["database"] = True
    except Exception as e:
        logger.warning(f"Database readiness check failed: {e}")
    
    # Check Redis connectivity
    try:
        if redis_client:
            redis_client.ping()
            checks["cache"] = True
        else:
            checks["cache"] = True  # Cache is optional
    except Exception as e:
        logger.warning(f"Cache readiness check failed: {e}")
        checks["cache"] = True  # Cache failures shouldn't block readiness
    
    checks["overall"] = checks["database"]  # Database is required
    
    status_code = 200 if checks["overall"] else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": checks["overall"],
            "checks": checks,
            "version": settings.APP_VERSION
        }
    )


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
