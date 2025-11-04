"""Integration tests for DMI FHIR extensions: Observation, Condition, Procedure endpoints."""

from datetime import datetime, date, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.patient import Patient
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.medical_code import Observation, Condition, Procedure
from app.core.security import get_password_hash, create_access_token


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def db():
    """Create test database session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Clinic",
        slug="test-clinic",
        is_active=True,
        configuration={},
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def doctor(db, tenant):
    """Create a doctor user."""
    doctor = User(
        tenant_id=tenant.id,
        email="doctor@test.com",
        username="doctor",
        hashed_password=get_password_hash("password"),
        first_name="Dr",
        last_name="Smith",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@pytest.fixture
def auth_headers(doctor):
    """Generate auth headers for a doctor."""
    token = create_access_token(
        data={"sub": doctor.email, "tenant_id": doctor.tenant_id, "role": doctor.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def patient(db, tenant):
    """Create a test patient."""
    patient = Patient(
        tenant_id=tenant.id,
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1980, 1, 15),
        gender="male",
        email="john@test.com",
        phone="+15551234567",
        address="123 Main St",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


class TestObservationFHIR:
    """Test FHIR Observation endpoints."""

    def test_get_observation(self, db, tenant, patient, doctor, auth_headers):
        """Test GET /fhir/Observation/{id}."""
        obs = Observation(
            tenant_id=tenant.id,
            patient_id=patient.id,
            status="final",
            loinc_code="8480-6",
            loinc_display="Systolic blood pressure",
            value_quantity="120",
            value_unit="mmHg",
            effective_datetime=datetime.now(timezone.utc),
        )
        db.add(obs)
        db.commit()
        db.refresh(obs)

        response = client.get(f"/api/v1/fhir/Observation/{obs.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Observation"
        assert data["id"] == str(obs.id)
        assert data["code"]["coding"][0]["code"] == "8480-6"
        assert "ETag" in response.headers

    def test_search_observations(self, db, tenant, patient, doctor, auth_headers):
        """Test GET /fhir/Observation with search params."""
        obs1 = Observation(
            tenant_id=tenant.id,
            patient_id=patient.id,
            status="final",
            loinc_code="8480-6",
            loinc_display="Systolic blood pressure",
            value_quantity="120",
            value_unit="mmHg",
            effective_datetime=datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc),
        )
        obs2 = Observation(
            tenant_id=tenant.id,
            patient_id=patient.id,
            status="preliminary",
            loinc_code="2339-0",
            loinc_display="Glucose",
            value_quantity="95",
            value_unit="mg/dL",
            effective_datetime=datetime(2024, 1, 16, 10, 0, tzinfo=timezone.utc),
        )
        db.add_all([obs1, obs2])
        db.commit()

        # Search by patient
        response = client.get(
            f"/api/v1/fhir/Observation?patient={patient.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Bundle"
        assert data["type"] == "searchset"
        assert data["total"] == 2
        assert len(data["entry"]) == 2
        assert "link" in data  # HATEOAS paging links

        # Search by code
        response = client.get(
            "/api/v1/fhir/Observation?code=8480-6", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["entry"][0]["resource"]["code"]["coding"][0]["code"] == "8480-6"

    def test_observation_not_found(self, auth_headers):
        """Test 404 returns FHIR OperationOutcome."""
        response = client.get("/api/v1/fhir/Observation/99999", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert data["resourceType"] == "OperationOutcome"
        assert data["issue"][0]["code"] == "not-found"


class TestConditionFHIR:
    """Test FHIR Condition endpoints."""

    def test_get_condition(self, db, tenant, patient, doctor, auth_headers):
        """Test GET /fhir/Condition/{id}."""
        condition = Condition(
            tenant_id=tenant.id,
            patient_id=patient.id,
            clinical_status="active",
            verification_status="confirmed",
            icd11_code="5A11",
            icd11_display="Type 2 diabetes mellitus",
            onset_date=datetime(2022, 1, 1, tzinfo=timezone.utc),
            recorded_date=datetime.now(timezone.utc),
        )
        db.add(condition)
        db.commit()
        db.refresh(condition)

        response = client.get(
            f"/api/v1/fhir/Condition/{condition.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Condition"
        assert data["id"] == str(condition.id)
        assert data["code"]["coding"][0]["code"] == "5A11"
        assert "ETag" in response.headers

    def test_search_conditions(self, db, tenant, patient, doctor, auth_headers):
        """Test GET /fhir/Condition with search params."""
        cond1 = Condition(
            tenant_id=tenant.id,
            patient_id=patient.id,
            clinical_status="active",
            verification_status="confirmed",
            icd11_code="5A11",
            icd11_display="Type 2 diabetes mellitus",
            recorded_date=datetime.now(timezone.utc),
        )
        cond2 = Condition(
            tenant_id=tenant.id,
            patient_id=patient.id,
            clinical_status="resolved",
            verification_status="confirmed",
            snomed_code="54150009",
            snomed_display="Upper respiratory infection",
            recorded_date=datetime.now(timezone.utc),
        )
        db.add_all([cond1, cond2])
        db.commit()

        # Search by patient
        response = client.get(
            f"/api/v1/fhir/Condition?patient={patient.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

        # Search by clinical status
        response = client.get(
            "/api/v1/fhir/Condition?clinical-status=active", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


class TestProcedureFHIR:
    """Test FHIR Procedure endpoints."""

    def test_get_procedure(self, db, tenant, patient, doctor, auth_headers):
        """Test GET /fhir/Procedure/{id}."""
        procedure = Procedure(
            tenant_id=tenant.id,
            patient_id=patient.id,
            status="completed",
            cpt_code="99213",
            cpt_display="Office visit",
            category="diagnostic",
            performed_datetime=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            performed_by_id=doctor.id,
        )
        db.add(procedure)
        db.commit()
        db.refresh(procedure)

        response = client.get(
            f"/api/v1/fhir/Procedure/{procedure.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resourceType"] == "Procedure"
        assert data["id"] == str(procedure.id)
        assert data["code"]["coding"][0]["code"] == "99213"

    def test_search_procedures(self, db, tenant, patient, doctor, auth_headers):
        """Test GET /fhir/Procedure with search params."""
        proc = Procedure(
            tenant_id=tenant.id,
            patient_id=patient.id,
            status="completed",
            cpt_code="99213",
            cpt_display="Office visit",
            performed_datetime=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
            performed_by_id=doctor.id,
        )
        db.add(proc)
        db.commit()

        # Search by patient
        response = client.get(
            f"/api/v1/fhir/Procedure?patient={patient.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        # Search by code
        response = client.get("/api/v1/fhir/Procedure?code=99213", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


class TestFHIRPagination:
    """Test FHIR search pagination and HATEOAS links."""

    def test_pagination_links(self, db, tenant, patient, doctor, auth_headers):
        """Test that bundle includes correct paging links."""
        # Create 25 observations (more than default page size of 20)
        for i in range(25):
            obs = Observation(
                tenant_id=tenant.id,
                patient_id=patient.id,
                status="final",
                loinc_code=f"CODE-{i}",
                loinc_display=f"Test {i}",
                value_quantity=str(100 + i),
                value_unit="unit",
                effective_datetime=datetime.now(timezone.utc),
            )
            db.add(obs)
        db.commit()

        # Get first page
        response = client.get(
            f"/api/v1/fhir/Observation?patient={patient.id}&_count=10&_page=1",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["entry"]) == 10

        # Check links
        links = {link["relation"]: link["url"] for link in data["link"]}
        assert "self" in links
        assert "first" in links
        assert "next" in links
        assert "last" in links
        assert "_page=2" in links["next"]
        assert "_page=3" in links["last"]
