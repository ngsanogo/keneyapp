"""
Tests for advanced patient search functionality
"""

import pytest
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.patient import Patient


@pytest.fixture
def sample_patients(db: Session, test_tenant):
    """Create sample patients for search testing"""
    patients = [
        Patient(
            tenant_id=test_tenant.id,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 5, 15),
            gender="male",
            email="john.doe@test.com",
            phone="1234567890",
            address="123 Main St, Paris, France",
            allergies="Peanuts",
            medical_history="Hypertension",
        ),
        Patient(
            tenant_id=test_tenant.id,
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1995, 8, 20),
            gender="female",
            email="jane.smith@test.com",
            phone="0987654321",
            address="456 Oak Ave, Lyon, France",
            allergies=None,
            medical_history=None,
        ),
        Patient(
            tenant_id=test_tenant.id,
            first_name="Bob",
            last_name="Johnson",
            date_of_birth=date(1970, 3, 10),
            gender="male",
            email="bob.johnson@test.com",
            phone="5555555555",
            address="789 Elm St, Marseille, France",
            allergies="Penicillin",
            medical_history=None,
        ),
    ]

    for patient in patients:
        db.add(patient)
    db.commit()
    for patient in patients:
        db.refresh(patient)

    return patients


def test_advanced_search_text_query(client: TestClient, auth_headers_doctor, sample_patients):
    """Test text search across multiple fields"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={"search": "John"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    assert any("john" in item["first_name"].lower() for item in data["items"])


def test_advanced_search_gender_filter(client: TestClient, auth_headers_doctor, sample_patients):
    """Test gender filtering"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={"gender": "male"},
    )

    assert response.status_code == 200
    data = response.json()

    # All results should be male
    for item in data["items"]:
        assert item["gender"] == "male"


def test_advanced_search_age_range(client: TestClient, auth_headers_doctor, sample_patients):
    """Test age range filtering"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={
            "min_age": 40,
            "max_age": 60,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Calculate ages and verify range
    current_year = datetime.now().year
    for item in data["items"]:
        dob = datetime.fromisoformat(item["date_of_birth"]).date()
        age = current_year - dob.year
        assert 40 <= age <= 60


def test_advanced_search_location(client: TestClient, auth_headers_doctor, sample_patients):
    """Test location-based search"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={"city": "Paris"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    # Note: Address field contains full address, so city search uses ILIKE


def test_advanced_search_medical_flags(client: TestClient, auth_headers_doctor, sample_patients):
    """Test medical history and allergy flags"""
    # Search for patients with allergies
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={"has_allergies": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # Search for patients with medical history
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={"has_medical_history": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_advanced_search_date_range(client: TestClient, auth_headers_doctor, sample_patients):
    """Test created_at date range filtering"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={
            "created_from": yesterday.isoformat(),
            "created_to": today.isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    # Should return patients created in the range


def test_advanced_search_sorting(client: TestClient, auth_headers_doctor, sample_patients):
    """Test custom sorting"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={
            "sort_by": "first_name",
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify ascending order
    names = [item["first_name"] for item in data["items"]]
    assert names == sorted(names)


def test_advanced_search_pagination(client: TestClient, auth_headers_doctor, sample_patients):
    """Test pagination parameters"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={
            "page": 1,
            "page_size": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) <= 2


def test_advanced_search_combined_filters(client: TestClient, auth_headers_doctor, sample_patients):
    """Test multiple filters combined"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={
            "gender": "male",
            "has_allergies": True,
            "min_age": 30,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # All results should match all criteria
    current_year = datetime.now().year
    for item in data["items"]:
        assert item["gender"] == "male"
        dob = datetime.fromisoformat(item["date_of_birth"]).date()
        age = current_year - dob.year
        assert age >= 30


def test_advanced_search_empty_results(client: TestClient, auth_headers_doctor, sample_patients):
    """Test search with no matching results"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        headers=auth_headers_doctor,
        json={
            "search": "NonexistentPatient12345",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []


def test_advanced_search_requires_authentication(client: TestClient):
    """Test that endpoint requires authentication"""
    response = client.post(
        "/api/v1/patients/search/advanced",
        json={"search": "test"},
    )

    assert response.status_code == 401
