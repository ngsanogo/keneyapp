"""
Tests for patient management endpoints
"""
import pytest
from fastapi import status
from datetime import date
from app.models.patient import Patient


class TestPatients:
    """Test patient management functionality"""
    
    def test_create_patient(self, client, auth_headers):
        """Test creating a new patient"""
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "address": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "zip_code": "12345",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "+1234567891",
            "medical_history": "No known allergies",
            "allergies": "None"
        }
        
        response = client.post("/api/patients", json=patient_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@example.com"
        assert "id" in data
    
    def test_get_patients(self, client, auth_headers):
        """Test getting list of patients"""
        response = client.get("/api/patients", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_patient_by_id(self, client, auth_headers, db_session):
        """Test getting a specific patient by ID"""
        # Create a patient first
        patient = Patient(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="+1234567890",
            date_of_birth="1985-05-15",
            gender="female"
        )
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
        
        response = client.get(f"/api/patients/{patient.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
    
    def test_update_patient(self, client, auth_headers, db_session):
        """Test updating a patient"""
        # Create a patient first
        patient = Patient(
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@example.com",
            phone="+1234567890",
            date_of_birth="1975-03-20",
            gender="male"
        )
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
        
        update_data = {
            "first_name": "Robert",
            "last_name": "Johnson",
            "phone": "+1234567899"
        }
        
        response = client.put(f"/api/patients/{patient.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Robert"
        assert data["phone"] == "+1234567899"
    
    def test_delete_patient(self, client, auth_headers, db_session):
        """Test deleting a patient"""
        # Create a patient first
        patient = Patient(
            first_name="Alice",
            last_name="Brown",
            email="alice.brown@example.com",
            phone="+1234567890",
            date_of_birth="1992-08-10",
            gender="female"
        )
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
        
        response = client.delete(f"/api/patients/{patient.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify patient is deleted
        get_response = client.get(f"/api/patients/{patient.id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_patient_unauthorized(self, client):
        """Test creating patient without authentication"""
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com"
        }
        
        response = client.post("/api/patients", json=patient_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
