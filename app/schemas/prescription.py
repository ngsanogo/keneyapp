from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.prescription import PrescriptionStatus

class PrescriptionBase(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None

class PrescriptionCreate(PrescriptionBase):
    prescribed_date: datetime

class PrescriptionUpdate(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[PrescriptionStatus] = None

class Prescription(PrescriptionBase):
    id: int
    status: PrescriptionStatus
    prescribed_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
