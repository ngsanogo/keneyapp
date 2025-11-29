"""
Comprehensive API endpoint tester for KeneyApp.

Tests all REST and GraphQL endpoints with realistic data flows.

Usage:
    python scripts/test_all_apis.py
    python scripts/test_all_apis.py --base-url http://localhost:8000
    python scripts/test_all_apis.py --verbose
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


@dataclass
class TestResult:
    """Store test result information."""

    endpoint: str
    method: str
    status_code: int
    success: bool
    response_time: float
    error: Optional[str] = None


class APITester:
    """Comprehensive API testing suite."""

    def __init__(self, base_url: str, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.results: list[TestResult] = []
        self.token: Optional[str] = None
        self.tenant_id: int = 1
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create session with retry logic."""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _log(self, message: str, color: str = ""):
        """Log message with optional color."""
        if self.verbose or "✅" in message or "❌" in message:
            print(f"{color}{message}{RESET}")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        auth_required: bool = True,
    ) -> TestResult:
        """Make HTTP request and record result."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        if auth_required and self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        start_time = time.time()

        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, params=params)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response_time = time.time() - start_time

            success = 200 <= response.status_code < 300
            error = None if success else response.text[:200]

            result = TestResult(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                success=success,
                response_time=response_time,
                error=error,
            )

            status_icon = "✅" if success else "❌"
            self._log(
                f"{status_icon} {method:6} {endpoint:40} [{response.status_code}] {response_time:.3f}s",
                GREEN if success else RED,
            )

            if self.verbose and not success:
                self._log(f"   Error: {error}", RED)

            self.results.append(result)
            return result

        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                success=False,
                response_time=response_time,
                error=str(e),
            )
            self._log(f"❌ {method:6} {endpoint:40} [ERROR] {str(e)}", RED)
            self.results.append(result)
            return result

    def authenticate(self) -> bool:
        """Login and get JWT token."""
        self._log("\n🔐 Authenticating...", BLUE)

        # FastAPI OAuth2PasswordRequestForm expects form data, not JSON
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                data={"username": "admin", "password": "admin123"},  # form data
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self._log(f"✅ Authenticated as admin", GREEN)
                    self._log(f"   Token: {self.token[:30]}...", GREEN)
                    return True
                else:
                    self._log(f"❌ No access_token in response", RED)
                    return False
            else:
                self._log(
                    f"❌ Authentication failed [{response.status_code}]: {response.text[:200]}",
                    RED,
                )
                return False
        except Exception as e:
            self._log(f"❌ Authentication error: {str(e)}", RED)
            return False


    def test_health_endpoints(self):
        """Test health and info endpoints."""
        self._log("\n🏥 Testing Health Endpoints", BLUE)
        self._request("GET", "/", auth_required=False)
        self._request("GET", "/health", auth_required=False)
        self._request("GET", "/api/v1/health", auth_required=False)

    def test_patient_crud(self):
        """Test patient CRUD operations."""
        self._log("\n👥 Testing Patient CRUD", BLUE)

        # List patients
        result = self._request("GET", "/api/v1/patients", params={"skip": 0, "limit": 10})

        # Get count
        self._request("GET", "/api/v1/patients/count")

        # Create patient
        patient_data = {
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "email": f"test.patient.{int(time.time())}@example.com",
            "phone": "+33612345678",
            "address": "123 Test Street, Paris",
            "blood_type": "A+",
        }
        create_result = self._request("POST", "/api/v1/patients", data=patient_data)

        if create_result.success:
            # Get the created patient ID from response
            response = self.session.post(
                f"{self.base_url}/api/v1/patients",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json=patient_data,
            )
            if response.ok:
                patient = response.json()
                patient_id = patient.get("id")

                # Get patient by ID
                self._request("GET", f"/api/v1/patients/{patient_id}")

                # Update patient
                update_data = {"phone": "+33698765432"}
                self._request("PUT", f"/api/v1/patients/{patient_id}", data=update_data)

                # Search patient
                self._request(
                    "GET", "/api/v1/patients/search", params={"q": "Test", "limit": 5}
                )

    def test_appointment_crud(self):
        """Test appointment CRUD operations."""
        self._log("\n📅 Testing Appointment CRUD", BLUE)

        # List appointments
        self._request("GET", "/api/v1/appointments", params={"skip": 0, "limit": 10})

        # Get today's appointments
        today = datetime.now().strftime("%Y-%m-%d")
        self._request("GET", f"/api/v1/appointments/date/{today}")

        # Create appointment (requires patient and doctor)
        # This may fail if no doctors/patients exist, which is expected
        appointment_data = {
            "patient_id": 1,
            "doctor_id": 1,
            "appointment_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "duration_minutes": 30,
            "reason": "Annual checkup",
            "status": "scheduled",
        }
        self._request("POST", "/api/v1/appointments", data=appointment_data)

    def test_prescription_crud(self):
        """Test prescription CRUD operations."""
        self._log("\n💊 Testing Prescription CRUD", BLUE)

        # List prescriptions
        self._request("GET", "/api/v1/prescriptions", params={"skip": 0, "limit": 10})

        # Create prescription
        prescription_data = {
            "patient_id": 1,
            "doctor_id": 1,
            "medication": "Amoxicillin 500mg",
            "dosage": "3x daily",
            "instructions": "Take with food",
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "status": "active",
        }
        self._request("POST", "/api/v1/prescriptions", data=prescription_data)

    def test_user_management(self):
        """Test user management endpoints."""
        self._log("\n👤 Testing User Management", BLUE)

        # List users
        self._request("GET", "/api/v1/users", params={"skip": 0, "limit": 10})

        # Get current user
        self._request("GET", "/api/v1/users/me")

    def test_tenant_endpoints(self):
        """Test tenant management."""
        self._log("\n🏢 Testing Tenant Management", BLUE)

        # List tenants
        self._request("GET", "/api/v1/tenants")

        # Get current tenant
        self._request("GET", f"/api/v1/tenants/{self.tenant_id}")

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoints."""
        self._log("\n📊 Testing Dashboard Statistics", BLUE)

        self._request("GET", "/api/v1/dashboard/stats")
        self._request("GET", "/api/v1/dashboard/recent-activity")

    def test_lab_tests(self):
        """Test lab test endpoints."""
        self._log("\n🔬 Testing Lab Tests", BLUE)

        # List lab test types
        self._request("GET", "/api/v1/lab/test-types")

        # List lab results
        self._request("GET", "/api/v1/lab/results", params={"skip": 0, "limit": 10})

    def test_medical_documents(self):
        """Test medical document endpoints."""
        self._log("\n📄 Testing Medical Documents", BLUE)

        # List documents
        self._request("GET", "/api/v1/documents", params={"skip": 0, "limit": 10})

    def test_messaging(self):
        """Test secure messaging endpoints."""
        self._log("\n💬 Testing Secure Messaging", BLUE)

        # List messages
        self._request("GET", "/api/v1/messages", params={"skip": 0, "limit": 10})

        # Get unread count
        self._request("GET", "/api/v1/messages/unread/count")

    def test_fhir_endpoints(self):
        """Test FHIR R4 endpoints."""
        self._log("\n🏥 Testing FHIR R4 Endpoints", BLUE)

        # FHIR metadata
        self._request("GET", "/fhir/metadata", auth_required=False)

        # FHIR patient search
        self._request("GET", "/fhir/Patient")

    def test_graphql(self):
        """Test GraphQL endpoint."""
        self._log("\n🔷 Testing GraphQL", BLUE)

        # Simple GraphQL query
        query = """
        query {
            patients(limit: 5) {
                id
                firstName
                lastName
            }
        }
        """
        self._request("POST", "/graphql", data={"query": query})

    def test_metrics(self):
        """Test Prometheus metrics endpoint."""
        self._log("\n📈 Testing Metrics", BLUE)
        self._request("GET", "/metrics", auth_required=False)

    def run_all_tests(self):
        """Run comprehensive test suite."""
        print("\n" + "=" * 80)
        print(f"{BLUE}🚀 KeneyApp API Comprehensive Test Suite{RESET}")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Authenticate first
        if not self.authenticate():
            self._log("\n❌ Authentication failed, cannot continue", RED)
            return

        # Run all test suites
        self.test_health_endpoints()
        self.test_patient_crud()
        self.test_appointment_crud()
        self.test_prescription_crud()
        self.test_user_management()
        self.test_tenant_endpoints()
        self.test_dashboard_stats()
        self.test_lab_tests()
        self.test_medical_documents()
        self.test_messaging()
        self.test_fhir_endpoints()
        self.test_graphql()
        self.test_metrics()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        avg_time = sum(r.response_time for r in self.results) / total if total > 0 else 0

        print("\n" + "=" * 80)
        print(f"{BLUE}📊 Test Results Summary{RESET}")
        print("=" * 80)
        print(f"Total Requests:  {total}")
        print(f"{GREEN}✅ Passed:        {passed} ({passed/total*100:.1f}%){RESET}")
        if failed > 0:
            print(f"{RED}❌ Failed:        {failed} ({failed/total*100:.1f}%){RESET}")
        print(f"Avg Response:    {avg_time:.3f}s")
        print("=" * 80)

        # Show failed tests
        if failed > 0:
            print(f"\n{RED}❌ Failed Tests:{RESET}")
            for result in self.results:
                if not result.success:
                    print(f"  • {result.method:6} {result.endpoint:40} [{result.status_code}]")
                    if result.error:
                        print(f"    Error: {result.error[:100]}")

        # Performance stats
        slowest = sorted(self.results, key=lambda r: r.response_time, reverse=True)[:5]
        if slowest:
            print(f"\n{YELLOW}🐢 Slowest Endpoints:{RESET}")
            for result in slowest:
                print(
                    f"  • {result.method:6} {result.endpoint:40} {result.response_time:.3f}s"
                )

        print("\n" + "=" * 80)
        print(
            f"{GREEN if failed == 0 else YELLOW}✅ Testing completed!{RESET}"
        )
        print("=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test all KeneyApp API endpoints")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    tester = APITester(args.base_url, args.verbose)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
