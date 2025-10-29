"""
Pydantic schemas for request/response validation.
"""

from app.schemas.user import UserCreate, UserResponse, UserLogin, Token
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
)
from app.schemas.prescription import PrescriptionCreate, PrescriptionResponse

__all__ = [
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "Token",
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "PrescriptionCreate",
    "PrescriptionResponse",
]
