"""
Tests for patient service layer.

Tests business logic and validation independent of HTTP routing.
"""

from datetime import date

import pytest

from app.exceptions import (
    DuplicateResourceError,
    PatientNotFoundError,
    TenantMismatchError,
)
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.patient_service import PatientService


def test_create_patient_success(db, test_tenant):
    """Test successful patient creation."""
    service = PatientService(db)
    patient_data = PatientCreate(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        gender="male",
        email="john.doe@test.com",
        phone="+1234567890",
    )

    patient = service.create_patient(patient_data, test_tenant.id)
    db.commit()

    assert patient.id is not None
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
    assert patient.tenant_id == test_tenant.id


def test_create_patient_duplicate_email(db, test_tenant):
    """Test that creating patient with duplicate email raises error."""
    service = PatientService(db)
    patient_data = PatientCreate(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1995, 5, 15),
        gender="female",
        email="duplicate@test.com",
        phone="+1234567891",
    )

    # Create first patient
    service.create_patient(patient_data, test_tenant.id)
    db.commit()

    # Attempt to create second patient with same email
    with pytest.raises(DuplicateResourceError) as exc_info:
        service.create_patient(patient_data, test_tenant.id)

    assert "duplicate@test.com" in str(exc_info.value.detail)


def test_get_patient_by_id(db, test_tenant):
    """Test retrieving patient by ID."""
    service = PatientService(db)
    # create a patient under the tenant (avoid relying on conftest's test_patient)
    p = service.create_patient(
        PatientCreate(
            first_name="Alice",
            last_name="Wonder",
            date_of_birth=date(1990, 1, 1),
            gender="female",
            email="alice@example.com",
            phone="+1111111111",
        ),
        test_tenant.id,
    )
    db.commit()

    patient = service.get_by_id(p.id, test_tenant.id)

    assert patient.id == p.id
    assert patient.first_name == "Alice"


def test_get_patient_not_found(db, test_tenant):
    """Test that getting non-existent patient raises error."""
    service = PatientService(db)

    with pytest.raises(PatientNotFoundError):
        service.get_by_id(99999, test_tenant.id)


def test_get_patient_wrong_tenant(db, test_tenant, other_tenant):
    """Test that accessing patient from different tenant raises error."""
    service = PatientService(db)

    # Create patient in test_tenant
    patient_data = PatientCreate(
        first_name="Tenant1",
        last_name="Patient",
        date_of_birth=date(1985, 1, 1),
        gender="male",
        email="tenant1@test.com",
        phone="+1234567892",
    )
    patient = service.create_patient(patient_data, test_tenant.id)
    db.commit()

    # Try to access from other_tenant
    with pytest.raises(PatientNotFoundError):
        service.get_by_id(patient.id, other_tenant.id)


def test_update_patient_success(db, test_tenant):
    """Test successful patient update."""
    service = PatientService(db)

    p = service.create_patient(
        PatientCreate(
            first_name="Bob",
            last_name="Original",
            date_of_birth=date(1988, 2, 2),
            gender="male",
            email="bob.original@test.com",
            phone="+2222222222",
        ),
        test_tenant.id,
    )
    db.commit()

    update_data = PatientUpdate(
        first_name="UpdatedFirst",
        phone="+9876543210",
    )

    updated = service.update_patient(p.id, update_data, test_tenant.id)
    db.commit()

    assert updated.first_name == "UpdatedFirst"
    assert updated.phone == "+9876543210"
    assert updated.last_name == "Original"  # Unchanged


def test_update_patient_email_conflict(db, test_tenant):
    """Test that updating to duplicate email raises error."""
    service = PatientService(db)

    # Create two patients
    patient1_data = PatientCreate(
        first_name="Patient",
        last_name="One",
        date_of_birth=date(1990, 1, 1),
        gender="male",
        email="patient1@test.com",
        phone="+1111111111",
    )
    service.create_patient(patient1_data, test_tenant.id)

    patient2_data = PatientCreate(
        first_name="Patient",
        last_name="Two",
        date_of_birth=date(1992, 2, 2),
        gender="female",
        email="patient2@test.com",
        phone="+2222222222",
    )
    patient2 = service.create_patient(patient2_data, test_tenant.id)
    db.commit()

    # Try to update patient2 email to patient1's email
    update_data = PatientUpdate(email="patient1@test.com")

    with pytest.raises(DuplicateResourceError):
        service.update_patient(patient2.id, update_data, test_tenant.id)


def test_delete_patient(db, test_tenant):
    """Test patient deletion."""
    service = PatientService(db)

    p = service.create_patient(
        PatientCreate(
            first_name="Charlie",
            last_name="Temp",
            date_of_birth=date(1992, 3, 3),
            gender="male",
            email="charlie.temp@test.com",
            phone="+3333333333",
        ),
        test_tenant.id,
    )
    db.commit()

    patient_id = p.id
    service.delete_patient(patient_id, test_tenant.id)
    db.commit()

    # Verify patient is deleted
    with pytest.raises(PatientNotFoundError):
        service.get_by_id(patient_id, test_tenant.id)


def test_list_patients(db, test_tenant):
    """Test listing patients with pagination."""
    service = PatientService(db)

    # Create multiple patients
    for i in range(5):
        patient_data = PatientCreate(
            first_name=f"Patient{i}",
            last_name=f"Test{i}",
            date_of_birth=date(1990 + i, 1, 1),
            gender="male" if i % 2 == 0 else "female",
            email=f"patient{i}@test.com",
            phone=f"+123456789{i}",
        )
        service.create_patient(patient_data, test_tenant.id)
    db.commit()

    # List all
    patients = service.list_patients(test_tenant.id, skip=0, limit=10)
    assert len(patients) == 5

    # Test pagination
    patients_page1 = service.list_patients(test_tenant.id, skip=0, limit=2)
    assert len(patients_page1) == 2

    patients_page2 = service.list_patients(test_tenant.id, skip=2, limit=2)
    assert len(patients_page2) == 2


def test_count_patients(db, test_tenant):
    """Test counting patients."""
    service = PatientService(db)

    initial_count = service.count_patients(test_tenant.id)

    # Create a patient
    patient_data = PatientCreate(
        first_name="Count",
        last_name="Test",
        date_of_birth=date(1990, 1, 1),
        gender="male",
        email="count@test.com",
        phone="+1234567890",
    )
    service.create_patient(patient_data, test_tenant.id)
    db.commit()

    new_count = service.count_patients(test_tenant.id)
    assert new_count == initial_count + 1


def test_search_patients(db, test_tenant):
    """Test searching patients by name or email."""
    service = PatientService(db)

    # Create test patients
    patients_data = [
        PatientCreate(
            first_name="Alice",
            last_name="Smith",
            date_of_birth=date(1990, 1, 1),
            gender="female",
            email="alice.smith@test.com",
            phone="+1111111111",
        ),
        PatientCreate(
            first_name="Bob",
            last_name="Smith",
            date_of_birth=date(1985, 5, 15),
            gender="male",
            email="bob.smith@test.com",
            phone="+2222222222",
        ),
        PatientCreate(
            first_name="Charlie",
            last_name="Jones",
            date_of_birth=date(1992, 10, 20),
            gender="male",
            email="charlie@test.com",
            phone="+3333333333",
        ),
    ]

    for pd in patients_data:
        service.create_patient(pd, test_tenant.id)
    db.commit()

    # Search by last name
    results = service.search_patients(test_tenant.id, "Smith")
    assert len(results) == 2

    # Search by first name
    results = service.search_patients(test_tenant.id, "Alice")
    assert len(results) == 1
    assert results[0].first_name == "Alice"

    # Search by email
    results = service.search_patients(test_tenant.id, "charlie@")
    assert len(results) == 1

    # Search with no results
    results = service.search_patients(test_tenant.id, "Nonexistent")
    assert len(results) == 0


def test_validate_patient_access(db, test_tenant, other_tenant):
    """Test patient access validation across tenants."""
    service = PatientService(db)

    # Create a patient under test_tenant
    created = service.create_patient(
        PatientCreate(
            first_name="Eva",
            last_name="Tenant",
            date_of_birth=date(1991, 4, 4),
            gender="female",
            email="eva.tenant@test.com",
            phone="+4444444444",
        ),
        test_tenant.id,
    )
    db.commit()

    # Valid access
    patient = service.validate_patient_access(created.id, test_tenant.id)
    assert patient.id == created.id

    # Invalid access (different tenant)
    with pytest.raises(TenantMismatchError):
        service.validate_patient_access(created.id, other_tenant.id)
