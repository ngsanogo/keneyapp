"""
Tests for appointment reminder service and endpoints.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.appointment_reminder import (
    AppointmentReminder,
    ReminderChannel,
    ReminderStatus,
)
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.services.reminder_service import ReminderService


class TestReminderService:
    """Test suite for ReminderService."""

    def test_create_reminders_for_appointment(
        self, db: Session, test_appointment, test_user
    ):
        """Test creating reminders for an appointment."""
        service = ReminderService(db)

        reminders = service.create_reminders_for_appointment(
            appointment_id=test_appointment.id,
            tenant_id=test_user.tenant_id,
            channels=[ReminderChannel.EMAIL, ReminderChannel.SMS],
            hours_before=[24, 2],
        )

        assert len(reminders) == 4  # 2 channels × 2 time intervals
        assert all(r.status == ReminderStatus.PENDING for r in reminders)
        assert all(r.tenant_id == test_user.tenant_id for r in reminders)

    def test_create_reminders_with_defaults(
        self, db: Session, test_appointment, test_user
    ):
        """Test creating reminders with default parameters."""
        service = ReminderService(db)

        reminders = service.create_reminders_for_appointment(
            appointment_id=test_appointment.id,
            tenant_id=test_user.tenant_id,
        )

        # Default: EMAIL and SMS channels, 24h and 2h before
        assert len(reminders) == 4
        channels = {r.channel for r in reminders}
        assert ReminderChannel.EMAIL in channels
        assert ReminderChannel.SMS in channels

    def test_create_reminders_past_time_skipped(
        self, db: Session, test_user, test_patient, test_doctor
    ):
        """Test that reminders for past times are skipped."""
        service = ReminderService(db)

        # Create appointment in the past
        past_appointment = Appointment(
            tenant_id=test_user.tenant_id,
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            appointment_date=datetime.now() - timedelta(hours=1),
            reason="Past appointment",
        )
        db.add(past_appointment)
        db.commit()

        reminders = service.create_reminders_for_appointment(
            appointment_id=past_appointment.id,
            tenant_id=test_user.tenant_id,
            hours_before=[24, 2],
        )

        # All reminders should be skipped
        assert len(reminders) == 0

    def test_create_reminders_cancelled_appointment(
        self, db: Session, test_user, test_patient, test_doctor
    ):
        """Test that reminders are not created for cancelled appointments."""
        service = ReminderService(db)

        # Create cancelled appointment
        cancelled_appointment = Appointment(
            tenant_id=test_user.tenant_id,
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            appointment_date=datetime.now() + timedelta(days=7),
            status=AppointmentStatus.CANCELLED,
            reason="Cancelled appointment",
        )
        db.add(cancelled_appointment)
        db.commit()

        reminders = service.create_reminders_for_appointment(
            appointment_id=cancelled_appointment.id,
            tenant_id=test_user.tenant_id,
        )

        assert len(reminders) == 0

    def test_get_due_reminders(self, db: Session, test_appointment, test_user):
        """Test retrieving due reminders."""
        service = ReminderService(db)

        # Create reminder that is due now
        due_reminder = AppointmentReminder(
            tenant_id=test_user.tenant_id,
            appointment_id=test_appointment.id,
            scheduled_time=datetime.now() - timedelta(minutes=1),
            channel=ReminderChannel.EMAIL,
            hours_before=24,
            status=ReminderStatus.PENDING,
        )
        db.add(due_reminder)

        # Create future reminder
        future_reminder = AppointmentReminder(
            tenant_id=test_user.tenant_id,
            appointment_id=test_appointment.id,
            scheduled_time=datetime.now() + timedelta(hours=1),
            channel=ReminderChannel.SMS,
            hours_before=2,
            status=ReminderStatus.PENDING,
        )
        db.add(future_reminder)
        db.commit()

        due_reminders = service.get_due_reminders(tenant_id=test_user.tenant_id)

        assert len(due_reminders) == 1
        assert due_reminders[0].id == due_reminder.id

    def test_send_reminder_success(self, db: Session, test_appointment, test_user):
        """Test sending a reminder successfully."""
        service = ReminderService(db)

        reminder = AppointmentReminder(
            tenant_id=test_user.tenant_id,
            appointment_id=test_appointment.id,
            scheduled_time=datetime.now(),
            channel=ReminderChannel.EMAIL,
            hours_before=24,
            status=ReminderStatus.PENDING,
        )
        db.add(reminder)
        db.commit()

        success = service.send_reminder(reminder.id)

        assert success
        db.refresh(reminder)
        assert reminder.status == ReminderStatus.SENT
        assert reminder.sent_at is not None

    def test_send_reminder_cancelled_appointment(
        self, db: Session, test_user, test_patient, test_doctor
    ):
        """Test that reminders for cancelled appointments are cancelled."""
        service = ReminderService(db)

        cancelled_appointment = Appointment(
            tenant_id=test_user.tenant_id,
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            appointment_date=datetime.now() + timedelta(days=7),
            status=AppointmentStatus.CANCELLED,
            reason="Cancelled",
        )
        db.add(cancelled_appointment)
        db.commit()

        reminder = AppointmentReminder(
            tenant_id=test_user.tenant_id,
            appointment_id=cancelled_appointment.id,
            scheduled_time=datetime.now(),
            channel=ReminderChannel.EMAIL,
            hours_before=24,
            status=ReminderStatus.PENDING,
        )
        db.add(reminder)
        db.commit()

        success = service.send_reminder(reminder.id)

        assert not success
        db.refresh(reminder)
        assert reminder.status == ReminderStatus.CANCELLED

    def test_cancel_reminders_for_appointment(
        self, db: Session, test_appointment, test_user
    ):
        """Test cancelling all reminders for an appointment."""
        service = ReminderService(db)

        # Create multiple reminders
        reminders = service.create_reminders_for_appointment(
            appointment_id=test_appointment.id,
            tenant_id=test_user.tenant_id,
        )

        count = service.cancel_reminders_for_appointment(
            appointment_id=test_appointment.id,
            tenant_id=test_user.tenant_id,
        )

        assert count == len(reminders)
        for r in reminders:
            db.refresh(r)
            assert r.status == ReminderStatus.CANCELLED

    def test_process_due_reminders(self, db: Session, test_appointment, test_user):
        """Test processing multiple due reminders."""
        service = ReminderService(db)

        # Create several due reminders
        for channel in [ReminderChannel.EMAIL, ReminderChannel.SMS]:
            reminder = AppointmentReminder(
                tenant_id=test_user.tenant_id,
                appointment_id=test_appointment.id,
                scheduled_time=datetime.now() - timedelta(minutes=1),
                channel=channel,
                hours_before=24,
                status=ReminderStatus.PENDING,
            )
            db.add(reminder)
        db.commit()

        results = service.process_due_reminders(tenant_id=test_user.tenant_id)

        assert results["total"] == 2
        assert results["sent"] >= 0
        assert results["failed"] >= 0
        assert results["sent"] + results["failed"] == results["total"]


class TestReminderEndpoints:
    """Test suite for reminder API endpoints."""

    def test_create_bulk_reminders(
        self, client, auth_headers, test_appointment, test_user
    ):
        """Test creating bulk reminders via API."""
        response = client.post(
            "/api/v1/reminders/bulk",
            headers=auth_headers,
            json={
                "appointment_id": test_appointment.id,
                "channels": ["email", "sms"],
                "hours_before": [24, 2],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data) == 4
        assert all(r["status"] == "pending" for r in data)

    def test_create_bulk_reminders_invalid_appointment(self, client, auth_headers):
        """Test creating reminders for non-existent appointment."""
        response = client.post(
            "/api/v1/reminders/bulk",
            headers=auth_headers,
            json={
                "appointment_id": 99999,
                "channels": ["email"],
                "hours_before": [24],
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_appointment_reminders(
        self, client, auth_headers, db, test_appointment, test_user
    ):
        """Test retrieving reminders for an appointment."""
        # Create reminders
        service = ReminderService(db)
        service.create_reminders_for_appointment(
            appointment_id=test_appointment.id,
            tenant_id=test_user.tenant_id,
        )

        response = client.get(
            f"/api/v1/reminders/appointment/{test_appointment.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert all(r["appointment_id"] == test_appointment.id for r in data)

    def test_process_due_reminders_admin_only(
        self, client, auth_headers, test_user_receptionist
    ):
        """Test that only admins can trigger reminder processing."""
        # Try with receptionist role
        response = client.post(
            "/api/v1/reminders/process",
            headers={"Authorization": f"Bearer {test_user_receptionist.token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_process_due_reminders_admin(
        self, client, admin_headers, db, test_appointment, test_admin
    ):
        """Test admin can process due reminders."""
        # Create a due reminder
        reminder = AppointmentReminder(
            tenant_id=test_admin.tenant_id,
            appointment_id=test_appointment.id,
            scheduled_time=datetime.now() - timedelta(minutes=1),
            channel=ReminderChannel.EMAIL,
            hours_before=24,
            status=ReminderStatus.PENDING,
        )
        db.add(reminder)
        db.commit()

        response = client.post(
            "/api/v1/reminders/process",
            headers=admin_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "sent" in data
        assert "failed" in data

    def test_cancel_appointment_reminders(
        self, client, auth_headers, db, test_appointment, test_user
    ):
        """Test cancelling reminders for an appointment."""
        # Create reminders
        service = ReminderService(db)
        service.create_reminders_for_appointment(
            appointment_id=test_appointment.id,
            tenant_id=test_user.tenant_id,
        )

        response = client.delete(
            f"/api/v1/reminders/appointment/{test_appointment.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify reminders are cancelled
        reminders = service.get_reminders_for_appointment(
            appointment_id=test_appointment.id,
            tenant_id=test_user.tenant_id,
        )
        assert all(r.status == ReminderStatus.CANCELLED for r in reminders)


@pytest.fixture
def test_appointment(db: Session, test_user, test_patient, test_doctor):
    """Create a test appointment."""
    appointment = Appointment(
        tenant_id=test_user.tenant_id,
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=datetime.now() + timedelta(days=7),
        reason="Regular checkup",
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


@pytest.fixture
def test_doctor(db: Session, test_user):
    """Create a test doctor."""
    doctor = User(
        tenant_id=test_user.tenant_id,
        email="doctor@test.com",
        username="test_doctor",
        full_name="Dr. Test",
        hashed_password="hashed",
        role=UserRole.DOCTOR,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@pytest.fixture
def test_patient(db: Session, test_user):
    """Create a test patient."""
    patient = Patient(
        tenant_id=test_user.tenant_id,
        first_name="John",
        last_name="Doe",
        date_of_birth=datetime(1990, 1, 1),
        gender="M",
        phone="1234567890",
        email="patient@test.com",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient
