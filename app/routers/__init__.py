"""
API routers for KeneyApp.
"""

from app.routers import (
    auth,
    dashboard,
    patients,
    prescriptions,
    tenants,
    users,
)

__all__ = [
    "auth",
    "patients",
    "prescriptions",
    "dashboard",
    "users",
    "tenants",
]
