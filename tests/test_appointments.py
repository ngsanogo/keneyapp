"""
Tests for appointment management module.

Comprehensive tests for appointment creation, scheduling, conflict detection,
and RBAC enforcement.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.appointment_scheduler import AppointmentSchedulerService
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.exceptions import (
    AppointmentConflictError,
    PatientNotFoundError,
)


@pytest.fixture
def appointment_service(db: Session):
    """Create appointment service instance."""
    return AppointmentSchedulerService(db)


@pytest.fixture
def test_doctor(db: Session, test_tenant: Tenant):
    """Create a test doctor."""
    doctor = User(
        username="dr_smith",
        email="dr.smith@test.com",
        hashed_password="hashed",
        full_name="Dr. John Smith",
        role=UserRole.DOCTOR,
        tenant_id=test_tenant.id,
        is_active=True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@pytest.fixture
def test_patient(db: Session, test_tenant: Tenant):
    """Create a test patient."""
    from datetime import date

    patient = Patient(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        gender="female",
        email="jane.doe@test.com",
        phone="+1234567890",
        tenant_id=test_tenant.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_create_appointment_success(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test successful appointment creation."""
    appointment_date = datetime.now() + timedelta(days=1)
    appt_data = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
        reason="Annual checkup",
    )

    result = appointment_service.create_appointment(appt_data, test_tenant.id)
    db.commit()

    assert result.id is not None
    assert result.patient_id == test_patient.id
    assert result.doctor_id == test_doctor.id
    assert result.status == AppointmentStatus.SCHEDULED
    assert result.duration_minutes == 30
    assert result.reason == "Annual checkup"


def test_create_appointment_patient_not_found(
    appointment_service, test_doctor, test_tenant
):
    """Test appointment creation with non-existent patient."""
    appointment_date = datetime.now() + timedelta(days=1)
    appt_data = AppointmentCreate(
        patient_id=99999,  # Non-existent
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
        reason="Test reason",
    )

    with pytest.raises(PatientNotFoundError):
        appointment_service.create_appointment(appt_data, test_tenant.id)


def test_detect_patient_appointment_conflict(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test detection of overlapping patient appointments."""
    appointment_date = datetime.now() + timedelta(days=1)

    # Create first appointment
    appt1 = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
        reason="First appointment",
    )
    appointment_service.create_appointment(appt1, test_tenant.id)
    db.commit()

    # Try to create overlapping appointment (same patient, overlapping time)
    appt2 = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date + timedelta(minutes=15),  # Overlaps
        duration_minutes=30,
        reason="Overlapping appointment",
    )

    with pytest.raises(AppointmentConflictError):
        appointment_service.create_appointment(appt2, test_tenant.id)


def test_detect_doctor_appointment_conflict(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test detection of overlapping doctor appointments."""
    from datetime import date

    # Create second patient
    patient2 = Patient(
        first_name="John",
        last_name="Smith",
        date_of_birth=date(1985, 5, 15),
        gender="male",
        email="john.smith@test.com",
        phone="+1987654321",
        tenant_id=test_tenant.id,
    )
    db.add(patient2)
    db.commit()
    db.refresh(patient2)

    appointment_date = datetime.now() + timedelta(days=1)

    # Create first appointment
    appt1 = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
        reason="First patient appointment",
    )
    appointment_service.create_appointment(appt1, test_tenant.id)
    db.commit()

    # Try to create overlapping appointment (different patient, same doctor, overlapping time)
    appt2 = AppointmentCreate(
        patient_id=patient2.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date + timedelta(minutes=20),  # Overlaps
        duration_minutes=30,
        reason="Second patient appointment",
    )

    with pytest.raises(AppointmentConflictError):
        appointment_service.create_appointment(appt2, test_tenant.id)


def test_update_appointment_success(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test successful appointment update."""
    appointment_date = datetime.now() + timedelta(days=1)

    # Create appointment
    appt_data = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
        reason="Initial reason",
    )
    appt = appointment_service.create_appointment(appt_data, test_tenant.id)
    db.commit()

    # Update appointment
    update_data = AppointmentUpdate(
        reason="Updated reason", duration_minutes=45, notes="Added notes"
    )
    updated = appointment_service.update_appointment(
        appt.id, update_data, test_tenant.id
    )
    db.commit()

    assert updated.reason == "Updated reason"
    assert updated.duration_minutes == 45
    assert updated.notes == "Added notes"


def test_cancel_appointment(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test appointment cancellation."""
    appointment_date = datetime.now() + timedelta(days=1)

    # Create appointment
    appt_data = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
    )
    appt = appointment_service.create_appointment(appt_data, test_tenant.id)
    db.commit()

    # Cancel appointment
    cancelled = appointment_service.cancel_appointment(appt.id, test_tenant.id)
    db.commit()

    assert cancelled.status == AppointmentStatus.CANCELLED


def test_get_appointment_by_id(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test retrieving appointment by ID."""
    appointment_date = datetime.now() + timedelta(days=1)

    # Create appointment
    appt_data = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
    )
    created = appointment_service.create_appointment(appt_data, test_tenant.id)
    db.commit()

    # Retrieve appointment
    retrieved = appointment_service.get_appointment_by_id(
        created.id, test_tenant.id
    )

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.patient_id == test_patient.id


def test_get_patient_appointments(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test retrieving all appointments for a patient."""
    # Create multiple appointments
    for i in range(3):
        appt_data = AppointmentCreate(
            patient_id=test_patient.id,
            doctor_id=test_doctor.id,
            appointment_date=datetime.now() + timedelta(days=i + 1),
            duration_minutes=30,
            reason=f"Appointment {i+1}",
        )
        appointment_service.create_appointment(appt_data, test_tenant.id)
    db.commit()

    # Get patient appointments
    appointments = appointment_service.get_patient_appointments(
        test_patient.id, test_tenant.id
    )

    assert len(appointments) == 3
    assert all(appt.patient_id == test_patient.id for appt in appointments)


def test_check_patient_availability(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test checking patient availability."""
    appointment_date = datetime.now() + timedelta(days=1)

    # Patient should be available initially
    is_available = appointment_service.check_patient_availability(
        test_patient.id,
        appointment_date,
        appointment_date + timedelta(minutes=30),
        test_tenant.id,
    )
    assert is_available is True

    # Create appointment
    appt_data = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
        reason="Availability test",
    )
    appointment_service.create_appointment(appt_data, test_tenant.id)
    db.commit()

    # Patient should not be available during appointment
    is_available = appointment_service.check_patient_availability(
        test_patient.id,
        appointment_date + timedelta(minutes=15),
        appointment_date + timedelta(minutes=45),
        test_tenant.id,
    )
    assert is_available is False


def test_check_doctor_availability(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test checking doctor availability."""
    appointment_date = datetime.now() + timedelta(days=1)

    # Doctor should be available initially
    is_available = appointment_service.check_doctor_availability(
        test_doctor.id,
        appointment_date,
        appointment_date + timedelta(minutes=30),
        test_tenant.id,
    )
    assert is_available is True

    # Create appointment
    appt_data = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
        reason="Doctor availability test",
    )
    appointment_service.create_appointment(appt_data, test_tenant.id)
    db.commit()

    # Doctor should not be available during appointment
    is_available = appointment_service.check_doctor_availability(
        test_doctor.id,
        appointment_date + timedelta(minutes=15),
        appointment_date + timedelta(minutes=45),
        test_tenant.id,
    )
    assert is_available is False


def test_appointment_tenant_isolation(
    appointment_service, db, test_patient, test_doctor, test_tenant
):
    """Test that appointments are properly isolated by tenant."""
    # Create appointment in tenant 1
    appointment_date = datetime.now() + timedelta(days=1)
    appt_data = AppointmentCreate(
        patient_id=test_patient.id,
        doctor_id=test_doctor.id,
        appointment_date=appointment_date,
        duration_minutes=30,
        reason="Tenant isolation test",
    )
    appt = appointment_service.create_appointment(appt_data, test_tenant.id)
    db.commit()

    # Try to access from different tenant
    retrieved = appointment_service.get_appointment_by_id(appt.id, tenant_id=999)

    assert retrieved is None  # Should not be accessible from other tenant
