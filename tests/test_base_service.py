"""
Comprehensive tests for base service class and common service patterns.
"""

import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.user import User
from app.services.base_service import BaseService
from app.exceptions import ResourceNotFoundError, TenantMismatchError


@pytest.mark.unit
class TestBaseService:
    """Test base service CRUD operations."""

    def test_get_by_id_success(self, db: Session, test_patient, test_tenant):
        """Test getting record by ID."""
        service = BaseService[Patient](db, Patient)

        patient = service.get_by_id(test_patient.id, tenant_id=test_tenant.id)

        assert patient is not None
        assert patient.id == test_patient.id
        assert patient.first_name == test_patient.first_name

    def test_get_by_id_not_found(self, db: Session, test_tenant):
        """Test getting non-existent record raises error."""
        service = BaseService[Patient](db, Patient)

        with pytest.raises(ResourceNotFoundError):
            service.get_by_id(99999, tenant_id=test_tenant.id)

    def test_get_by_id_tenant_mismatch(self, db: Session, test_patient, other_tenant):
        """Test getting record from different tenant raises error."""
        service = BaseService[Patient](db, Patient)

        with pytest.raises(TenantMismatchError):
            service.get_by_id(test_patient.id, tenant_id=other_tenant.id)

    def test_list_with_tenant_filter(self, db: Session, test_patient, test_tenant):
        """Test listing records filtered by tenant."""
        service = BaseService[Patient](db, Patient)

        patients = service.list(tenant_id=test_tenant.id)

        assert len(patients) > 0
        assert all(p.tenant_id == test_tenant.id for p in patients)

    def test_list_with_pagination(self, db: Session, test_patients_bulk, test_tenant):
        """Test listing with pagination."""
        service = BaseService[Patient](db, Patient)

        # Get first page
        page1 = service.list(tenant_id=test_tenant.id, skip=0, limit=5)
        assert len(page1) == 5

        # Get second page
        page2 = service.list(tenant_id=test_tenant.id, skip=5, limit=5)
        assert len(page2) == 5

        # Ensure different records
        page1_ids = {p.id for p in page1}
        page2_ids = {p.id for p in page2}
        assert len(page1_ids & page2_ids) == 0

    def test_count(self, db: Session, test_patients_bulk, test_tenant):
        """Test counting records."""
        service = BaseService[Patient](db, Patient)

        count = service.count(tenant_id=test_tenant.id)

        assert count == len(test_patients_bulk)

    def test_create(self, db: Session, test_tenant):
        """Test creating new record."""
        service = BaseService[Patient](db, Patient)

        data = {
            "first_name": "New",
            "last_name": "Patient",
            "date_of_birth": date(1990, 1, 1),
            "gender": "male",
            "email": "new@test.com",
            "phone": "+1234567890",
        }

        patient = service.create(data, tenant_id=test_tenant.id)

        assert patient.id is not None
        assert patient.first_name == "New"
        assert patient.tenant_id == test_tenant.id

    def test_update(self, db: Session, test_patient, test_tenant):
        """Test updating existing record."""
        service = BaseService[Patient](db, Patient)

        data = {"first_name": "Updated"}

        patient = service.update(test_patient.id, data, tenant_id=test_tenant.id)

        assert patient.first_name == "Updated"
        assert patient.id == test_patient.id

    def test_soft_delete(self, db: Session, test_patient, test_tenant):
        """Test soft deleting record."""
        service = BaseService[Patient](db, Patient)

        result = service.delete(test_patient.id, tenant_id=test_tenant.id, soft_delete=True)

        assert result is True

        # Query directly from DB to verify soft deleted
        deleted_record = db.query(Patient).filter(Patient.id == test_patient.id).first()
        assert deleted_record is not None
        assert deleted_record.is_deleted is True

    def test_bulk_create(self, db: Session, test_tenant):
        """Test bulk creating multiple records."""
        service = BaseService[Patient](db, Patient)

        data_list = [
            {
                "first_name": f"Bulk{i}",
                "last_name": "Test",
                "date_of_birth": date(1990, 1, 1),
                "gender": "male",
                "email": f"bulk{i}@test.com",
                "phone": f"+123456789{i}",
            }
            for i in range(5)
        ]

        patients = service.bulk_create(data_list, tenant_id=test_tenant.id)

        assert len(patients) == 5
        assert all(p.tenant_id == test_tenant.id for p in patients)

    def test_exists(self, db: Session, test_patient, test_tenant):
        """Test checking if record exists."""
        service = BaseService[Patient](db, Patient)

        assert service.exists(test_patient.id, tenant_id=test_tenant.id) is True
        assert service.exists(99999, tenant_id=test_tenant.id) is False


@pytest.mark.integration
class TestServicePatterns:
    """Test common service layer patterns."""

    def test_service_with_filters(self, db: Session, test_patients_bulk, test_tenant):
        """Test service with custom filters."""
        service = BaseService[Patient](db, Patient)

        # Filter by gender
        males = service.list(tenant_id=test_tenant.id, filters={"gender": "male"})

        assert len(males) > 0
        assert all(p.gender == "male" for p in males)

    def test_service_transaction_rollback(self, db: Session, test_tenant):
        """Test service respects transaction rollback."""
        service = BaseService[Patient](db, Patient)

        initial_count = service.count(tenant_id=test_tenant.id)

        try:
            # Create without commit
            service.create(
                {
                    "first_name": "Test",
                    "last_name": "Rollback",
                    "date_of_birth": date(1990, 1, 1),
                    "gender": "male",
                    "email": "rollback@test.com",
                    "phone": "+1234567890",
                },
                tenant_id=test_tenant.id,
                commit=False,
            )

            # Trigger rollback
            db.rollback()
        except:
            pass

        final_count = service.count(tenant_id=test_tenant.id)
        assert final_count == initial_count

    def test_service_exclude_deleted(self, db: Session, test_patient, test_tenant):
        """Test service excludes soft-deleted records by default."""
        service = BaseService[Patient](db, Patient)

        # Soft delete
        service.delete(test_patient.id, tenant_id=test_tenant.id, soft_delete=True)

        # List without deleted  (should exclude soft-deleted)
        patients = service.list(tenant_id=test_tenant.id, include_deleted=False)
        patient_ids = [p.id for p in patients]
        assert test_patient.id not in patient_ids

        # List with deleted (should include soft-deleted)
        all_patients = service.list(tenant_id=test_tenant.id, include_deleted=True)
        all_ids = [p.id for p in all_patients]
        assert test_patient.id in all_ids
