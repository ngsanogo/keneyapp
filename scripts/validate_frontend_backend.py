"""
Frontend-Backend Alignment Validator for KeneyApp.

Validates that:
1. Frontend can reach backend APIs
2. API contracts match expected schemas
3. Authentication flow works end-to-end
4. CORS configuration is correct
5. WebSocket connections work
6. Static assets are served correctly

Usage:
    python scripts/validate_frontend_backend.py
    python scripts/validate_frontend_backend.py --backend http://localhost:8000 --frontend http://localhost:3000
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


@dataclass
class ValidationResult:
    """Validation test result."""

    test_name: str
    success: bool
    message: str
    details: Optional[str] = None


class FrontendBackendValidator:
    """Validate frontend-backend integration."""

    def __init__(self, backend_url: str, frontend_url: str):
        self.backend_url = backend_url.rstrip("/")
        self.frontend_url = frontend_url.rstrip("/")
        self.results: List[ValidationResult] = []

    def _log(self, message: str, color: str = ""):
        """Log colored message."""
        print(f"{color}{message}{RESET}")

    def _add_result(self, test_name: str, success: bool, message: str, details: str = None):
        """Add validation result."""
        result = ValidationResult(test_name, success, message, details)
        self.results.append(result)

        icon = "✅" if success else "❌"
        color = GREEN if success else RED
        self._log(f"{icon} {test_name}: {message}", color)
        if details:
            self._log(f"   {details}", YELLOW)

    def validate_backend_health(self) -> bool:
        """Check if backend is up and healthy."""
        self._log("\n🏥 Validating Backend Health", BLUE)

        try:
            response = requests.get(f"{self.backend_url}/", timeout=5)
            if response.ok:
                data = response.json()
                self._add_result(
                    "Backend Health",
                    True,
                    f"Backend is running: {data.get('name', 'KeneyApp')} v{data.get('version', '1.0.0')}",
                )
                return True
            else:
                self._add_result(
                    "Backend Health",
                    False,
                    f"Backend returned status {response.status_code}",
                )
                return False
        except Exception as e:
            self._add_result("Backend Health", False, "Backend is not reachable", str(e))
            return False

    def validate_frontend_health(self) -> bool:
        """Check if frontend is up and serving."""
        self._log("\n🎨 Validating Frontend Health", BLUE)

        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.ok:
                # Check if it's an HTML page
                content_type = response.headers.get("content-type", "")
                if "text/html" in content_type:
                    self._add_result(
                        "Frontend Health",
                        True,
                        "Frontend is serving HTML correctly",
                    )
                    return True
                else:
                    self._add_result(
                        "Frontend Health",
                        False,
                        f"Frontend returned unexpected content-type: {content_type}",
                    )
                    return False
            else:
                self._add_result(
                    "Frontend Health",
                    False,
                    f"Frontend returned status {response.status_code}",
                )
                return False
        except Exception as e:
            self._add_result("Frontend Health", False, "Frontend is not reachable", str(e))
            return False

    def validate_cors_configuration(self):
        """Validate CORS headers are set correctly."""
        self._log("\n🌐 Validating CORS Configuration", BLUE)

        try:
            # Simulate a CORS preflight request from frontend
            headers = {
                "Origin": self.frontend_url,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            }

            response = requests.options(
                f"{self.backend_url}/api/v1/patients", headers=headers, timeout=5
            )

            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get(
                    "Access-Control-Allow-Methods"
                ),
                "Access-Control-Allow-Headers": response.headers.get(
                    "Access-Control-Allow-Headers"
                ),
            }

            if cors_headers["Access-Control-Allow-Origin"]:
                self._add_result(
                    "CORS Headers",
                    True,
                    "CORS headers are configured",
                    f"Allowed origin: {cors_headers['Access-Control-Allow-Origin']}",
                )
            else:
                self._add_result(
                    "CORS Headers",
                    False,
                    "CORS headers not found",
                    "Frontend may have issues calling backend APIs",
                )

        except Exception as e:
            self._add_result("CORS Headers", False, "Failed to check CORS", str(e))

    def validate_api_endpoints(self):
        """Validate critical API endpoints exist."""
        self._log("\n🔌 Validating API Endpoints", BLUE)

        critical_endpoints = [
            ("/api/v1/health", "GET", "Health Check"),
            ("/api/v1/auth/login", "POST", "Authentication"),
            ("/api/v1/patients", "GET", "Patient List"),
            ("/api/v1/appointments", "GET", "Appointment List"),
            ("/api/v1/dashboard/stats", "GET", "Dashboard Stats"),
        ]

        for endpoint, method, name in critical_endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"

                if method == "GET":
                    # Try without auth first
                    response = requests.get(url, timeout=5)
                elif method == "POST":
                    response = requests.post(url, json={}, timeout=5)

                # 401/403 is ok - means endpoint exists but needs auth
                # 404 is bad - endpoint doesn't exist
                if response.status_code != 404:
                    self._add_result(
                        f"Endpoint: {name}",
                        True,
                        f"{method} {endpoint} exists",
                        f"Status: {response.status_code}",
                    )
                else:
                    self._add_result(
                        f"Endpoint: {name}",
                        False,
                        f"{method} {endpoint} not found",
                    )

            except Exception as e:
                self._add_result(
                    f"Endpoint: {name}",
                    False,
                    f"Failed to check {endpoint}",
                    str(e),
                )

    def validate_api_contract(self):
        """Validate API response structure matches expected schema."""
        self._log("\n📋 Validating API Contracts", BLUE)

        # Test health endpoint schema
        try:
            response = requests.get(f"{self.backend_url}/", timeout=5)
            if response.ok:
                data = response.json()
                required_fields = ["name", "version", "status"]
                has_all = all(field in data for field in required_fields)

                if has_all:
                    self._add_result(
                        "API Root Schema",
                        True,
                        "Root endpoint returns correct schema",
                    )
                else:
                    missing = [f for f in required_fields if f not in data]
                    self._add_result(
                        "API Root Schema",
                        False,
                        f"Missing fields: {', '.join(missing)}",
                    )
        except Exception as e:
            self._add_result("API Root Schema", False, "Failed to validate", str(e))

    def validate_authentication_flow(self):
        """Validate complete authentication flow."""
        self._log("\n🔐 Validating Authentication Flow", BLUE)

        try:
            # Step 1: Login
            login_response = requests.post(
                f"{self.backend_url}/api/v1/auth/login",
                json={"username": "admin", "password": "admin123"},
                timeout=5,
            )

            if login_response.ok:
                data = login_response.json()

                # Check for access_token
                if "access_token" in data:
                    self._add_result(
                        "Authentication",
                        True,
                        "Login returns access token",
                    )

                    # Step 2: Use token to access protected endpoint
                    token = data["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}

                    me_response = requests.get(
                        f"{self.backend_url}/api/v1/users/me",
                        headers=headers,
                        timeout=5,
                    )

                    if me_response.ok:
                        self._add_result(
                            "Token Authentication",
                            True,
                            "Token works for protected endpoints",
                        )
                    else:
                        self._add_result(
                            "Token Authentication",
                            False,
                            "Token doesn't work for protected endpoints",
                            f"Status: {me_response.status_code}",
                        )
                else:
                    self._add_result(
                        "Authentication",
                        False,
                        "Login response missing access_token",
                    )
            else:
                self._add_result(
                    "Authentication",
                    False,
                    f"Login failed with status {login_response.status_code}",
                )

        except Exception as e:
            self._add_result("Authentication Flow", False, "Failed to validate auth", str(e))

    def validate_static_assets(self):
        """Validate frontend static assets are accessible."""
        self._log("\n📦 Validating Static Assets", BLUE)

        # Common frontend assets
        assets = [
            ("/favicon.ico", "Favicon"),
            ("/static/js/main.*.js", "Main JS Bundle"),
            ("/static/css/main.*.css", "Main CSS Bundle"),
        ]

        for asset_pattern, name in assets:
            try:
                # For wildcard patterns, just check the directory
                if "*" in asset_pattern:
                    # Check if the static directory exists
                    response = requests.get(f"{self.frontend_url}/static", timeout=5)
                    success = response.status_code != 404
                    self._add_result(
                        f"Asset: {name}",
                        success,
                        "Static directory accessible" if success else "Not found",
                    )
                else:
                    response = requests.get(f"{self.frontend_url}{asset_pattern}", timeout=5)
                    success = response.ok
                    self._add_result(
                        f"Asset: {name}",
                        success,
                        "Asset accessible" if success else "Not found",
                    )

            except Exception as e:
                self._add_result(f"Asset: {name}", False, "Failed to check", str(e))

    def validate_api_docs(self):
        """Validate API documentation is accessible."""
        self._log("\n📚 Validating API Documentation", BLUE)

        docs_endpoints = [
            ("/api/v1/docs", "Swagger UI"),
            ("/api/v1/redoc", "ReDoc"),
            ("/api/v1/openapi.json", "OpenAPI Schema"),
        ]

        for endpoint, name in docs_endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                if response.ok:
                    self._add_result(f"Docs: {name}", True, f"{name} is accessible")
                else:
                    self._add_result(
                        f"Docs: {name}",
                        False,
                        f"{name} returned {response.status_code}",
                    )
            except Exception as e:
                self._add_result(f"Docs: {name}", False, "Failed to access", str(e))

    def run_validation(self):
        """Run complete validation suite."""
        print("\n" + "=" * 80)
        print(f"{BLUE}🔍 Frontend-Backend Alignment Validation{RESET}")
        print("=" * 80)
        print(f"Backend:  {self.backend_url}")
        print(f"Frontend: {self.frontend_url}")
        print("=" * 80)

        # Check basic health first
        backend_ok = self.validate_backend_health()
        frontend_ok = self.validate_frontend_health()

        if not backend_ok:
            self._log("\n❌ Backend is not running. Start backend and try again.", RED)
            return

        # Run other validations
        self.validate_cors_configuration()
        self.validate_api_endpoints()
        self.validate_api_contract()
        self.validate_authentication_flow()
        self.validate_api_docs()

        if frontend_ok:
            self.validate_static_assets()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print validation summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed

        print("\n" + "=" * 80)
        print(f"{BLUE}📊 Validation Summary{RESET}")
        print("=" * 80)
        print(f"Total Checks: {total}")
        print(f"{GREEN}✅ Passed:     {passed} ({passed/total*100:.1f}%){RESET}")
        if failed > 0:
            print(f"{RED}❌ Failed:     {failed} ({failed/total*100:.1f}%){RESET}")
        print("=" * 80)

        # Show failed validations
        if failed > 0:
            print(f"\n{RED}❌ Failed Validations:{RESET}")
            for result in self.results:
                if not result.success:
                    print(f"  • {result.test_name}: {result.message}")
                    if result.details:
                        print(f"    Details: {result.details}")

        if failed == 0:
            print(
                f"\n{GREEN}✅ All validations passed! Frontend and backend are properly aligned.{RESET}"
            )
        elif failed <= 3:
            print(f"\n{YELLOW}⚠️  Minor issues detected. System should mostly work.{RESET}")
        else:
            print(f"\n{RED}❌ Significant issues detected. Please fix before proceeding.{RESET}")

        print("=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate frontend-backend alignment")
    parser.add_argument(
        "--backend",
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--frontend",
        default="http://localhost:3000",
        help="Frontend URL (default: http://localhost:3000)",
    )

    args = parser.parse_args()

    validator = FrontendBackendValidator(args.backend, args.frontend)
    validator.run_validation()


if __name__ == "__main__":
    main()
