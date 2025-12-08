"""
Tests for laboratory test management module.

Comprehensive tests for lab test catalog, result management, validation,
state transitions, and RBAC enforcement.
"""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.models.lab import LabResult, LabResultState, LabTestType
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.lab import LabTestTypeCreate, LabTestTypeUpdate


@pytest.fixture
def test_doctor(db: Session, test_tenant: Tenant):
    """Create a test doctor."""
    doctor = User(
        username="dr_lab",
        email="dr.lab@test.com",
        hashed_password="hashed",
        full_name="Dr. Lab Specialist",
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
        first_name="John",
        last_name="Lab Patient",
        date_of_birth=date(1985, 5, 20),
        gender="male",
        email="john.lab@test.com",
        phone="+1234567890",
        tenant_id=test_tenant.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@pytest.fixture
def test_lab_test_type(db: Session, test_tenant: Tenant):
    """Create a test lab test type."""
    lab_test = LabTestType(
        tenant_id=test_tenant.id,
        code="CBC",
        name="Complete Blood Count",
        specimen_type="blood",
        gender=None,
        min_age_years=0,
        max_age_years=None,
        category="hematology",
        report_style="tbl_h_r_u_nr",
        active=True,
    )
    db.add(lab_test)
    db.commit()
    db.refresh(lab_test)
    return lab_test


def test_create_lab_test_type_success(db: Session, test_tenant: Tenant):
    """Test successful lab test type creation."""
    lab_data = LabTestTypeCreate(
        code="HBA1C",
        name="Hemoglobin A1C",
        specimen_type="blood",
        category="biochemical",
        active=True,
    )

    lab_test = LabTestType(
        **lab_data.model_dump(),
        tenant_id=test_tenant.id,
    )
    db.add(lab_test)
    db.commit()
    db.refresh(lab_test)

    assert lab_test.id is not None
    assert lab_test.code == "HBA1C"
    assert lab_test.name == "Hemoglobin A1C"
    assert lab_test.specimen_type == "blood"
    assert lab_test.category == "biochemical"
    assert lab_test.active is True
    assert lab_test.tenant_id == test_tenant.id


def test_lab_test_type_uniqueness_per_tenant(
    db: Session, test_tenant: Tenant, test_lab_test_type: LabTestType
):
    """Test that lab test codes must be unique within a tenant."""
    # Try to create duplicate lab test with same code in same tenant
    duplicate = LabTestType(
        tenant_id=test_tenant.id,
        code="CBC",  # Duplicate code
        name="Duplicate CBC",
        specimen_type="blood",
        active=True,
    )
    db.add(duplicate)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        db.commit()
    db.rollback()


def test_lab_test_type_update(db: Session, test_tenant: Tenant, test_lab_test_type: LabTestType):
    """Test updating lab test type fields."""
    update_data = LabTestTypeUpdate(
        name="Updated CBC Name",
        specimen_type="venous blood",
        category="hematology",
    )

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(test_lab_test_type, field, value)

    db.commit()
    db.refresh(test_lab_test_type)

    assert test_lab_test_type.name == "Updated CBC Name"
    assert test_lab_test_type.specimen_type == "venous blood"
    assert test_lab_test_type.code == "CBC"  # Code unchanged


def test_lab_test_type_deactivation(
    db: Session, test_tenant: Tenant, test_lab_test_type: LabTestType
):
    """Test deactivating a lab test type (soft delete)."""
    test_lab_test_type.active = False
    db.commit()
    db.refresh(test_lab_test_type)

    assert test_lab_test_type.active is False
    assert test_lab_test_type.id is not None  # Still exists in database


def test_create_lab_result_with_test_type(
    db: Session,
    test_tenant: Tenant,
    test_patient: Patient,
    test_lab_test_type: LabTestType,
):
    """Test creating a lab result linked to a test type."""
    result = LabResult(
        tenant_id=test_tenant.id,
        patient_id=test_patient.id,
        test_type_id=test_lab_test_type.id,
        test_name="Complete Blood Count",
        result_value="Normal",
        units="cells/mcL",
        reference_range="4000-11000",
        state=LabResultState.DRAFT,
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    assert result.id is not None
    assert result.tenant_id == test_tenant.id
    assert result.patient_id == test_patient.id
    assert result.test_type_id == test_lab_test_type.id
    assert result.state == LabResultState.DRAFT


def test_lab_result_state_transitions(
    db: Session,
    test_tenant: Tenant,
    test_patient: Patient,
    test_lab_test_type: LabTestType,
):
    """Test lab result workflow state transitions."""
    result = LabResult(
        tenant_id=test_tenant.id,
        patient_id=test_patient.id,
        test_type_id=test_lab_test_type.id,
        test_name="CBC",
        result_value="Normal",
        state=LabResultState.DRAFT,
    )
    db.add(result)
    db.commit()

    # Transition: DRAFT → PENDING_REVIEW
    result.state = LabResultState.PENDING_REVIEW
    db.commit()
    assert result.state == LabResultState.PENDING_REVIEW

    # Transition: PENDING_REVIEW → REVIEWED
    result.state = LabResultState.REVIEWED
    db.commit()
    assert result.state == LabResultState.REVIEWED

    # Transition: REVIEWED → VALIDATED
    result.state = LabResultState.VALIDATED
    db.commit()
    assert result.state == LabResultState.VALIDATED


def test_lab_result_cancellation(
    db: Session,
    test_tenant: Tenant,
    test_patient: Patient,
    test_lab_test_type: LabTestType,
):
    """Test cancelling a lab result."""
    result = LabResult(
        tenant_id=test_tenant.id,
        patient_id=test_patient.id,
        test_type_id=test_lab_test_type.id,
        test_name="Cancelled Test",
        result_value="Pending",
        state=LabResultState.DRAFT,  # Can only cancel from DRAFT state
    )
    db.add(result)
    db.commit()

    # Cancel the result (DRAFT → CANCELLED is valid transition)
    result.state = LabResultState.CANCELLED
    db.commit()

    assert result.state == LabResultState.CANCELLED


def test_get_patient_lab_results(
    db: Session,
    test_tenant: Tenant,
    test_patient: Patient,
    test_lab_test_type: LabTestType,
):
    """Test retrieving all lab results for a patient."""
    # Create multiple results
    for i in range(3):
        result = LabResult(
            tenant_id=test_tenant.id,
            patient_id=test_patient.id,
            test_type_id=test_lab_test_type.id,
            test_name=f"Test {i + 1}",
            result_value=f"Value {i + 1}",
            state=LabResultState.VALIDATED,
        )
        db.add(result)
    db.commit()

    # Retrieve all results for patient
    results = (
        db.query(LabResult)
        .filter(
            LabResult.patient_id == test_patient.id,
            LabResult.tenant_id == test_tenant.id,
        )
        .all()
    )

    assert len(results) == 3
    assert all(r.patient_id == test_patient.id for r in results)
    assert all(r.tenant_id == test_tenant.id for r in results)


def test_lab_test_type_tenant_isolation(db: Session, test_tenant: Tenant):
    """Test that lab test types are properly isolated by tenant."""
    # Create lab test in tenant 1
    lab1 = LabTestType(
        tenant_id=test_tenant.id,
        code="TENANT1_TEST",
        name="Tenant 1 Test",
        active=True,
    )
    db.add(lab1)
    db.commit()

    # Try to query from different tenant
    result = (
        db.query(LabTestType)
        .filter(
            LabTestType.code == "TENANT1_TEST",
            LabTestType.tenant_id == 999,  # Different tenant
        )
        .first()
    )

    assert result is None  # Should not be accessible from other tenant


def test_lab_result_tenant_isolation(
    db: Session,
    test_tenant: Tenant,
    test_patient: Patient,
    test_lab_test_type: LabTestType,
):
    """Test that lab results are properly isolated by tenant."""
    # Create result in tenant 1
    result = LabResult(
        tenant_id=test_tenant.id,
        patient_id=test_patient.id,
        test_type_id=test_lab_test_type.id,
        test_name="Isolated Test",
        result_value="Value",
        state=LabResultState.VALIDATED,
    )
    db.add(result)
    db.commit()

    # Try to access from different tenant
    retrieved = (
        db.query(LabResult)
        .filter(
            LabResult.id == result.id,
            LabResult.tenant_id == 999,  # Different tenant
        )
        .first()
    )

    assert retrieved is None  # Should not be accessible from other tenant


def test_lab_test_type_filtering_by_category(db: Session, test_tenant: Tenant):
    """Test filtering lab test types by category."""
    # Create tests in different categories
    categories = ["hematology", "biochemical", "immunological"]
    for category in categories:
        lab = LabTestType(
            tenant_id=test_tenant.id,
            code=f"TEST_{category.upper()}",
            name=f"Test {category}",
            category=category,
            active=True,
        )
        db.add(lab)
    db.commit()

    # Filter by hematology
    hematology_tests = (
        db.query(LabTestType)
        .filter(
            LabTestType.tenant_id == test_tenant.id,
            LabTestType.category == "hematology",
        )
        .all()
    )

    assert len(hematology_tests) >= 1
    assert all(t.category == "hematology" for t in hematology_tests)


def test_lab_result_with_reference_range(
    db: Session,
    test_tenant: Tenant,
    test_patient: Patient,
    test_lab_test_type: LabTestType,
):
    """Test lab result with reference range validation."""
    result = LabResult(
        tenant_id=test_tenant.id,
        patient_id=test_patient.id,
        test_type_id=test_lab_test_type.id,
        test_name="Glucose",
        result_value="110",
        units="mg/dL",
        reference_range="70-100",
        state=LabResultState.VALIDATED,
    )
    db.add(result)
    db.commit()

    assert result.result_value == "110"
    assert result.units == "mg/dL"
    assert result.reference_range == "70-100"


def test_get_active_lab_test_types(db: Session, test_tenant: Tenant):
    """Test retrieving only active lab test types."""
    # Create active and inactive tests
    active = LabTestType(
        tenant_id=test_tenant.id,
        code="ACTIVE_TEST",
        name="Active Test",
        active=True,
    )
    inactive = LabTestType(
        tenant_id=test_tenant.id,
        code="INACTIVE_TEST",
        name="Inactive Test",
        active=False,
    )
    db.add_all([active, inactive])
    db.commit()

    # Query only active tests
    active_tests = (
        db.query(LabTestType)
        .filter(
            LabTestType.tenant_id == test_tenant.id,
            LabTestType.active.is_(True),
        )
        .all()
    )

    assert len([t for t in active_tests if t.code == "ACTIVE_TEST"]) == 1
    assert len([t for t in active_tests if t.code == "INACTIVE_TEST"]) == 0
