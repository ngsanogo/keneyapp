"""Tests for the secured GraphQL API."""

from __future__ import annotations

from datetime import date, datetime, timezone
import uuid
from typing import Dict
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.graphql import schema as graphql_schema
from app.main import app
from app.core.database import Base
from app.core.security import create_access_token, get_password_hash
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Gender, Patient
from app.models.prescription import Prescription
from app.models.tenant import Tenant
from app.models.user import User, UserRole

# Configure in-memory SQLite database shared across the app for tests
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure the GraphQL module uses the testing session factory
graphql_schema.SessionLocal = TestingSessionLocal

client = TestClient(app)


def _reset_database() -> Tenant:
    """Reset the in-memory database and seed a default tenant."""

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as session:
        tenant = Tenant(
            name="Test Tenant",
            slug=f"tenant-{uuid.uuid4().hex[:6]}",
            is_active=True,
            configuration={},
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
        return tenant


def _create_user(tenant: Tenant, role: UserRole = UserRole.ADMIN) -> User:
    """Persist a user for authentication."""

    with TestingSessionLocal() as session:
        username = f"user_{uuid.uuid4().hex[:8]}"
        user = User(
            tenant_id=tenant.id,
            email=f"{username}@example.com",
            username=username,
            full_name="GraphQL Tester",
            role=role,
            hashed_password=get_password_hash("StrongPass123!"),
            is_active=True,
            password_changed_at=datetime.now(timezone.utc),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _auth_headers(user: User) -> Dict[str, str]:
    """Generate Authorization headers for the supplied user."""

    token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role.value,
            "tenant_id": user.tenant_id,
        }
    )
    return {"Authorization": f"Bearer {token}"}


def test_graphql_requires_authentication():
    """Queries without credentials should fail with 401."""

    tenant = _reset_database()
    _create_user(tenant=tenant)

    response = client.post("/graphql", json={"query": "{ hello }"})
    assert response.status_code == 401


def test_graphql_basic_queries_with_auth():
    """Hello and version queries succeed with valid credentials."""

    tenant = _reset_database()
    user = _create_user(tenant=tenant)
    headers = _auth_headers(user)

    hello_response = client.post("/graphql", json={"query": "{ hello }"}, headers=headers)
    assert hello_response.status_code == 200
    assert hello_response.json()["data"]["hello"] == "Hello from KeneyApp GraphQL API!"

    version_response = client.post(
        "/graphql", json={"query": "{ apiVersion }"}, headers=headers
    )
    assert version_response.status_code == 200
    assert version_response.json()["data"]["apiVersion"] == "1.0.0"


def test_graphql_me_and_patients_query():
    """The authenticated user can fetch profile information and tenant patients."""

    tenant = _reset_database()
    user = _create_user(tenant=tenant, role=UserRole.DOCTOR)
    headers = _auth_headers(user)

    with TestingSessionLocal() as session:
        patient = Patient(
            tenant_id=tenant.id,
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1990, 5, 17),
            gender=Gender.FEMALE,
            email="jane.doe@example.com",
            phone="+15551234567",
            address="123 GraphQL Ave",
        )
        session.add(patient)
        session.commit()

    query = """
        query FetchMeAndPatients($limit: Int!) {
            me {
                id
                username
                role
                tenantId
            }
            patients(limit: $limit) {
                id
                firstName
                lastName
                gender
                email
            }
        }
    """

    response = client.post(
        "/graphql",
        json={"query": query, "variables": {"limit": 10}},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()["data"]

    assert payload["me"]["username"] == user.username
    assert payload["me"]["tenantId"] == tenant.id
    assert payload["me"]["role"] == user.role.name

    assert len(payload["patients"]) == 1
    patient_data = payload["patients"][0]
    assert patient_data["firstName"] == "Jane"
    assert patient_data["gender"] == "FEMALE"


def test_graphql_dashboard_and_relationship_queries():
    """GraphQL dashboard stats aggregate recent tenant activity."""

    tenant = _reset_database()
    user = _create_user(tenant=tenant, role=UserRole.ADMIN)
    headers = _auth_headers(user)

    with TestingSessionLocal() as session:
        patient = Patient(
            tenant_id=tenant.id,
            first_name="Alex",
            last_name="Hamilton",
            date_of_birth=date(1985, 3, 12),
            gender=Gender.MALE,
            phone="+15554443333",
        )
        session.add(patient)
        session.flush()

        appointment = Appointment(
            tenant_id=tenant.id,
            patient_id=patient.id,
            doctor_id=user.id,
            appointment_date=datetime.now(timezone.utc),
            status=AppointmentStatus.SCHEDULED,
            reason="Annual check-up",
        )
        session.add(appointment)

        prescription = Prescription(
            tenant_id=tenant.id,
            patient_id=patient.id,
            doctor_id=user.id,
            medication_name="Metformin",
            dosage="500mg",
            frequency="twice daily",
            duration="30 days",
        )
        session.add(prescription)
        session.commit()

    query = """
        query DashboardSnapshot {
            appointments(limit: 5) {
                id
                status
                patientId
            }
            prescriptions(limit: 5) {
                id
                medicationName
            }
            dashboardStats {
                totalPatients
                totalAppointments
                totalPrescriptions
                appointmentsByStatus {
                    scheduled
                }
                recentActivity {
                    patients
                    appointments
                    prescriptions
                }
            }
        }
    """

    response = client.post("/graphql", json={"query": query}, headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data["appointments"]) == 1
    assert data["appointments"][0]["status"] == "SCHEDULED"

    assert len(data["prescriptions"]) == 1
    assert data["prescriptions"][0]["medicationName"] == "Metformin"

    stats = data["dashboardStats"]
    assert stats["totalPatients"] == 1
    assert stats["totalAppointments"] == 1
    assert stats["totalPrescriptions"] == 1
    assert stats["appointmentsByStatus"]["scheduled"] == 1
    assert stats["recentActivity"]["patients"] >= 1


def test_graphql_create_patient_mutation():
    """Users with clinical roles can create patients via GraphQL mutations."""

    tenant = _reset_database()
    user = _create_user(tenant=tenant, role=UserRole.NURSE)
    headers = _auth_headers(user)

    mutation = """
        mutation CreatePatient($input: PatientCreateInput!) {
            createPatient(payload: $input) {
                id
                firstName
                email
            }
        }
    """

    variables = {
        "input": {
            "firstName": "George",
            "lastName": "Washington",
            "dateOfBirth": "1970-07-04",
            "gender": "MALE",
            "phone": "+15553334444",
            "email": "george@example.com",
        }
    }

    response = client.post(
        "/graphql", json={"query": mutation, "variables": variables}, headers=headers
    )

    assert response.status_code == 200
    patient_data = response.json()["data"]["createPatient"]
    assert patient_data["firstName"] == "George"
    assert patient_data["email"] == "george@example.com"

    with TestingSessionLocal() as session:
        patients = session.query(Patient).all()
        assert len(patients) == 1
        assert patients[0].email == "george@example.com"
