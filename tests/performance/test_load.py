"""
Performance and Load Testing for KeneyApp using Locust
========================================================

This module defines baseline performance tests for critical API endpoints.
These tests establish performance benchmarks and validate system behavior under load.

Target Performance Metrics:
- Patients endpoint: 100 req/s with <500ms p95 latency
- Messages endpoint: 50 req/s with <300ms p95 latency
- Documents upload: 20 uploads/s with <2s p95 latency

Usage:
    # Run with web UI (recommended for analysis):
    locust -f tests/performance/test_load.py --host=http://localhost:8000

    # Run headless with specific parameters:
    locust -f tests/performance/test_load.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 2m --headless

    # Run with custom test scenarios:
    locust -f tests/performance/test_load.py --host=http://localhost:8000 \
           --tags read_heavy  # Focus on read operations
    locust -f tests/performance/test_load.py --host=http://localhost:8000 \
           --tags write_heavy  # Focus on write operations

Requirements:
    pip install locust

Notes:
    - Requires running backend instance (make dev or docker-compose up)
    - Tests use bootstrap admin credentials (admin/admin123) by default
    - For production testing, update authentication and use valid credentials
    - Configure BASE_URL environment variable for different targets
"""

import json
import os
import random
import time
from typing import Any, Dict, List, Optional

from locust import HttpUser, TaskSet, between, tag, task


class AuthenticatedTaskSet(TaskSet):
    """Base TaskSet with authentication support."""

    def on_start(self):
        """Called when a simulated user starts executing tasks."""
        self.access_token = None
        self.tenant_id = "1"  # Default tenant
        self.authenticate()

    def authenticate(self) -> bool:
        """
        Authenticate and obtain JWT access token.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json={
                    "username": "admin",
                    "password": "admin123",
                },
                name="/api/v1/auth/login",
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                return True
            else:
                print(f"Authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }


class PatientTasks(AuthenticatedTaskSet):
    """
    Patient management tasks - simulates typical patient operations.

    Weight distribution:
    - 70% list/read operations (most common in healthcare)
    - 20% create operations
    - 10% update operations
    """

    @task(50)
    @tag("read_heavy", "patients")
    def list_patients(self):
        """List patients with pagination (most frequent operation)."""
        params = {
            "skip": random.randint(0, 20),
            "limit": random.choice([10, 20, 50]),
        }
        self.client.get(
            "/api/v1/patients/",
            headers=self.get_headers(),
            params=params,
            name="/api/v1/patients/ (list)",
        )

    @task(20)
    @tag("read_heavy", "patients")
    def get_patient_detail(self):
        """Get specific patient details."""
        # In real scenario, maintain a pool of valid patient IDs
        patient_id = random.randint(1, 100)
        self.client.get(
            f"/api/v1/patients/{patient_id}",
            headers=self.get_headers(),
            name="/api/v1/patients/{id} (detail)",
            catch_response=True,
        )

    @task(15)
    @tag("read_heavy", "patients")
    def search_patients(self):
        """Search patients by name or other criteria."""
        search_terms = ["Jean", "Marie", "Pierre", "Sophie", "Dupont", "Martin"]
        params = {"search": random.choice(search_terms)}
        self.client.get(
            "/api/v1/patients/search",
            headers=self.get_headers(),
            params=params,
            name="/api/v1/patients/search",
        )

    @task(10)
    @tag("write_heavy", "patients")
    def create_patient(self):
        """Create a new patient (simulates admission)."""
        patient_data = {
            "first_name": f"Patient{random.randint(1000, 9999)}",
            "last_name": f"Test{random.randint(1000, 9999)}",
            "date_of_birth": "1990-01-01",
            "gender": random.choice(["M", "F", "O"]),
            "phone": f"+33600{random.randint(100000, 999999)}",
            "email": f"patient{random.randint(1000, 9999)}@test.com",
            "address": "123 Test Street",
            "medical_history": "Test medical history",
            "allergies": "None",
            "blood_group": random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]),
        }
        self.client.post(
            "/api/v1/patients/",
            headers=self.get_headers(),
            json=patient_data,
            name="/api/v1/patients/ (create)",
        )

    @task(5)
    @tag("write_heavy", "patients")
    def update_patient(self):
        """Update patient information."""
        patient_id = random.randint(1, 100)
        update_data = {
            "phone": f"+33600{random.randint(100000, 999999)}",
            "address": f"{random.randint(1, 999)} Updated Street",
        }
        self.client.put(
            f"/api/v1/patients/{patient_id}",
            headers=self.get_headers(),
            json=update_data,
            name="/api/v1/patients/{id} (update)",
            catch_response=True,
        )


class MessageTasks(AuthenticatedTaskSet):
    """
    Messaging tasks - simulates secure patient-doctor communication (v3.0 feature).

    Weight distribution:
    - 60% read operations (checking messages)
    - 30% send operations (replying/new messages)
    - 10% thread management
    """

    @task(40)
    @tag("read_heavy", "messages")
    def list_messages(self):
        """List received messages (most common operation)."""
        params = {
            "skip": 0,
            "limit": 20,
        }
        self.client.get(
            "/api/v1/messages/",
            headers=self.get_headers(),
            params=params,
            name="/api/v1/messages/ (list)",
        )

    @task(20)
    @tag("read_heavy", "messages")
    def get_message_detail(self):
        """Read specific message details."""
        message_id = random.randint(1, 50)
        self.client.get(
            f"/api/v1/messages/{message_id}",
            headers=self.get_headers(),
            name="/api/v1/messages/{id} (detail)",
            catch_response=True,
        )

    @task(25)
    @tag("write_heavy", "messages")
    def send_message(self):
        """Send a new message (doctor-patient communication)."""
        message_data = {
            "recipient_id": random.randint(1, 50),
            "subject": f"Test Message {random.randint(1000, 9999)}",
            "content": "This is a test message for performance testing.",
            "priority": random.choice(["low", "normal", "high"]),
        }
        self.client.post(
            "/api/v1/messages/",
            headers=self.get_headers(),
            json=message_data,
            name="/api/v1/messages/ (send)",
        )

    @task(10)
    @tag("read_heavy", "messages")
    def list_threads(self):
        """List message threads."""
        self.client.get(
            "/api/v1/messages/threads",
            headers=self.get_headers(),
            name="/api/v1/messages/threads (list)",
        )

    @task(5)
    @tag("write_heavy", "messages")
    def mark_as_read(self):
        """Mark message as read."""
        message_id = random.randint(1, 50)
        self.client.put(
            f"/api/v1/messages/{message_id}/read",
            headers=self.get_headers(),
            name="/api/v1/messages/{id}/read",
            catch_response=True,
        )


class DocumentTasks(AuthenticatedTaskSet):
    """
    Document management tasks - simulates medical document operations (v3.0 feature).

    Weight distribution:
    - 50% list/view operations
    - 30% upload operations
    - 20% metadata/search operations

    Note: Upload tests use small dummy files for performance testing.
    """

    @task(35)
    @tag("read_heavy", "documents")
    def list_documents(self):
        """List patient documents."""
        patient_id = random.randint(1, 50)
        params = {
            "patient_id": patient_id,
            "skip": 0,
            "limit": 20,
        }
        self.client.get(
            "/api/v1/documents/",
            headers=self.get_headers(),
            params=params,
            name="/api/v1/documents/ (list)",
        )

    @task(15)
    @tag("read_heavy", "documents")
    def get_document_metadata(self):
        """Get document metadata."""
        document_id = random.randint(1, 100)
        self.client.get(
            f"/api/v1/documents/{document_id}/metadata",
            headers=self.get_headers(),
            name="/api/v1/documents/{id}/metadata",
            catch_response=True,
        )

    @task(30)
    @tag("write_heavy", "documents")
    def upload_document(self):
        """
        Upload a document (simulated with small test file).

        Note: Uses multipart/form-data with dummy PDF content.
        In production, test with realistic file sizes.
        """
        # Create small dummy PDF-like content
        dummy_content = b"%PDF-1.4\n%Test document for performance testing\n%%EOF"

        files = {
            "file": (
                f"test_doc_{random.randint(1000, 9999)}.pdf",
                dummy_content,
                "application/pdf",
            ),
        }
        data = {
            "patient_id": str(random.randint(1, 50)),
            "document_type": random.choice(
                ["prescription", "lab_result", "imaging", "consultation_note"]
            ),
            "description": "Performance test document",
        }

        # Note: Remove Content-Type header for multipart/form-data
        headers = {"Authorization": f"Bearer {self.access_token}"}

        self.client.post(
            "/api/v1/documents/upload",
            headers=headers,
            files=files,
            data=data,
            name="/api/v1/documents/upload",
        )

    @task(20)
    @tag("read_heavy", "documents")
    def search_documents(self):
        """Search documents by type or description."""
        params = {
            "document_type": random.choice(["prescription", "lab_result", "imaging"]),
        }
        self.client.get(
            "/api/v1/documents/search",
            headers=self.get_headers(),
            params=params,
            name="/api/v1/documents/search",
        )


class MixedWorkloadUser(HttpUser):
    """
    Simulates realistic mixed workload with multiple user behaviors.

    This user performs a combination of patient, messaging, and document operations
    with realistic timing between requests.

    Target load: 100 concurrent users with 10 users/sec spawn rate
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    tasks = {
        PatientTasks: 5,  # 50% weight - patients are most accessed
        MessageTasks: 3,  # 30% weight - messaging is frequent
        DocumentTasks: 2,  # 20% weight - documents less frequent
    }


class ReadHeavyUser(HttpUser):
    """
    Simulates users performing mostly read operations.

    Use this for testing read-heavy scenarios (e.g., doctors reviewing records).
    Run with: locust -f test_load.py ReadHeavyUser --host=http://localhost:8000
    """

    wait_time = between(0.5, 2)

    tasks = {
        PatientTasks: 6,
        MessageTasks: 3,
        DocumentTasks: 1,
    }


class WriteHeavyUser(HttpUser):
    """
    Simulates users performing write-intensive operations.

    Use this for testing write performance (e.g., admission desk, document uploads).
    Run with: locust -f test_load.py WriteHeavyUser --host=http://localhost:8000
    """

    wait_time = between(2, 5)  # Longer wait for write operations

    tasks = {
        PatientTasks: 3,
        MessageTasks: 3,
        DocumentTasks: 4,  # Document uploads are write-heavy
    }


# Default user class for general load testing
class KeneyAppUser(HttpUser):
    """
    Default user class for general load testing.

    This is an alias for MixedWorkloadUser and will be used when running:
    locust -f tests/performance/test_load.py --host=http://localhost:8000
    """

    wait_time = between(1, 3)
    tasks = {
        PatientTasks: 5,
        MessageTasks: 3,
        DocumentTasks: 2,
    }


# Example Locust commands for different scenarios:
# ================================================
#
# 1. Mixed workload (default):
#    locust -f tests/performance/test_load.py --host=http://localhost:8000 \
#           --users 100 --spawn-rate 10 --run-time 5m
#
# 2. Read-heavy scenario:
#    locust -f tests/performance/test_load.py ReadHeavyUser --host=http://localhost:8000 \
#           --users 150 --spawn-rate 15 --run-time 5m
#
# 3. Write-heavy scenario:
#    locust -f tests/performance/test_load.py WriteHeavyUser --host=http://localhost:8000 \
#           --users 50 --spawn-rate 5 --run-time 5m
#
# 4. Target specific endpoints with tags:
#    locust -f tests/performance/test_load.py --host=http://localhost:8000 \
#           --tags read_heavy --users 100 --spawn-rate 10 --run-time 3m
#
# 5. Baseline test (quick validation):
#    locust -f tests/performance/test_load.py --host=http://localhost:8000 \
#           --users 50 --spawn-rate 10 --run-time 2m --headless --csv=baseline_results
#
# Performance Targets:
# ===================
# - Patients endpoint: p95 < 500ms at 100 req/s
# - Messages endpoint: p95 < 300ms at 50 req/s
# - Documents upload: p95 < 2s at 20 uploads/s
# - Error rate: < 1% under target load
# - CPU usage: < 70% under target load
# - Memory usage: < 80% under target load
