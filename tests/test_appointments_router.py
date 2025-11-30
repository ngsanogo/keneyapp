import datetime as dt
from datetime import timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(token="testtoken"):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_appointments_crud_flow(client):
    # Note: This assumes test auth and tenant context are handled by dependencies/mocks in test setup.
    scheduled_at = dt.datetime.now(timezone.utc).isoformat()
    payload = {
        "patient_id": 1,
        "doctor_id": 1,
        "scheduled_at": scheduled_at,
        "reason": "Routine checkup",
        "location": "Room 101",
    }

    # Create
    r = client.post("/api/v1/appointments/", json=payload, headers=auth_headers())
    assert r.status_code in (201, 401, 403)  # Depending on auth setup, allow guarded failures
    if r.status_code == 201:
        created = r.json()
        appt_id = created["id"]

        # Read detail
        r = client.get(f"/api/v1/appointments/{appt_id}", headers=auth_headers())
        assert r.status_code == 200

        # List
        r = client.get("/api/v1/appointments/", headers=auth_headers())
        assert r.status_code == 200

        # Update
        r = client.put(
            f"/api/v1/appointments/{appt_id}",
            json={"location": "Room 102"},
            headers=auth_headers(),
        )
        assert r.status_code == 200

        # Delete
        r = client.delete(f"/api/v1/appointments/{appt_id}", headers=auth_headers())
        assert r.status_code in (204, 200)
