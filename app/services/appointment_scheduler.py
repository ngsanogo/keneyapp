"""
Appointment scheduling service with conflict detection.

Implements business rules for appointment booking, overlap detection,
and availability management.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.exceptions import AppointmentConflictError, raise_if_not_found
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


class AppointmentSchedulerService:
    """Service for appointment scheduling and conflict management."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_id: int, tenant_id: int) -> Appointment:
        """
        Retrieve an appointment by ID within tenant scope.

        Args:
            appointment_id: Appointment ID
            tenant_id: Tenant ID for isolation

        Returns:
            Appointment instance

        Raises:
            AppointmentNotFoundError: If appointment doesn't exist
        """
        appointment = (
            self.db.query(Appointment)
            .filter(
                Appointment.id == appointment_id,
                Appointment.tenant_id == tenant_id,
            )
            .first()
        )
        raise_if_not_found(appointment, "Appointment")
        return appointment

    def check_doctor_availability(
        self,
        doctor_id: int,
        start_time: datetime,
        duration_minutes: int,
        exclude_appointment_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
    ) -> bool:
        """
        Check if a doctor is available for a time slot.

        Args:
            doctor_id: Doctor user ID
            start_time: Appointment start time
            duration_minutes: Appointment duration in minutes
            exclude_appointment_id: Appointment ID to exclude (for updates)
            tenant_id: Optional tenant ID filter

        Returns:
            True if available, False if conflicting appointment exists
        """
        end_time = start_time + timedelta(minutes=duration_minutes)

        # Build query for potentially overlapping appointments
        # We'll check overlap logic in Python to avoid SQLAlchemy type issues
        query = self.db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_(
                [
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.IN_PROGRESS,
                ]
            ),
        )

        if tenant_id:
            query = query.filter(Appointment.tenant_id == tenant_id)

        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)

        # Get all potentially conflicting appointments and check in Python
        appointments = query.all()
        for appt in appointments:
            appt_end = appt.appointment_date + timedelta(minutes=appt.duration_minutes)
            # Overlap condition: (start < other_end) AND (end > other_start)
            if start_time < appt_end and end_time > appt.appointment_date:
                return False

        return True

    def check_patient_availability(
        self,
        patient_id: int,
        start_time: datetime,
        duration_minutes: int,
        exclude_appointment_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
    ) -> bool:
        """
        Check if a patient has overlapping appointments.

        Args:
            patient_id: Patient ID
            start_time: Appointment start time
            duration_minutes: Appointment duration in minutes
            exclude_appointment_id: Appointment ID to exclude (for updates)
            tenant_id: Optional tenant ID filter

        Returns:
            True if available, False if conflicting appointment exists
        """
        end_time = start_time + timedelta(minutes=duration_minutes)

        # Build query for potentially overlapping appointments
        query = self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.status.in_(
                [
                    AppointmentStatus.SCHEDULED,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.IN_PROGRESS,
                ]
            ),
        )

        if tenant_id:
            query = query.filter(Appointment.tenant_id == tenant_id)

        if exclude_appointment_id:
            query = query.filter(Appointment.id != exclude_appointment_id)

        # Get all potentially conflicting appointments and check in Python
        appointments = query.all()
        for appt in appointments:
            appt_end = appt.appointment_date + timedelta(minutes=appt.duration_minutes)
            # Overlap condition: (start < other_end) AND (end > other_start)
            if start_time < appt_end and end_time > appt.appointment_date:
                return False

        return True

    def create_appointment(
        self, appointment_data: AppointmentCreate, tenant_id: int
    ) -> Appointment:
        """
        Create a new appointment with conflict validation.

        Args:
            appointment_data: Appointment creation data
            tenant_id: Tenant ID for ownership

        Returns:
            Created Appointment instance

        Raises:
            AppointmentConflictError: If time slot conflicts with existing appointment
            PatientNotFoundError: If patient doesn't exist
            UserNotFoundError: If doctor doesn't exist
        """
        # Validate patient exists
        patient = (
            self.db.query(Patient)
            .filter(
                Patient.id == appointment_data.patient_id,
                Patient.tenant_id == tenant_id,
            )
            .first()
        )
        raise_if_not_found(patient, "Patient")

        # Validate doctor exists
        doctor = (
            self.db.query(User)
            .filter(
                User.id == appointment_data.doctor_id,
                User.tenant_id == tenant_id,
            )
            .first()
        )
        raise_if_not_found(doctor, "Doctor")

        # Check doctor availability
        if not self.check_doctor_availability(
            appointment_data.doctor_id,
            appointment_data.appointment_date,
            appointment_data.duration_minutes or 30,
            tenant_id=tenant_id,
        ):
            raise AppointmentConflictError(
                detail=f"Doctor is not available at {appointment_data.appointment_date}"
            )

        # Check patient availability
        if not self.check_patient_availability(
            appointment_data.patient_id,
            appointment_data.appointment_date,
            appointment_data.duration_minutes or 30,
            tenant_id=tenant_id,
        ):
            raise AppointmentConflictError(
                detail=f"Patient has conflicting appointment at {appointment_data.appointment_date}"
            )

        # Create appointment
        appointment = Appointment(
            **appointment_data.model_dump(),
            tenant_id=tenant_id,
        )
        self.db.add(appointment)
        self.db.flush()
        return appointment

    def update_appointment(
        self,
        appointment_id: int,
        appointment_data: AppointmentUpdate,
        tenant_id: int,
    ) -> Appointment:
        """
        Update an existing appointment with conflict validation.

        Args:
            appointment_id: Appointment ID
            appointment_data: Updated appointment data
            tenant_id: Tenant ID for isolation

        Returns:
            Updated Appointment instance

        Raises:
            AppointmentNotFoundError: If appointment doesn't exist
            AppointmentConflictError: If new time conflicts with existing appointment
        """
        appointment = self.get_by_id(appointment_id, tenant_id)

        update_dict = appointment_data.model_dump(exclude_unset=True)

        # If changing doctor, date, or duration, check conflicts
        if any(k in update_dict for k in ["doctor_id", "appointment_date", "duration_minutes"]):
            new_doctor_id = update_dict.get("doctor_id", appointment.doctor_id)
            new_date = update_dict.get("appointment_date", appointment.appointment_date)
            new_duration = update_dict.get("duration_minutes", appointment.duration_minutes)

            # Check doctor availability
            if not self.check_doctor_availability(
                new_doctor_id,
                new_date,
                new_duration,
                exclude_appointment_id=appointment_id,
                tenant_id=tenant_id,
            ):
                raise AppointmentConflictError(detail=f"Doctor is not available at {new_date}")

            # Check patient availability
            if not self.check_patient_availability(
                appointment.patient_id,
                new_date,
                new_duration,
                exclude_appointment_id=appointment_id,
                tenant_id=tenant_id,
            ):
                raise AppointmentConflictError(
                    detail=f"Patient has conflicting appointment at {new_date}"
                )

        # Update fields
        for field, value in update_dict.items():
            setattr(appointment, field, value)

        self.db.flush()
        return appointment

    def cancel_appointment(self, appointment_id: int, tenant_id: int) -> Appointment:
        """
        Cancel an appointment.

        Args:
            appointment_id: Appointment ID
            tenant_id: Tenant ID for isolation

        Returns:
            Cancelled Appointment instance
        """
        appointment = self.get_by_id(appointment_id, tenant_id)
        appointment.status = AppointmentStatus.CANCELLED
        self.db.flush()
        return appointment

    def get_doctor_appointments(
        self,
        doctor_id: int,
        start_date: datetime,
        end_date: datetime,
        tenant_id: int,
    ) -> List[Appointment]:
        """
        Get all appointments for a doctor within a date range.

        Args:
            doctor_id: Doctor user ID
            start_date: Range start date
            end_date: Range end date
            tenant_id: Tenant ID for isolation

        Returns:
            List of Appointment instances
        """
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.tenant_id == tenant_id,
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date < end_date,
            )
            .order_by(Appointment.appointment_date)
            .all()
        )

    def get_patient_appointments(
        self,
        patient_id: int,
        tenant_id: int,
        include_cancelled: bool = False,
    ) -> List[Appointment]:
        """
        Get all appointments for a patient.

        Args:
            patient_id: Patient ID
            tenant_id: Tenant ID for isolation
            include_cancelled: Whether to include cancelled appointments

        Returns:
            List of Appointment instances
        """
        query = self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.tenant_id == tenant_id,
        )

        if not include_cancelled:
            query = query.filter(Appointment.status != AppointmentStatus.CANCELLED)

        return query.order_by(Appointment.appointment_date.desc()).all()
