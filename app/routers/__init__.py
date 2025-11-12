"""
API routers for KeneyApp.
"""

from app.routers import appointments, auth, dashboard, patients, prescriptions, tenants, users

__all__ = [
    "auth",
    "patients",
    "appointments",
    "prescriptions",
    "dashboard",
    "users",
    "tenants",
]
