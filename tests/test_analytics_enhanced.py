"""
Tests for enhanced analytics endpoints with custom date ranges.
"""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.user import User, UserRole


@pytest.fixture
def test_patients(db: Session, test_tenant):
    """Create test patients with various ages."""
    patients = []

    birth_dates = [
        date(2018, 1, 1),  # 5-6 years old
        date(2010, 5, 15),  # 13-14 years old
        date(1995, 8, 20),  # 28-29 years old
        date(1985, 3, 10),  # 38-39 years old
        date(1975, 12, 5),  # 48-49 years old
        date(1960, 7, 25),  # 63-64 years old
    ]

    for i, dob in enumerate(birth_dates):
        patient = Patient(
            tenant_id=test_tenant.id,
            first_name=f"Test{i}",
            last_name=f"Patient{i}",
            date_of_birth=dob,
            gender="male" if i % 2 == 0 else "female",
            email=f"patient{i}@test.com",
            phone=f"123456789{i}",
        )
        db.add(patient)
        patients.append(patient)

    db.commit()
    for p in patients:
        db.refresh(p)
    return patients


@pytest.fixture
def test_doctor(db: Session, test_tenant):
    """Create a test doctor."""
    doctor = User(
        tenant_id=test_tenant.id,
        email="doctor@test.com",
        username="testdoctor",
        hashed_password="hashed",
        full_name="Test Doctor",
        role=UserRole.DOCTOR,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@pytest.fixture
def test_appointments(db: Session, test_tenant, test_patients, test_doctor):
    """Create test appointments with various dates and statuses."""
    appointments = []

    today = datetime.now()
    dates = [
        today - timedelta(days=30),
        today - timedelta(days=15),
        today - timedelta(days=7),
        today - timedelta(days=2),
        today,
    ]

    statuses = [
        AppointmentStatus.COMPLETED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.SCHEDULED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.SCHEDULED,
    ]

    for i, (appt_date, status) in enumerate(zip(dates, statuses)):
        appointment = Appointment(
            tenant_id=test_tenant.id,
            patient_id=test_patients[i % len(test_patients)].id,
            doctor_id=test_doctor.id,
            appointment_date=appt_date,
            status=status,
            reason=f"Test appointment {i}",
        )
        db.add(appointment)
        appointments.append(appointment)

    db.commit()
    for a in appointments:
        db.refresh(a)
    return appointments


@pytest.fixture
def test_prescriptions(db: Session, test_tenant, test_patients, test_doctor):
    """Create test prescriptions."""
    prescriptions = []

    for i in range(3):
        prescription = Prescription(
            tenant_id=test_tenant.id,
            patient_id=test_patients[i].id,
            doctor_id=test_doctor.id,
            medication_name=f"Medication {i}",
            dosage=f"{i+1}mg",
            instructions=f"Take {i+1} times daily",
        )
        db.add(prescription)
        prescriptions.append(prescription)

    db.commit()
    for p in prescriptions:
        db.refresh(p)
    return prescriptions


class TestAnalyticsAPI:
    """Test enhanced analytics API endpoints."""

    def test_get_dashboard_metrics(
        self,
        client: TestClient,
        admin_token,
        test_patients,
        test_appointments,
    ):
        """Test GET /analytics/metrics endpoint."""
        response = client.get(
            "/api/v1/analytics/metrics",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_patients" in data
        assert "appointments_today" in data
        assert "active_doctors" in data
        assert data["total_patients"] >= len(test_patients)

    def test_get_patient_trend(
        self,
        client: TestClient,
        admin_token,
        test_patients,
    ):
        """Test GET /analytics/patient-trend endpoint."""
        response = client.get(
            "/api/v1/analytics/patient-trend?period=30d",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "values" in data
        assert len(data["labels"]) == len(data["values"])
        assert len(data["labels"]) == 31  # 30 days + today

    def test_get_appointment_stats(
        self,
        client: TestClient,
        admin_token,
        test_appointments,
    ):
        """Test GET /analytics/appointments endpoint."""
        response = client.get(
            "/api/v1/analytics/appointments?period=7d",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "completed" in data
        assert "pending" in data
        assert "cancelled" in data
        assert len(data["labels"]) == len(data["completed"])

    def test_get_gender_distribution(
        self,
        client: TestClient,
        admin_token,
        test_patients,
    ):
        """Test GET /analytics/gender-distribution endpoint."""
        response = client.get(
            "/api/v1/analytics/gender-distribution",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "values" in data
        assert len(data["labels"]) == len(data["values"])
        # Should have male and female
        assert len(data["labels"]) >= 2

    def test_get_custom_period_metrics_default(
        self,
        client: TestClient,
        admin_token,
        test_patients,
        test_appointments,
        test_prescriptions,
    ):
        """Test GET /analytics/custom-period with default dates (last 30 days)."""
        response = client.get(
            "/api/v1/analytics/custom-period",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        assert "period_start" in data
        assert "period_end" in data
        assert "total_patients" in data
        assert "new_patients" in data
        assert "total_appointments" in data
        assert "completed_appointments" in data
        assert "cancelled_appointments" in data
        assert "pending_appointments" in data
        assert "total_prescriptions" in data
        assert "unique_doctors_seen" in data

        # Verify counts match test data
        assert data["total_patients"] >= len(test_patients)
        assert data["total_appointments"] >= 0
        assert data["total_prescriptions"] >= 0

    def test_get_custom_period_metrics_with_dates(
        self,
        client: TestClient,
        admin_token,
        test_appointments,
    ):
        """Test GET /analytics/custom-period with specific date range."""
        today = date.today()
        date_from = (today - timedelta(days=7)).isoformat()
        date_to = today.isoformat()

        response = client.get(
            f"/api/v1/analytics/custom-period?date_from={date_from}&date_to={date_to}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["period_start"] == date_from
        assert data["period_end"] == date_to
        assert isinstance(data["total_appointments"], int)

    def test_get_custom_period_metrics_from_date_only(
        self,
        client: TestClient,
        admin_token,
    ):
        """Test GET /analytics/custom-period with only date_from."""
        date_from = (date.today() - timedelta(days=15)).isoformat()

        response = client.get(
            f"/api/v1/analytics/custom-period?date_from={date_from}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == date_from
        # period_end should be today
        assert isinstance(data["total_patients"], int)

    def test_get_custom_period_metrics_to_date_only(
        self,
        client: TestClient,
        admin_token,
    ):
        """Test GET /analytics/custom-period with only date_to."""
        date_to = date.today().isoformat()

        response = client.get(
            f"/api/v1/analytics/custom-period?date_to={date_to}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_end"] == date_to
        # period_start should be 30 days before date_to
        assert isinstance(data["new_patients"], int)

    def test_get_age_distribution(
        self,
        client: TestClient,
        admin_token,
        test_patients,
    ):
        """Test GET /analytics/age-distribution endpoint."""
        response = client.get(
            "/api/v1/analytics/age-distribution",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "values" in data
        assert len(data["labels"]) == 9  # 9 age ranges
        assert "0-10" in data["labels"]
        assert "11-20" in data["labels"]
        assert "81+" in data["labels"]

        # Verify total matches test patients with DOB
        total_in_ranges = sum(data["values"])
        assert total_in_ranges == len(test_patients)

    def test_get_doctor_performance_admin_only(
        self,
        client: TestClient,
        admin_token,
        doctor_token,
        test_appointments,
    ):
        """Test GET /analytics/doctor-performance is admin-only."""
        # Admin should succeed
        response = client.get(
            "/api/v1/analytics/doctor-performance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        # Doctor should be forbidden
        response = client.get(
            "/api/v1/analytics/doctor-performance",
            headers={"Authorization": f"Bearer {doctor_token}"},
        )
        assert response.status_code == 403

    def test_get_doctor_performance_metrics(
        self,
        client: TestClient,
        admin_token,
        test_appointments,
    ):
        """Test GET /analytics/doctor-performance returns correct data."""
        response = client.get(
            "/api/v1/analytics/doctor-performance",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "doctor_names" in data
        assert "appointments_count" in data
        assert "completion_rate" in data
        assert "average_rating" in data

        # All arrays should have same length
        assert len(data["doctor_names"]) == len(data["appointments_count"])
        assert len(data["doctor_names"]) == len(data["completion_rate"])
        assert len(data["doctor_names"]) == len(data["average_rating"])

        # If we have data, verify completion rate is percentage
        if len(data["completion_rate"]) > 0:
            for rate in data["completion_rate"]:
                assert 0 <= rate <= 100

    def test_get_doctor_performance_with_date_range(
        self,
        client: TestClient,
        admin_token,
        test_appointments,
    ):
        """Test GET /analytics/doctor-performance with custom date range."""
        today = date.today()
        date_from = (today - timedelta(days=10)).isoformat()
        date_to = today.isoformat()

        response = client.get(
            f"/api/v1/analytics/doctor-performance?date_from={date_from}&date_to={date_to}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["doctor_names"], list)

    def test_analytics_require_authentication(self, client: TestClient):
        """Test that analytics endpoints require authentication."""
        endpoints = [
            "/api/v1/analytics/metrics",
            "/api/v1/analytics/patient-trend",
            "/api/v1/analytics/appointments",
            "/api/v1/analytics/gender-distribution",
            "/api/v1/analytics/custom-period",
            "/api/v1/analytics/age-distribution",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_analytics_respect_tenant_isolation(
        self,
        client: TestClient,
        admin_token,
        db: Session,
        test_patients,
    ):
        """Test that analytics respect tenant isolation."""
        # This test assumes admin_token is for test_tenant
        # Results should only include data from that tenant
        response = client.get(
            "/api/v1/analytics/metrics",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        # Patient count should match test tenant patients, not include other tenants
        assert data["total_patients"] == len(test_patients)
