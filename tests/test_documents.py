"""
Integration tests for the Documents API: upload, list, get, download, update, delete, and stats.
Covers both router handlers and document_service happy paths using the in-memory DB and temp upload dir.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_active_user
from app.main import app
from app.models.medical_document import DocumentType
from app.models.patient import Gender, Patient
from app.models.tenant import Tenant
from app.models.user import User, UserRole


@pytest.mark.unit
@pytest.mark.api
def test_documents_full_flow(
    client: TestClient,
    db,
    sample_pdf_bytes: bytes,
):
    # Arrange: create tenant, doctor user, and patient matching current models
    tenant = Tenant(
        name="Acme Health",
        slug="acme",
        is_active=True,
        contact_email="ops@acme.tld",
        configuration={},
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    doctor = User(
        email="doctor@test.com",
        username="doctor_smith",
        full_name="John Smith",
        role=UserRole.DOCTOR,
        tenant_id=tenant.id,
        hashed_password="not-used-in-tests",
        is_active=True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    patient = Patient(
        tenant_id=tenant.id,
        first_name="Alice",
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
        gender=Gender.FEMALE,
        email="alice@example.com",
        phone="+123456789",
        address="1 Clinic Way",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # Override auth dependency to return our doctor
    def _override_user():
        return doctor

    app.dependency_overrides[get_current_active_user] = _override_user

    # 1) Upload a PDF document
    files = {
        "file": ("lab_result.pdf", sample_pdf_bytes, "application/pdf"),
    }
    data = {
        "patient_id": str(patient.id),
        "document_type": DocumentType.CONSULTATION_NOTE.value,
        "description": "Initial consultation notes",
        "tags": json.dumps(["urgent", "extern"]),
        "is_sensitive": "true",
    }

    r = client.post("/api/v1/documents/upload", files=files, data=data)
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["patient_id"] == patient.id
    assert doc["document_type"] == DocumentType.CONSULTATION_NOTE.value
    doc_id = doc["id"]

    # 2) List patient documents
    r = client.get(f"/api/v1/documents/patient/{patient.id}?limit=10")
    assert r.status_code == 200
    docs = r.json()
    assert any(d["id"] == doc_id for d in docs)

    # 3) Get document metadata
    r = client.get(f"/api/v1/documents/{doc_id}")
    assert r.status_code == 200
    got = r.json()
    assert got["id"] == doc_id

    # 4) Download file
    r = client.get(f"/api/v1/documents/{doc_id}/download")
    assert r.status_code == 200
    assert r.content  # file bytes should be returned

    # 5) Update metadata (allowed for Doctor)
    patch_body = {
        "description": "Updated description",
        "tags": ["updated", "review"],
    }
    r = client.patch(f"/api/v1/documents/{doc_id}", json=patch_body)
    assert r.status_code == 200, r.text
    patched = r.json()
    assert patched["description"] == "Updated description"

    # 6) Stats
    r = client.get(f"/api/v1/documents/stats?patient_id={patient.id}")
    assert r.status_code == 200
    stats = r.json()
    assert stats["total_documents"] >= 1
    assert stats["by_type"].get(DocumentType.CONSULTATION_NOTE.value, 0) >= 1

    # 7) Delete
    r = client.delete(f"/api/v1/documents/{doc_id}")
    assert r.status_code == 204

    # 8) Get after delete should 404
    r = client.get(f"/api/v1/documents/{doc_id}")
    assert r.status_code == 404

    # Cleanup auth override
    app.dependency_overrides.pop(get_current_active_user, None)
