"""
Tests for recommendation service and API endpoints
"""

import pytest
from datetime import datetime, timedelta
from app.services.recommendation_service import RecommendationService
from app.models.patient import Patient, Gender
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prescription import Prescription
from app.models.user import User, UserRole


def test_patient_care_recommendations_follow_up(db, test_tenant):
    """Test follow-up appointment recommendation"""
    # Create patient
    patient = Patient(
        tenant_id=test_tenant.id,
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        phone="1234567890",
        date_of_birth=datetime(1980, 1, 1).date(),
        gender=Gender.MALE,
        address="123 Test St",
    )
    db.add(patient)
    db.flush()

    # Create old appointment (6+ months ago)
    doctor = User(
        tenant_id=test_tenant.id,
        username="doctor1",
        email="doctor1@test.com",
        full_name="Dr. Test",
        role=UserRole.DOCTOR,
        hashed_password="hashed",
        is_active=True,
    )
    db.add(doctor)
    db.flush()

    old_appointment = Appointment(
        tenant_id=test_tenant.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=datetime.now() - timedelta(days=200),
        reason="Checkup",
        status=AppointmentStatus.COMPLETED,
    )
    db.add(old_appointment)
    db.commit()

    # Get recommendations
    service = RecommendationService(db)
    recommendations = service.get_patient_care_recommendations(
        patient_id=patient.id, tenant_id=test_tenant.id
    )

    # Should recommend follow-up
    follow_up_rec = next((r for r in recommendations if r["type"] == "follow_up"), None)
    assert follow_up_rec is not None
    assert follow_up_rec["priority"] == "high"
    assert "200" in follow_up_rec["description"]


def test_patient_care_recommendations_prescription_refill(db, test_tenant):
    """Test prescription refill recommendation"""
    # Create patient
    patient = Patient(
        tenant_id=test_tenant.id,
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@test.com",
        phone="0987654321",
        date_of_birth=datetime(1985, 5, 15).date(),
        gender=Gender.FEMALE,
        address="456 Test Ave",
    )
    db.add(patient)
    db.flush()

    # Create prescription expiring soon
    doctor = User(
        tenant_id=test_tenant.id,
        username="doctor2",
        email="doctor2@test.com",
        full_name="Dr. Smith",
        role=UserRole.DOCTOR,
        hashed_password="hashed",
        is_active=True,
    )
    db.add(doctor)
    db.flush()

    # Create a prescription expiring soon (prescribed 30 days ago, duration 35 days = 5 days left)
    from datetime import timezone
    prescribed_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    prescription = Prescription(
        tenant_id=test_tenant.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        medication_name="Lisinopril",
        dosage="10mg",
        frequency="Once daily",
        duration="35 days",
        instructions="Blood pressure medication",
        prescribed_date=prescribed_date,
    )
    db.add(prescription)
    db.commit()

    # Get recommendations
    service = RecommendationService(db)
    recommendations = service.get_patient_care_recommendations(
        patient_id=patient.id, tenant_id=test_tenant.id
    )

    # Should recommend prescription refill
    refill_rec = next(
        (r for r in recommendations if r["type"] == "prescription_refill"), None
    )
    assert refill_rec is not None
    assert refill_rec["priority"] == "medium"
    assert "Lisinopril" in refill_rec["description"]


def test_patient_care_recommendations_missing_data(db, test_tenant):
    """Test data quality recommendations for missing patient information"""
    # Create patient with missing data
    patient = Patient(
        tenant_id=test_tenant.id,
        first_name="Bob",
        last_name="Smith",
        email="bob.smith@test.com",
        phone="5555555555",
        date_of_birth=datetime(1990, 3, 20).date(),
        gender=Gender.MALE,
        address="789 Test Blvd",
        allergies="",  # Missing
        emergency_contact="",  # Missing
    )
    db.add(patient)
    db.commit()

    # Get recommendations
    service = RecommendationService(db)
    recommendations = service.get_patient_care_recommendations(
        patient_id=patient.id, tenant_id=test_tenant.id
    )

    # Should recommend updating both fields
    data_quality_recs = [r for r in recommendations if r["type"] == "data_quality"]
    assert len(data_quality_recs) >= 2

    # Check for allergy recommendation
    allergy_rec = next(
        (r for r in data_quality_recs if r["metadata"].get("field") == "allergies"),
        None,
    )
    assert allergy_rec is not None

    # Check for emergency contact recommendation
    emergency_rec = next(
        (
            r
            for r in data_quality_recs
            if r["metadata"].get("field") == "emergency_contact"
        ),
        None,
    )
    assert emergency_rec is not None
    assert emergency_rec["priority"] == "medium"


def test_appointment_slot_recommendations(db, test_tenant):
    """Test appointment slot recommendation generation"""
    # Create doctor
    doctor = User(
        tenant_id=test_tenant.id,
        username="doctor3",
        email="doctor3@test.com",
        full_name="Dr. Johnson",
        role=UserRole.DOCTOR,
        hashed_password="hashed",
        is_active=True,
    )
    db.add(doctor)
    db.flush()

    # Create patient for appointment
    patient = Patient(
        tenant_id=test_tenant.id,
        first_name="Test",
        last_name="Patient",
        email="test.patient@test.com",
        phone="1111111111",
        date_of_birth=datetime(1975, 7, 10).date(),
        gender=Gender.MALE,
        address="321 Test Ln",
    )
    db.add(patient)
    db.flush()

    # Create appointment at 10 AM
    target_date = datetime.now() + timedelta(days=1)
    existing_appointment = Appointment(
        tenant_id=test_tenant.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=target_date.replace(hour=10, minute=0, second=0),
        reason="Consultation",
        status=AppointmentStatus.SCHEDULED,
    )
    db.add(existing_appointment)
    db.commit()

    # Get slot recommendations
    service = RecommendationService(db)
    recommendations = service.get_appointment_slot_recommendations(
        doctor_id=doctor.id, date=target_date, tenant_id=test_tenant.id
    )

    # Should have available slots
    assert len(recommendations) > 0

    # 10 AM should not be available
    slot_10am = next((r for r in recommendations if r["time"] == "10:00"), None)
    assert slot_10am is None or not slot_10am["available"]

    # Other morning slots should be available
    available_slots = [r for r in recommendations if r["available"]]
    assert len(available_slots) > 0


def test_medication_interaction_warnings(db, test_tenant):
    """Test medication interaction checking"""
    # Create patient
    patient = Patient(
        tenant_id=test_tenant.id,
        first_name="Mary",
        last_name="Johnson",
        email="mary.j@test.com",
        phone="2222222222",
        date_of_birth=datetime(1982, 9, 25).date(),
        gender=Gender.FEMALE,
        address="654 Test Ct",
    )
    db.add(patient)
    db.flush()

    # Create doctor
    doctor = User(
        tenant_id=test_tenant.id,
        username="doctor4",
        email="doctor4@test.com",
        full_name="Dr. Williams",
        role=UserRole.DOCTOR,
        hashed_password="hashed",
        is_active=True,
    )
    db.add(doctor)
    db.flush()

    # Add existing prescription (Warfarin)
    prescription = Prescription(
        tenant_id=test_tenant.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        medication_name="Warfarin",
        dosage="5mg",
        frequency="Once daily",
        duration="90 days",
        instructions="Anticoagulant",
    )
    db.add(prescription)
    db.commit()

    # Check for interactions with Aspirin
    service = RecommendationService(db)
    warnings = service.get_medication_interaction_warnings(
        patient_id=patient.id,
        new_medication="Aspirin",
        tenant_id=test_tenant.id,
    )

    # Should warn about Warfarin-Aspirin interaction
    assert len(warnings) > 0
    warning = warnings[0]
    assert warning["severity"] == "high"
    assert "Warfarin" in warning["description"] or "warfarin" in warning["description"]
    assert "Aspirin" in warning["description"] or "aspirin" in warning["description"]


def test_resource_optimization_recommendations_workload(db, test_tenant):
    """Test workload balancing recommendations"""
    # Create multiple doctors
    doctor1 = User(
        tenant_id=test_tenant.id,
        username="doctor_busy",
        email="busy@test.com",
        full_name="Dr. Busy",
        role=UserRole.DOCTOR,
        hashed_password="hashed",
        is_active=True,
    )
    doctor2 = User(
        tenant_id=test_tenant.id,
        username="doctor_free",
        email="free@test.com",
        full_name="Dr. Free",
        role=UserRole.DOCTOR,
        hashed_password="hashed",
        is_active=True,
    )
    db.add_all([doctor1, doctor2])
    db.flush()

    # Create patient
    patient = Patient(
        tenant_id=test_tenant.id,
        first_name="Load",
        last_name="Test",
        email="load@test.com",
        phone="3333333333",
        date_of_birth=datetime(1988, 11, 5).date(),
        gender=Gender.MALE,
        address="987 Test Dr",
    )
    db.add(patient)
    db.flush()

    # Give doctor1 many appointments
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    for i in range(15):
        appointment = Appointment(
            tenant_id=test_tenant.id,
            patient_id=patient.id,
            doctor_id=doctor1.id,
            appointment_date=week_start + timedelta(days=i % 5, hours=9 + i % 8),
            reason="Checkup",
            status=AppointmentStatus.SCHEDULED,
        )
        db.add(appointment)

    # Give doctor2 few appointments
    for i in range(3):
        appointment = Appointment(
            tenant_id=test_tenant.id,
            patient_id=patient.id,
            doctor_id=doctor2.id,
            appointment_date=week_start + timedelta(days=i, hours=10),
            reason="Checkup",
            status=AppointmentStatus.SCHEDULED,
        )
        db.add(appointment)

    db.commit()

    # Get optimization recommendations
    service = RecommendationService(db)
    recommendations = service.get_resource_optimization_recommendations(
        tenant_id=test_tenant.id
    )

    # Should recommend workload balancing for busy doctor
    workload_rec = next(
        (r for r in recommendations if r["type"] == "workload_balance"), None
    )
    assert workload_rec is not None
    assert workload_rec["priority"] in ["medium", "high"]


@pytest.mark.api
def test_patient_care_recommendations_api(client, test_tenant, auth_headers_doctor):
    """Test patient care recommendations API endpoint"""
    # Create test patient
    patient_data = {
        "first_name": "API",
        "last_name": "Test",
        "email": "api.test@example.com",
        "phone": "4444444444",
        "date_of_birth": "1992-06-15",
        "gender": "male",
        "address": "111 API St",
    }
    patient_response = client.post(
        "/api/v1/patients/",
        json=patient_data,
        headers=auth_headers_doctor,
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    # Get recommendations
    response = client.get(
        f"/api/v1/recommendations/patient/{patient_id}/care",
        headers=auth_headers_doctor,
    )

    assert response.status_code == 200
    recommendations = response.json()
    assert isinstance(recommendations, list)


@pytest.mark.api
def test_medication_interaction_api(client, test_tenant, auth_headers_doctor):
    """Test medication interaction check API endpoint"""
    # Create test patient
    patient_data = {
        "first_name": "Med",
        "last_name": "Test",
        "email": "med.test@example.com",
        "phone": "5555555555",
        "date_of_birth": "1987-04-20",
        "gender": "female",
        "address": "222 Med Ave",
    }
    patient_response = client.post(
        "/api/v1/patients/",
        json=patient_data,
        headers=auth_headers_doctor,
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    # Check interactions
    response = client.get(
        f"/api/v1/recommendations/medications/interactions/{patient_id}",
        params={"new_medication": "Ibuprofen"},
        headers=auth_headers_doctor,
    )

    assert response.status_code == 200
    warnings = response.json()
    assert isinstance(warnings, list)
