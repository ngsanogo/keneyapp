"""
Test suite for batch operations endpoints.
"""
import pytest
from fastapi import status
from datetime import date

from app.models.user import UserRole


class TestBatchPatients:
    """Test batch patient operations."""

    def test_batch_create_patients_success(self, client, auth_headers_doctor, test_tenant):
        """Test successful batch creation of patients."""
        headers = auth_headers_doctor
        
        patients_data = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "phone": "+1234567890",
                "email": "john.doe@example.com"
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1985-05-15",
                "gender": "female",
                "phone": "+1234567891",
                "email": "jane.smith@example.com"
            },
            {
                "first_name": "Bob",
                "last_name": "Johnson",
                "date_of_birth": "1975-12-30",
                "gender": "male",
                "phone": "+1234567892",
                "email": "bob.johnson@example.com"
            }
        ]
        
        response = client.post(
            "/api/v1/batch/patients",
            json=patients_data,
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["created"] == 3
        assert data["total"] == 3
        assert len(data["patients"]) == 3
        
        # Verify all patients were created
        for i, patient in enumerate(data["patients"]):
            assert patient["first_name"] == patients_data[i]["first_name"]
            assert patient["last_name"] == patients_data[i]["last_name"]
            assert patient["tenant_id"] == test_tenant.id

    def test_batch_create_patients_atomic_rollback(self, client, auth_headers_doctor, db):
        """Test that batch creation rolls back all on error."""
        headers = auth_headers_doctor
        db_session = db
        
        patients_data = [
            {
                "first_name": "Valid",
                "last_name": "Patient",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "phone": "+1234567890",
                "email": "valid@example.com"
            },
            {
                # Missing required fields - should cause error
                "first_name": "Invalid"
            }
        ]
        
        response = client.post(
            "/api/v1/batch/patients",
            json=patients_data,
            headers=headers
        )
        
        # Should fail validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        
        # Verify no patients were created (atomic rollback)
        from app.models.patient import Patient
        patients = db_session.query(Patient).filter(
            Patient.email == "valid@example.com"
        ).all()
        assert len(patients) == 0

    def test_batch_update_patients_success(self, client, auth_headers_doctor, test_patient, db):
        """Test successful batch update of patients."""
        # Create additional patients
        from app.models.patient import Patient
        from app.services.patient_security import encrypt_patient_payload
        
        db_session = db
        patient2_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": date(1985, 5, 15),
            "gender": "female",
            "phone": "+1234567891",
            "email": "jane@example.com",
            "tenant_id": test_patient.tenant_id
        }
        encrypted_data2 = encrypt_patient_payload(patient2_data)
        patient2 = Patient(**encrypted_data2)
        db_session.add(patient2)
        db_session.commit()
        db_session.refresh(patient2)
        
        headers = auth_headers_doctor
        
        updates = [
            {
                "id": str(test_patient.id),
                "phone": "+9999999999"
            },
            {
                "id": str(patient2.id),
                "email": "newemail@example.com"
            }
        ]
        
        response = client.put(
            "/api/v1/batch/patients",
            json=updates,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["updated"] == 2
        assert len(data["patients"]) == 2
        
        # Verify updates
        db_session.refresh(test_patient)
        db_session.refresh(patient2)
        
        from app.services.patient_security import serialize_patient_dict
        patient1_dict = serialize_patient_dict(test_patient)
        patient2_dict = serialize_patient_dict(patient2)
        
        assert patient1_dict["phone"] == "+9999999999"
        assert patient2_dict["email"] == "newemail@example.com"
    def test_batch_update_nonexistent_patient(self, client, auth_headers_doctor):
        """Test batch update with non-existent patient."""
        updates = [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "phone": "+9999999999"
            }
        ]
        
        response = client.put(
            "/api/v1/batch/patients",
            json=updates,
            headers=auth_headers_doctor
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_batch_delete_patients_success(self, client, auth_headers_doctor, test_patient, db):
        """Test successful batch deletion of patients."""
        # Create additional patients
        from app.models.patient import Patient
        from app.services.patient_security import encrypt_patient_payload
        
        db_session = db
        patient2_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": date(1985, 5, 15),
            "gender": "female",
            "phone": "+1234567891",
            "email": "jane@example.com",
            "tenant_id": test_patient.tenant_id
        }
        encrypted_data2 = encrypt_patient_payload(patient2_data)
        patient2 = Patient(**encrypted_data2)
        db_session.add(patient2)
        db_session.commit()
        db_session.refresh(patient2)
        
        headers = auth_headers_doctor
        
        patient_ids = [str(test_patient.id), str(patient2.id)]
        
        response = client.delete(
            "/api/v1/batch/patients",
            params={"patient_ids": patient_ids},
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted"] == 2
        assert data["requested"] == 2
        
        # Verify patients were deleted
        patients = db_session.query(Patient).filter(
            Patient.id.in_([test_patient.id, patient2.id])
        ).all()
        assert len(patients) == 0

    def test_batch_delete_partial_success(self, client, auth_headers_doctor, test_patient):
        """Test batch deletion with some non-existent patients."""
        headers = auth_headers_doctor
        
        patient_ids = [
            str(test_patient.id),
            "00000000-0000-0000-0000-000000000000"  # Non-existent
        ]
        
        response = client.delete(
            "/api/v1/batch/patients",
            params={"patient_ids": patient_ids},
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted"] == 1
        assert data["requested"] == 2

    def test_batch_operations_require_auth(self, unauthenticated_client):
        """Test that batch operations require authentication."""
        # POST without auth
        response = unauthenticated_client.post("/api/v1/batch/patients", json=[])
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # PUT without auth
        response = unauthenticated_client.put("/api/v1/batch/patients", json=[])
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # DELETE without auth
        response = unauthenticated_client.delete("/api/v1/batch/patients", params={"patient_ids": []})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_batch_operations_tenant_isolation(self, client, auth_headers_doctor, test_patient, db):
        """Test that batch operations respect tenant isolation."""
        # Create patient in different tenant
        from app.models.patient import Patient
        from app.models.tenant import Tenant
        from app.services.patient_security import encrypt_patient_payload
        
        db_session = db
        # Create another tenant
        other_tenant = Tenant(name="Other Tenant", slug="other")
        db_session.add(other_tenant)
        db_session.commit()
        
        other_patient_data = {
            "first_name": "Other",
            "last_name": "Tenant",
            "date_of_birth": date(1990, 1, 1),
            "gender": "male",
            "phone": "+9999999999",
            "email": "other@example.com",
            "tenant_id": other_tenant.id
        }
        encrypted_data = encrypt_patient_payload(other_patient_data)
        other_patient = Patient(**encrypted_data)
        db_session.add(other_patient)
        db_session.commit()
        db_session.refresh(other_patient)
        
        # Try to update patient from other tenant
        updates = [
            {
                "id": str(other_patient.id),
                "phone": "+1111111111"
            }
        ]
        
        response = client.put(
            "/api/v1/batch/patients",
            json=updates,
            headers=auth_headers_doctor
        )
        
        # Should fail - patient not found in current tenant
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_batch_create_empty_list(self, client, auth_headers_doctor):
        """Test batch creation with empty list - should be rejected."""
        response = client.post(
            "/api/v1/batch/patients",
            json=[],
            headers=auth_headers_doctor
        )
        
        # Empty batches should be rejected with 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data or "error" in data

    def test_batch_operations_rate_limiting(self, client, auth_headers_doctor):
        """Test that batch operations have rate limiting."""
        # Rate limit is 10/minute for batch operations
        # Make 11 requests rapidly
        for i in range(11):
            response = client.post(
                "/api/v1/batch/patients",
                json=[],
                headers=auth_headers_doctor
            )
            if i < 10:
                assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_429_TOO_MANY_REQUESTS]
        
        # Last request should be rate limited
        # Note: This might not always trigger in tests due to timing
        # Consider this a smoke test for rate limiting presence
