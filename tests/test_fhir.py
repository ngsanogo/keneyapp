"""Tests for FHIR interoperability."""

from datetime import date, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.fhir.converters import fhir_converter
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.tenant import Tenant

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db():
    """Create a test database session."""
    # Create new tables for each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def tenant(db):
    """Create a default tenant for fixtures."""
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        is_active=True,
        configuration={},
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def sample_patient(db, tenant):
    """Create a sample patient."""
    patient = Patient(
        tenant_id=tenant.id,
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1980, 1, 15),
        gender="male",
        email="john.doe@example.com",
        phone="+15551234567",
        address="123 Main St, Boston, MA",
        medical_history="Diabetes Type 2",
        allergies="Penicillin",
        blood_type="O+",
        emergency_contact="Jane Doe",
        emergency_phone="+15557654321",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_patient_to_fhir(sample_patient):
    """Test converting Patient to FHIR Patient resource."""
    fhir_patient = fhir_converter.patient_to_fhir(sample_patient)

    # Check resource type
    assert fhir_patient is not None

    # Check name
    assert fhir_patient["name"][0]["family"] == "Doe"
    assert fhir_patient["name"][0]["given"] == ["John"]

    # Check gender
    assert fhir_patient["gender"] == "male"

    # Check birth date
    assert str(fhir_patient["birthDate"]) == "1980-01-15"

    # Check contact info
    telecom = fhir_patient["telecom"]
    phone_found = False
    email_found = False

    for contact in telecom:
        if contact["system"] == "phone":
            assert contact["value"] == "+15551234567"
            phone_found = True
        elif contact["system"] == "email":
            assert contact["value"] == "john.doe@example.com"
            email_found = True

    assert phone_found
    assert email_found

    # Check address
    assert fhir_patient["address"][0]["text"] == "123 Main St, Boston, MA"

    # Check active status
    assert fhir_patient["active"] is True


def test_fhir_to_patient():
    """Test converting FHIR Patient resource to Patient data."""
    fhir_patient = {
        "name": [{"family": "Smith", "given": ["Jane"]}],
        "gender": "female",
        "birthDate": "1990-05-20",
        "telecom": [
            {"system": "phone", "value": "+15559876543"},
            {"system": "email", "value": "jane.smith@example.com"},
        ],
        "address": [{"text": "456 Oak Ave, NYC, NY"}],
    }

    patient_data = fhir_converter.fhir_to_patient(fhir_patient)

    assert patient_data["first_name"] == "Jane"
    assert patient_data["last_name"] == "Smith"
    assert patient_data["gender"] == "female"
    assert patient_data["date_of_birth"] == "1990-05-20"
    assert patient_data["phone"] == "+15559876543"
    assert patient_data["email"] == "jane.smith@example.com"
    assert patient_data["address"] == "456 Oak Ave, NYC, NY"


def test_appointment_to_fhir(db, sample_patient):
    """Test converting Appointment to FHIR Appointment resource."""
    tenant_id = sample_patient.tenant_id
    appointment = Appointment(
        tenant_id=tenant_id,
        patient_id=sample_patient.id,
        doctor_id=1,
        appointment_date=datetime(2024, 2, 15, 10, 30),
        reason="Annual checkup",
        status=AppointmentStatus.SCHEDULED,
        notes="Fasting required",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    fhir_appointment = fhir_converter.appointment_to_fhir(appointment)

    assert fhir_appointment is not None
    assert fhir_appointment["status"] == "booked"
    assert fhir_appointment["description"] == "Annual checkup"
    assert fhir_appointment["comment"] == "Fasting required"
    assert "2024-02-15" in fhir_appointment["start"]


def test_prescription_to_fhir(db, sample_patient):
    """Test converting Prescription to FHIR MedicationRequest resource."""
    tenant_id = sample_patient.tenant_id
    prescription = Prescription(
        tenant_id=tenant_id,
        patient_id=sample_patient.id,
        doctor_id=1,
        medication_name="Metformin",
        dosage="500mg",
        frequency="twice daily",
        duration="30 days",
        instructions="Take with meals",
        refills=3,
        prescribed_date=datetime(2024, 1, 10),
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    fhir_med_request = fhir_converter.prescription_to_fhir(prescription)

    assert fhir_med_request is not None
    assert fhir_med_request["status"] == "active"
    assert fhir_med_request["intent"] == "order"
    assert fhir_med_request["medicationCodeableConcept"]["text"] == "Metformin"
    assert len(fhir_med_request["dosageInstruction"]) > 0
    assert "500mg" in fhir_med_request["dosageInstruction"][0]["text"]
    assert (
        "Take with meals"
        in fhir_med_request["dosageInstruction"][0]["patientInstruction"]
    )


def test_appointment_status_mapping(db, sample_patient):
    """Test that appointment status is correctly mapped to FHIR."""
    statuses = [
        (AppointmentStatus.SCHEDULED, "booked"),
        (AppointmentStatus.COMPLETED, "fulfilled"),
        (AppointmentStatus.CANCELLED, "cancelled"),
    ]

    for keneyapp_status, fhir_status in statuses:
        appointment = Appointment(
            tenant_id=sample_patient.tenant_id,
            patient_id=sample_patient.id,
            doctor_id=1,
            appointment_date=datetime(2024, 2, 15, 10, 30),
            status=keneyapp_status,
        )

        fhir_appointment = fhir_converter.appointment_to_fhir(appointment)
        assert fhir_appointment["status"] == fhir_status
