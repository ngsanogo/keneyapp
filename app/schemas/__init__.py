"""
Pydantic schemas for request/response validation.
"""

from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.schemas.prescription import PrescriptionCreate, PrescriptionResponse
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

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
