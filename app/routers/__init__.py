"""
API routers for KeneyApp.
"""

from app.routers import (
    auth,
    patients,
    appointments,
    prescriptions,
    dashboard,
    users,
    tenants,
)

__all__ = [
    "auth",
    "patients",
    "appointments",
    "prescriptions",
    "dashboard",
    "users",
    "tenants",
]
