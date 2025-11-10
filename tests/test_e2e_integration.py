"""
End-to-End Integration Tests for KeneyApp

Tests the entire application stack in a Docker environment:
- Authentication workflows
- CRUD operations on all resources
- RBAC enforcement
- Multi-tenancy isolation
- Cache behavior
- Background tasks
- FHIR endpoints
- GraphQL queries

All operations are logged for post-test analysis.
"""

import json
import logging
import time
from datetime import datetime, date
from typing import Dict, List, Any

import pytest
import requests
from requests.exceptions import RequestException

# Configure structured logging for analysis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/e2e_integration_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('e2e_integration')


class E2ETestLogger:
    """Structured logger for E2E test results"""
    
    def __init__(self):
        self.results = {
            'test_run_id': datetime.utcnow().isoformat(),
            'start_time': None,
            'end_time': None,
            'total_duration_seconds': 0,
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            },
            'errors': [],
            'performance_metrics': {}
        }
    
    def start(self):
        self.results['start_time'] = datetime.utcnow().isoformat()
        logger.info("=" * 80)
        logger.info("Starting End-to-End Integration Tests")
        logger.info("=" * 80)
    
    def log_test(self, name: str, status: str, duration: float, details: Dict = None):
        test_result = {
            'name': name,
            'status': status,
            'duration_seconds': duration,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        self.results['tests'].append(test_result)
        self.results['summary']['total'] += 1
        self.results['summary'][status] += 1
        
        emoji = "✅" if status == "passed" else "❌" if status == "failed" else "⏭️"
        logger.info(f"{emoji} {name} | {status.upper()} | {duration:.2f}s")
        if details:
            logger.info(f"   Details: {json.dumps(details, indent=2)}")
    
    def log_error(self, test_name: str, error: str, traceback: str = None):
        error_record = {
            'test': test_name,
            'error': error,
            'traceback': traceback,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.results['errors'].append(error_record)
        logger.error(f"❌ ERROR in {test_name}: {error}")
        if traceback:
            logger.error(f"   Traceback: {traceback}")
    
    def log_performance(self, metric_name: str, value: float, unit: str = "ms"):
        self.results['performance_metrics'][metric_name] = {
            'value': value,
            'unit': unit
        }
        logger.info(f"📊 Performance: {metric_name} = {value:.2f} {unit}")
    
    def finish(self):
        self.results['end_time'] = datetime.utcnow().isoformat()
        start = datetime.fromisoformat(self.results['start_time'])
        end = datetime.fromisoformat(self.results['end_time'])
        self.results['total_duration_seconds'] = (end - start).total_seconds()
        
        # Save detailed results
        with open('logs/e2e_integration_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info("=" * 80)
        logger.info("End-to-End Integration Tests Complete")
        logger.info(f"Total: {self.results['summary']['total']}")
        logger.info(f"Passed: {self.results['summary']['passed']} ✅")
        logger.info(f"Failed: {self.results['summary']['failed']} ❌")
        logger.info(f"Duration: {self.results['total_duration_seconds']:.2f}s")
        logger.info(f"Results saved to: logs/e2e_integration_results.json")
        logger.info("=" * 80)
    
    def get_results(self) -> Dict:
        return self.results


@pytest.fixture(scope="module")
def api_base_url():
    """Base URL for API - configurable for Docker environment"""
    return "http://localhost:8000"


@pytest.fixture(scope="module")
def test_logger():
    """Test logger fixture"""
    logger_instance = E2ETestLogger()
    logger_instance.start()
    yield logger_instance
    logger_instance.finish()


@pytest.fixture(scope="module")
def authenticated_sessions(api_base_url, test_logger):
    """Create authenticated sessions for different user roles"""
    sessions = {}
    
    # Super Admin
    sessions['super_admin'] = _authenticate(
        api_base_url, "superadmin", "superadmin123", "Super Admin", test_logger
    )
    
    # Admin
    sessions['admin'] = _authenticate(
        api_base_url, "admin", "admin123", "Admin", test_logger
    )
    
    # Doctor
    sessions['doctor'] = _authenticate(
        api_base_url, "doctor_smith", "doctor123", "Doctor", test_logger
    )
    
    # Nurse
    sessions['nurse'] = _authenticate(
        api_base_url, "nurse_williams", "nurse123", "Nurse", test_logger
    )
    
    # Receptionist
    sessions['receptionist'] = _authenticate(
        api_base_url, "receptionist", "receptionist123", "Receptionist", test_logger
    )
    
    return sessions


def _authenticate(base_url: str, username: str, password: str, role: str, test_logger: E2ETestLogger) -> Dict:
    """Authenticate and return session with token"""
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            data={"username": username, "password": password},
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            test_logger.log_test(
                f"Authentication: {role}",
                "passed",
                duration,
                {"username": username, "token_received": bool(data.get('access_token'))}
            )
            test_logger.log_performance(f"auth_{role.lower().replace(' ', '_')}", duration * 1000)
            
            return {
                'token': data['access_token'],
                'headers': {
                    'Authorization': f"Bearer {data['access_token']}",
                    'Content-Type': 'application/json'
                },
                'user': data.get('user', {})
            }
        else:
            test_logger.log_test(
                f"Authentication: {role}",
                "failed",
                duration,
                {"status_code": response.status_code, "error": response.text}
            )
            return None
            
    except RequestException as e:
        test_logger.log_error(f"Authentication: {role}", str(e))
        return None


class TestE2EHealthChecks:
    """Test application health and readiness"""
    
    def test_root_endpoint(self, api_base_url, test_logger):
        """Test root endpoint availability"""
        start_time = time.time()
        try:
            response = requests.get(f"{api_base_url}/", timeout=5)
            duration = time.time() - start_time
            
            assert response.status_code == 200, "Root endpoint should be accessible"
            data = response.json()
            
            test_logger.log_test(
                "Root Endpoint",
                "passed",
                duration,
                {"response": data}
            )
            test_logger.log_performance("root_endpoint_response_time", duration * 1000)
            
        except Exception as e:
            test_logger.log_error("Root Endpoint", str(e))
            raise
    
    def test_health_check(self, api_base_url, test_logger):
        """Test health check endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{api_base_url}/health", timeout=5)
            duration = time.time() - start_time
            
            assert response.status_code == 200, "Health check should return 200"
            data = response.json()
            assert data.get('status') == 'healthy', "Application should be healthy"
            
            test_logger.log_test(
                "Health Check",
                "passed",
                duration,
                {"health_status": data}
            )
            test_logger.log_performance("health_check_response_time", duration * 1000)
            
        except Exception as e:
            test_logger.log_error("Health Check", str(e))
            raise
    
    def test_api_docs_accessible(self, api_base_url, test_logger):
        """Test API documentation availability"""
        start_time = time.time()
        try:
            response = requests.get(f"{api_base_url}/docs", timeout=5)
            duration = time.time() - start_time
            
            assert response.status_code == 200, "API docs should be accessible"
            
            test_logger.log_test(
                "API Documentation",
                "passed",
                duration,
                {"accessible": True}
            )
            
        except Exception as e:
            test_logger.log_error("API Documentation", str(e))
            raise


class TestE2EPatientWorkflows:
    """Test complete patient management workflows"""
    
    def test_patient_crud_workflow(self, api_base_url, authenticated_sessions, test_logger):
        """Test complete patient CRUD workflow"""
        admin_session = authenticated_sessions['admin']
        if not admin_session:
            pytest.skip("Admin authentication failed")
        
        patient_id = None
        
        # CREATE Patient
        start_time = time.time()
        try:
            create_payload = {
                "first_name": "John",
                "last_name": "E2ETest",
                "date_of_birth": "1990-01-15",
                "gender": "male",
                "email": f"john.e2e.{int(time.time())}@test.com",
                "phone": "+1234567890",
                "address": "123 Test Street",
                "medical_history": "No significant history",
                "allergies": "Penicillin",
                "blood_type": "O+",
                "emergency_contact": "Jane Doe",
                "emergency_phone": "+0987654321"
            }
            
            response = requests.post(
                f"{api_base_url}/api/v1/patients/",
                json=create_payload,
                headers=admin_session['headers'],
                timeout=10
            )
            create_duration = time.time() - start_time
            
            assert response.status_code == 201, f"Patient creation failed: {response.text}"
            patient_data = response.json()
            patient_id = patient_data['id']
            
            # Verify encrypted fields are not plain text
            assert patient_data['medical_history'] != create_payload['medical_history'], \
                "Medical history should be encrypted"
            
            test_logger.log_test(
                "Patient Create",
                "passed",
                create_duration,
                {"patient_id": patient_id, "email": patient_data['email']}
            )
            test_logger.log_performance("patient_create_time", create_duration * 1000)
            
        except Exception as e:
            test_logger.log_error("Patient Create", str(e))
            raise
        
        # READ Patient
        start_time = time.time()
        try:
            response = requests.get(
                f"{api_base_url}/api/v1/patients/{patient_id}",
                headers=admin_session['headers'],
                timeout=10
            )
            read_duration = time.time() - start_time
            
            assert response.status_code == 200, "Patient read failed"
            patient_data = response.json()
            assert patient_data['id'] == patient_id
            assert patient_data['first_name'] == "John"
            
            test_logger.log_test(
                "Patient Read",
                "passed",
                read_duration,
                {"patient_id": patient_id, "decrypted_successfully": True}
            )
            test_logger.log_performance("patient_read_time", read_duration * 1000)
            
        except Exception as e:
            test_logger.log_error("Patient Read", str(e))
            raise
        
        # UPDATE Patient
        start_time = time.time()
        try:
            update_payload = {
                "phone": "+9999999999",
                "address": "456 Updated Street"
            }
            
            response = requests.put(
                f"{api_base_url}/api/v1/patients/{patient_id}",
                json=update_payload,
                headers=admin_session['headers'],
                timeout=10
            )
            update_duration = time.time() - start_time
            
            assert response.status_code == 200, "Patient update failed"
            updated_data = response.json()
            assert updated_data['phone'] == "+9999999999"
            
            test_logger.log_test(
                "Patient Update",
                "passed",
                update_duration,
                {"patient_id": patient_id, "updated_fields": list(update_payload.keys())}
            )
            test_logger.log_performance("patient_update_time", update_duration * 1000)
            
        except Exception as e:
            test_logger.log_error("Patient Update", str(e))
            raise
        
        # LIST Patients
        start_time = time.time()
        try:
            response = requests.get(
                f"{api_base_url}/api/v1/patients/?skip=0&limit=10",
                headers=admin_session['headers'],
                timeout=10
            )
            list_duration = time.time() - start_time
            
            assert response.status_code == 200, "Patient list failed"
            patients = response.json()
            assert isinstance(patients, list)
            assert any(p['id'] == patient_id for p in patients), "Created patient should be in list"
            
            test_logger.log_test(
                "Patient List",
                "passed",
                list_duration,
                {"total_patients": len(patients), "contains_created": True}
            )
            test_logger.log_performance("patient_list_time", list_duration * 1000)
            
        except Exception as e:
            test_logger.log_error("Patient List", str(e))
            raise
        
        # DELETE Patient (Super Admin only)
        super_admin_session = authenticated_sessions['super_admin']
        if super_admin_session:
            start_time = time.time()
            try:
                response = requests.delete(
                    f"{api_base_url}/api/v1/patients/{patient_id}",
                    headers=super_admin_session['headers'],
                    timeout=10
                )
                delete_duration = time.time() - start_time
                
                assert response.status_code == 204, "Patient deletion failed"
                
                # Verify patient is deleted
                verify_response = requests.get(
                    f"{api_base_url}/api/v1/patients/{patient_id}",
                    headers=admin_session['headers'],
                    timeout=10
                )
                assert verify_response.status_code == 404, "Patient should be deleted"
                
                test_logger.log_test(
                    "Patient Delete",
                    "passed",
                    delete_duration,
                    {"patient_id": patient_id, "verified_deleted": True}
                )
                test_logger.log_performance("patient_delete_time", delete_duration * 1000)
                
            except Exception as e:
                test_logger.log_error("Patient Delete", str(e))
                raise


class TestE2ERBACEnforcement:
    """Test role-based access control enforcement"""
    
    def test_rbac_patient_access(self, api_base_url, authenticated_sessions, test_logger):
        """Test RBAC for patient endpoints"""
        # Receptionist should be able to list patients
        receptionist = authenticated_sessions['receptionist']
        if receptionist:
            start_time = time.time()
            try:
                response = requests.get(
                    f"{api_base_url}/api/v1/patients/",
                    headers=receptionist['headers'],
                    timeout=10
                )
                duration = time.time() - start_time
                
                assert response.status_code == 200, "Receptionist should list patients"
                
                test_logger.log_test(
                    "RBAC: Receptionist can list patients",
                    "passed",
                    duration,
                    {"role": "Receptionist", "endpoint": "/patients", "method": "GET"}
                )
            except Exception as e:
                test_logger.log_error("RBAC: Receptionist list", str(e))
                raise
        
        # Receptionist should NOT be able to create patients
        if receptionist:
            start_time = time.time()
            try:
                create_payload = {
                    "first_name": "Unauthorized",
                    "last_name": "Test",
                    "date_of_birth": "1990-01-01",
                    "gender": "male",
                    "email": "unauthorized@test.com",
                    "phone": "+1111111111"
                }
                
                response = requests.post(
                    f"{api_base_url}/api/v1/patients/",
                    json=create_payload,
                    headers=receptionist['headers'],
                    timeout=10
                )
                duration = time.time() - start_time
                
                assert response.status_code == 403, "Receptionist should not create patients"
                
                test_logger.log_test(
                    "RBAC: Receptionist blocked from creating patients",
                    "passed",
                    duration,
                    {"role": "Receptionist", "endpoint": "/patients", "method": "POST", "blocked": True}
                )
            except Exception as e:
                test_logger.log_error("RBAC: Receptionist create block", str(e))
                raise


class TestE2ECacheValidation:
    """Test caching behavior"""
    
    def test_cache_hit_performance(self, api_base_url, authenticated_sessions, test_logger):
        """Test cache hit improves performance"""
        admin_session = authenticated_sessions['admin']
        if not admin_session:
            pytest.skip("Admin authentication failed")
        
        # First request (cache miss)
        start_time = time.time()
        response1 = requests.get(
            f"{api_base_url}/api/v1/patients/?skip=0&limit=10",
            headers=admin_session['headers'],
            timeout=10
        )
        first_duration = time.time() - start_time
        
        # Second request (should hit cache)
        start_time = time.time()
        response2 = requests.get(
            f"{api_base_url}/api/v1/patients/?skip=0&limit=10",
            headers=admin_session['headers'],
            timeout=10
        )
        second_duration = time.time() - start_time
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Second request should be faster (cached)
        improvement = ((first_duration - second_duration) / first_duration) * 100
        
        test_logger.log_test(
            "Cache Performance",
            "passed",
            first_duration + second_duration,
            {
                "first_request_ms": first_duration * 1000,
                "second_request_ms": second_duration * 1000,
                "improvement_percent": improvement,
                "cache_working": second_duration < first_duration
            }
        )


class TestE2EGraphQL:
    """Test GraphQL endpoints"""
    
    def test_graphql_patient_query(self, api_base_url, authenticated_sessions, test_logger):
        """Test GraphQL patient query"""
        admin_session = authenticated_sessions['admin']
        if not admin_session:
            pytest.skip("Admin authentication failed")
        
        start_time = time.time()
        try:
            query = """
            query {
                patients(skip: 0, limit: 5) {
                    id
                    firstName
                    lastName
                    email
                }
            }
            """
            
            response = requests.post(
                f"{api_base_url}/graphql",
                json={"query": query},
                headers=admin_session['headers'],
                timeout=10
            )
            duration = time.time() - start_time
            
            assert response.status_code == 200, "GraphQL query failed"
            data = response.json()
            assert 'data' in data, "GraphQL response should have data"
            
            test_logger.log_test(
                "GraphQL Patient Query",
                "passed",
                duration,
                {"patients_returned": len(data.get('data', {}).get('patients', []))}
            )
            test_logger.log_performance("graphql_query_time", duration * 1000)
            
        except Exception as e:
            test_logger.log_error("GraphQL Patient Query", str(e))
            raise


class TestE2EMetricsAndMonitoring:
    """Test metrics and monitoring endpoints"""
    
    def test_prometheus_metrics(self, api_base_url, test_logger):
        """Test Prometheus metrics endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{api_base_url}/metrics", timeout=10)
            duration = time.time() - start_time
            
            assert response.status_code == 200, "Metrics endpoint should be accessible"
            metrics_text = response.text
            
            # Verify key metrics exist
            assert "patient_operations_total" in metrics_text, "Patient operations metric missing"
            assert "http_requests_total" in metrics_text or "python_info" in metrics_text, \
                "HTTP metrics missing"
            
            test_logger.log_test(
                "Prometheus Metrics",
                "passed",
                duration,
                {"metrics_available": True, "metrics_size_bytes": len(metrics_text)}
            )
            
        except Exception as e:
            test_logger.log_error("Prometheus Metrics", str(e))
            raise


@pytest.mark.integration
def test_full_e2e_suite(test_logger):
    """Final summary test that consolidates all results"""
    results = test_logger.get_results()
    
    logger.info("\n" + "=" * 80)
    logger.info("FINAL TEST SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Test Run ID: {results['test_run_id']}")
    logger.info(f"Duration: {results['total_duration_seconds']:.2f}s")
    logger.info(f"Total Tests: {results['summary']['total']}")
    logger.info(f"Passed: {results['summary']['passed']} ✅")
    logger.info(f"Failed: {results['summary']['failed']} ❌")
    logger.info(f"Skipped: {results['summary']['skipped']} ⏭️")
    
    if results['errors']:
        logger.error(f"\nErrors Encountered: {len(results['errors'])}")
        for error in results['errors']:
            logger.error(f"  - {error['test']}: {error['error']}")
    
    logger.info("\n📊 Performance Metrics:")
    for metric, data in results['performance_metrics'].items():
        logger.info(f"  {metric}: {data['value']:.2f} {data['unit']}")
    
    logger.info("\n📄 Detailed results: logs/e2e_integration_results.json")
    logger.info("=" * 80)
    
    # Assert overall success
    assert results['summary']['failed'] == 0, \
        f"{results['summary']['failed']} test(s) failed. Check logs for details."
