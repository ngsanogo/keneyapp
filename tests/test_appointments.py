"""
Tests for appointment management endpoints
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, date
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.user import User, UserRole
from tests.conftest import parse_date_string


class TestAppointments:
    """Test appointment management functionality"""
    
    def test_create_appointment(self, client, auth_headers, db_session):
        """Test creating a new appointment"""
        # Create a patient first
        patient = Patient(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            date_of_birth=parse_date_string("1990-01-01"),
            gender="male"
        )
        db_session.add(patient)
        db_session.commit()
        db_session.refresh(patient)
        
        # Create a doctor
        doctor = User(
            email="doctor@test.com",
            username="doctor",
            hashed_password="hashed_password",
            full_name="Test Doctor",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True
        )
        db_session.add(doctor)
        db_session.commit()
        db_session.refresh(doctor)
        
        appointment_data = {
            "patient_id": patient.id,
            "doctor_id": doctor.id,
            "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 30,
            "notes": "Regular checkup",
            "status": "scheduled"
        }
        
        response = client.post("/api/appointments", json=appointment_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["patient_id"] == patient.id
        assert data["doctor_id"] == doctor.id
        assert data["status"] == "scheduled"
        assert "id" in data
    
    def test_get_appointments(self, client, auth_headers):
        """Test getting list of appointments"""
        response = client.get("/api/appointments", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_appointment_by_id(self, client, auth_headers, db_session):
        """Test getting a specific appointment by ID"""
        # Create test data
        patient = Patient(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            phone="+1234567890",
            date_of_birth=parse_date_string("1985-05-15"),
            gender="female"
        )
        db_session.add(patient)
        
        doctor = User(
            email="doctor2@test.com",
            username="doctor2",
            hashed_password="hashed_password",
            full_name="Test Doctor 2",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True
        )
        db_session.add(doctor)
        db_session.commit()
        db_session.refresh(patient)
        db_session.refresh(doctor)
        
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=datetime.now() + timedelta(days=1),
            duration_minutes=30,
            notes="Test appointment",
            status=AppointmentStatus.SCHEDULED
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        response = client.get(f"/api/appointments/{appointment.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["patient_id"] == patient.id
        assert data["doctor_id"] == doctor.id
        assert data["status"] == "scheduled"
    
    def test_update_appointment_status(self, client, auth_headers, db_session):
        """Test updating appointment status"""
        # Create test data
        patient = Patient(
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@example.com",
            phone="+1234567890",
            date_of_birth=parse_date_string("1975-03-20"),
            gender="male"
        )
        db_session.add(patient)
        
        doctor = User(
            email="doctor3@test.com",
            username="doctor3",
            hashed_password="hashed_password",
            full_name="Test Doctor 3",
            role=UserRole.DOCTOR,
            is_active=True,
            is_verified=True
        )
        db_session.add(doctor)
        db_session.commit()
        db_session.refresh(patient)
        db_session.refresh(doctor)
        
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_date=datetime.now() + timedelta(days=1),
            duration_minutes=30,
            notes="Test appointment",
            status=AppointmentStatus.SCHEDULED
        )
        db_session.add(appointment)
        db_session.commit()
        db_session.refresh(appointment)
        
        update_data = {
            "status": "confirmed",
            "notes": "Appointment confirmed"
        }
        
        response = client.put(f"/api/appointments/{appointment.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["notes"] == "Appointment confirmed"
    
    def test_create_appointment_unauthorized(self, client):
        """Test creating appointment without authentication"""
        appointment_data = {
            "patient_id": 1,
            "doctor_id": 1,
            "appointment_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 30
        }
        
        response = client.post("/api/appointments", json=appointment_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
