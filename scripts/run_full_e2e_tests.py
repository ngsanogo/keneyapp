"""
Master End-to-End Test Orchestrator for KeneyApp.

Orchestrates complete E2E testing workflow:
1. Validates environment setup
2. Seeds test data
3. Runs API tests
4. Validates frontend-backend alignment
5. Generates comprehensive report

Usage:
    python scripts/run_full_e2e_tests.py
    python scripts/run_full_e2e_tests.py --skip-seed
    python scripts/run_full_e2e_tests.py --clean-first
    python scripts/run_full_e2e_tests.py --patient-count 200
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


class E2ETestOrchestrator:
    """Orchestrate end-to-end testing workflow."""

    def __init__(
        self,
        backend_url: str = "http://localhost:8000",
        frontend_url: str = "http://localhost:3000",
        patient_count: int = 100,
        skip_seed: bool = False,
        clean_first: bool = False,
    ):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.patient_count = patient_count
        self.skip_seed = skip_seed
        self.clean_first = clean_first
        self.start_time = datetime.now()
        self.results: Dict[str, Tuple[bool, str]] = {}
        self.scripts_dir = Path(__file__).parent

    def _log(self, message: str, color: str = ""):
        """Log colored message."""
        print(f"{color}{message}{RESET}")

    def _run_command(self, cmd: List[str], stage_name: str) -> Tuple[bool, str]:
        """Run a command and capture output."""
        self._log(f"\n{'='*80}", CYAN)
        self._log(f"🚀 {stage_name}", CYAN)
        self._log(f"{'='*80}", CYAN)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            success = result.returncode == 0
            output = result.stdout if result.stdout else result.stderr

            if success:
                self._log(f"✅ {stage_name} completed successfully", GREEN)
            else:
                self._log(f"❌ {stage_name} failed", RED)
                self._log(f"Error output:\n{result.stderr[:500]}", RED)

            return success, output

        except subprocess.TimeoutExpired:
            self._log(f"❌ {stage_name} timed out after 5 minutes", RED)
            return False, "Command timed out"
        except Exception as e:
            self._log(f"❌ {stage_name} failed with exception: {e}", RED)
            return False, str(e)

    def check_prerequisites(self) -> bool:
        """Check if required services are running."""
        self._log("\n" + "=" * 80, MAGENTA)
        self._log("🔍 Checking Prerequisites", MAGENTA)
        self._log("=" * 80, MAGENTA)

        prerequisites = {
            "Backend": self.backend_url,
            "Frontend": self.frontend_url,
            "Python": sys.executable,
        }

        all_ok = True

        for name, value in prerequisites.items():
            if name in ["Backend", "Frontend"]:
                # Check if service is running
                try:
                    import requests

                    response = requests.get(value, timeout=3)
                    if response.ok:
                        self._log(f"✅ {name:15} {value}", GREEN)
                    else:
                        self._log(
                            f"❌ {name:15} {value} returned {response.status_code}",
                            RED,
                        )
                        all_ok = False
                except Exception as e:
                    self._log(f"❌ {name:15} {value} not accessible", RED)
                    all_ok = False
            else:
                self._log(f"✅ {name:15} {value}", GREEN)

        return all_ok

    def stage_1_seed_data(self) -> bool:
        """Stage 1: Seed test data."""
        if self.skip_seed:
            self._log("\n⏭️  Skipping data seeding (--skip-seed)", YELLOW)
            self.results["Seed Data"] = (True, "Skipped")
            return True

        cmd = [
            sys.executable,
            str(self.scripts_dir / "seed_test_data.py"),
            "--count",
            str(self.patient_count),
        ]

        if self.clean_first:
            cmd.append("--clean")

        success, output = self._run_command(cmd, "Stage 1: Seed Test Data")
        self.results["Seed Data"] = (success, output[-500:] if output else "")
        return success

    def stage_2_validate_alignment(self) -> bool:
        """Stage 2: Validate frontend-backend alignment."""
        cmd = [
            sys.executable,
            str(self.scripts_dir / "validate_frontend_backend.py"),
            "--backend",
            self.backend_url,
            "--frontend",
            self.frontend_url,
        ]

        success, output = self._run_command(cmd, "Stage 2: Validate Frontend-Backend Alignment")
        self.results["Frontend-Backend Validation"] = (
            success,
            output[-500:] if output else "",
        )
        return success

    def stage_3_test_apis(self) -> bool:
        """Stage 3: Test all API endpoints."""
        cmd = [
            sys.executable,
            str(self.scripts_dir / "test_all_apis.py"),
            "--base-url",
            self.backend_url,
            "--verbose",
        ]

        success, output = self._run_command(cmd, "Stage 3: Test All API Endpoints")
        self.results["API Tests"] = (success, output[-500:] if output else "")
        return success

    def stage_4_check_database(self) -> bool:
        """Stage 4: Verify database integrity."""
        self._log(f"\n{'='*80}", CYAN)
        self._log("🗄️  Stage 4: Database Integrity Check", CYAN)
        self._log(f"{'='*80}", CYAN)

        try:
            import requests

            # Check if we can query patients
            response = requests.get(f"{self.backend_url}/api/v1/patients/count")

            if response.ok:
                count = response.json()
                self._log(f"✅ Database accessible, {count} patients found", GREEN)
                self.results["Database Check"] = (True, f"{count} patients")
                return True
            else:
                self._log(f"❌ Failed to query database: {response.status_code}", RED)
                self.results["Database Check"] = (False, "Query failed")
                return False

        except Exception as e:
            self._log(f"❌ Database check failed: {e}", RED)
            self.results["Database Check"] = (False, str(e))
            return False

    def generate_report(self):
        """Generate comprehensive test report."""
        duration = (datetime.now() - self.start_time).total_seconds()

        print("\n" + "=" * 80)
        print(f"{MAGENTA}{'🎉 END-TO-END TEST REPORT':^80}{RESET}")
        print("=" * 80)

        # Test Results
        print(f"\n{BLUE}📊 Test Results:{RESET}")
        print("-" * 80)

        for stage, (success, output) in self.results.items():
            icon = "✅" if success else "❌"
            color = GREEN if success else RED
            status = "PASSED" if success else "FAILED"
            print(f"{icon} {stage:35} {color}{status:10}{RESET}")

        # Summary
        total = len(self.results)
        passed = sum(1 for s, _ in self.results.values() if s)
        failed = total - passed

        print(f"\n{BLUE}📈 Summary:{RESET}")
        print("-" * 80)
        print(f"Total Stages:     {total}")
        print(f"{GREEN}✅ Passed:         {passed}{RESET}")
        if failed > 0:
            print(f"{RED}❌ Failed:         {failed}{RESET}")
        print(f"Duration:         {duration:.2f}s")

        # Environment Info
        print(f"\n{BLUE}🌐 Environment:{RESET}")
        print("-" * 80)
        print(f"Backend:          {self.backend_url}")
        print(f"Frontend:         {self.frontend_url}")
        print(f"Test Patients:    {self.patient_count}")
        print(f"Python:           {sys.version.split()[0]}")

        # Final Status
        print("\n" + "=" * 80)
        if failed == 0:
            print(f"{GREEN}{'✅ ALL TESTS PASSED! System is ready for use.':^80}{RESET}")
        else:
            print(f"{RED}{'❌ SOME TESTS FAILED! Please review and fix issues.':^80}{RESET}")
        print("=" * 80 + "\n")

        # Save report to file
        self.save_report_to_file(duration, passed, failed)

    def save_report_to_file(self, duration: float, passed: int, failed: int):
        """Save test report to JSON file."""
        report = {
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": duration,
            "environment": {
                "backend_url": self.backend_url,
                "frontend_url": self.frontend_url,
                "python_version": sys.version.split()[0],
                "patient_count": self.patient_count,
            },
            "summary": {
                "total_stages": len(self.results),
                "passed": passed,
                "failed": failed,
                "success_rate": f"{passed/len(self.results)*100:.1f}%",
            },
            "results": {
                stage: {"success": success, "output_sample": output[:200]}
                for stage, (success, output) in self.results.items()
            },
        }

        report_file = (
            Path(__file__).parent.parent
            / "test_reports"
            / f"e2e_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        self._log(f"\n📄 Report saved to: {report_file}", CYAN)

    def run_full_suite(self):
        """Run complete E2E test suite."""
        print("\n" + "=" * 80)
        print(f"{MAGENTA}{'🚀 KENEYAPP END-TO-END TEST SUITE':^80}{RESET}")
        print("=" * 80)
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Check prerequisites
        if not self.check_prerequisites():
            self._log(
                "\n❌ Prerequisites check failed. Please ensure all services are running.",
                RED,
            )
            return

        # Run test stages
        stages = [
            self.stage_1_seed_data,
            self.stage_2_validate_alignment,
            self.stage_3_test_apis,
            self.stage_4_check_database,
        ]

        continue_testing = True
        for stage_func in stages:
            if not continue_testing:
                self._log("\n⚠️  Skipping remaining stages due to failures", YELLOW)
                break

            success = stage_func()

            # Optionally stop on failure (uncomment to enable)
            # if not success:
            #     continue_testing = False

        # Generate report
        self.generate_report()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run comprehensive end-to-end tests for KeneyApp")
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
    parser.add_argument(
        "--patient-count",
        type=int,
        default=100,
        help="Number of test patients to generate (default: 100)",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip test data seeding",
    )
    parser.add_argument(
        "--clean-first",
        action="store_true",
        help="Clean existing test data before seeding",
    )

    args = parser.parse_args()

    orchestrator = E2ETestOrchestrator(
        backend_url=args.backend,
        frontend_url=args.frontend,
        patient_count=args.patient_count,
        skip_seed=args.skip_seed,
        clean_first=args.clean_first,
    )

    orchestrator.run_full_suite()


if __name__ == "__main__":
    main()
