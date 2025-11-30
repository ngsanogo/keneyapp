from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus


def run(tenant_id: int, patient_id: int, doctor_id: int) -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        demos = [
            Appointment(
                tenant_id=tenant_id,
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=now + timedelta(days=1),
                duration_minutes=30,
                status=AppointmentStatus.SCHEDULED,
                reason="Routine checkup",
                notes=None,
            ),
            Appointment(
                tenant_id=tenant_id,
                patient_id=patient_id,
                doctor_id=doctor_id,
                appointment_date=now + timedelta(days=2, hours=2),
                duration_minutes=45,
                status=AppointmentStatus.CONFIRMED,
                reason="Follow-up",
                notes="Bring lab results",
            ),
        ]
        for appt in demos:
            db.add(appt)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    # Default demo IDs; adjust as needed for your environment.
    run(tenant_id=1, patient_id=1, doctor_id=1)
