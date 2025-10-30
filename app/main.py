"""
Main FastAPI application entry point for KeneyApp.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, Base
from app.core.rate_limit import limiter
from app.core.middleware import MetricsMiddleware, SecurityHeadersMiddleware
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
)
from app.graphql.schema import create_graphql_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup: Initialize database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


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

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add custom middleware
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

# Include GraphQL router
graphql_router = create_graphql_router()
app.include_router(graphql_router, prefix="/graphql")


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
