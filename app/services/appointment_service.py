from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.exceptions import raise_if_not_found


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_id: int, tenant_id: int) -> Appointment:
        appt = (
            self.db.query(Appointment)
            .filter(Appointment.id == appointment_id, Appointment.tenant_id == tenant_id)
            .first()
        )
        return raise_if_not_found(appt, "Appointment not found")

    def list(self, tenant_id: int, patient_id: Optional[int] = None) -> List[Appointment]:
        q = self.db.query(Appointment).filter(Appointment.tenant_id == tenant_id)
        if patient_id:
            q = q.filter(Appointment.patient_id == patient_id)
        return q.order_by(Appointment.scheduled_at.desc()).all()

    def create(self, data: dict, tenant_id: int) -> Appointment:
        appt = Appointment(**data, tenant_id=tenant_id)
        self.db.add(appt)
        self.db.commit()
        self.db.refresh(appt)
        return appt

    def update(self, appointment_id: int, data: dict, tenant_id: int) -> Appointment:
        appt = self.get_by_id(appointment_id, tenant_id)
        for k, v in data.items():
            setattr(appt, k, v)
        self.db.commit()
        self.db.refresh(appt)
        return appt

    def delete(self, appointment_id: int, tenant_id: int) -> None:
        appt = self.get_by_id(appointment_id, tenant_id)
        self.db.delete(appt)
        self.db.commit()
