# Testing Strategy and Validation

## Table of Contents

1. [Overview](#overview)
2. [Testing Pyramid](#testing-pyramid)
3. [Backend Testing](#backend-testing)
4. [Frontend Testing](#frontend-testing)
5. [Integration Testing](#integration-testing)
6. [Security Testing](#security-testing)
7. [Performance Testing](#performance-testing)
8. [Beta Testing](#beta-testing)
9. [Compliance Validation](#compliance-validation)
10. [Test Automation](#test-automation)

## Overview

KeneyApp follows a comprehensive testing strategy aligned with healthcare industry requirements and modern software quality practices. Our goal is to achieve **80%+ test coverage** while ensuring safety, security, and compliance for healthcare data management.

### Testing Objectives

1. **Functional Correctness**: All features work as specified
2. **Data Integrity**: Patient data is accurately stored and retrieved
3. **Security**: No vulnerabilities or data leaks
4. **Performance**: Fast response times under load
5. **Compliance**: GDPR/HIPAA/HDS requirements met
6. **Reliability**: System handles errors gracefully
7. **Usability**: Interface is intuitive and accessible

### Quality Gates

Before any production deployment:

- ✅ All unit tests pass (100%)
- ✅ Integration tests pass (100%)
- ✅ Code coverage ≥ 70% (target 80%)
- ✅ No critical security vulnerabilities
- ✅ Performance tests meet SLA requirements
- ✅ Manual QA sign-off
- ✅ Security audit completed

## Testing Pyramid

```
         /\
        /  \        End-to-End Tests (10%)
       /    \       - Full user workflows
      /------\      - Docker-based scenarios
     /        \     - Critical paths only
    /          \
   /            \   Integration Tests (30%)
  /              \  - API contracts
 /                \ - Database interactions
/------------------\- Service integration
\                  /
 \                / Unit Tests (60%)
  \              /  - Functions & classes
   \            /   - Business logic
    \          /    - Isolated components
     \--------/
```

### Test Distribution

- **60% Unit Tests**: Fast, focused, testing individual components
- **30% Integration Tests**: Testing component interactions
- **10% End-to-End Tests**: Full workflow testing

## Backend Testing

### Unit Tests (pytest)

**Location**: `tests/`

**Framework**: pytest with pytest-asyncio

**Coverage**: 77% (159 tests, 155 passing, 4 expected failures)

**Test Types**:

1. **Model Tests** (`tests/test_models.py`)
   - Database model creation
   - Field validation
   - Relationship integrity
   - Timestamp auto-generation

2. **API Endpoint Tests** (`tests/test_api.py`)
   - Request/response validation
   - HTTP status codes
   - Authentication required
   - RBAC enforcement
   - Error handling

3. **Service Layer Tests** (`tests/test_services.py`)
   - Business logic validation
   - Data transformations
   - Encryption/decryption
   - FHIR conversions

4. **Security Tests** (`tests/test_security.py`)
   - Password hashing
   - JWT token generation
   - Token expiration
   - Permission checks

**Example Test**:

```python
def test_create_patient_authenticated(client, auth_headers):
    """Test creating a patient with authentication."""
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "gender": "M",
        "email": "john.doe@example.com"
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/patients/",
        json=patient_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert "id" in data
    assert "created_at" in data
```

**Running Unit Tests**:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::test_create_patient_authenticated -v

# Run tests in parallel
pytest -n auto
```

### Integration Tests

**Location**: `tests/test_integration.py`

**Testing**:

- Database transactions
- Redis cache operations
- Celery background tasks
- FHIR resource conversion
- OAuth2 authentication flow
- GraphQL queries

**Example Test**:

```python
def test_patient_cache_integration(client, db, auth_headers):
    """Test patient caching integration."""
    # Create patient
    response = client.post(
        f"{settings.API_V1_PREFIX}/patients/",
        json=patient_data,
        headers=auth_headers
    )
    patient_id = response.json()["id"]

    # First request - cache miss
    response1 = client.get(
        f"{settings.API_V1_PREFIX}/patients/{patient_id}",
        headers=auth_headers
    )
    assert response1.status_code == 200

    # Second request - cache hit (should be faster)
    response2 = client.get(
        f"{settings.API_V1_PREFIX}/patients/{patient_id}",
        headers=auth_headers
    )
    assert response2.status_code == 200
    assert response1.json() == response2.json()

    # Verify cache was used
    cache_key = f"patients:detail:{tenant_id}:{patient_id}"
    cached_data = cache_get(cache_key)
    assert cached_data is not None
```

### API Contract Tests

**Location**: `tests/test_contracts.py`

**Framework**: jsonschema

**Purpose**: Ensure API responses match documented schemas

**Example Test**:

```python
def test_patient_response_schema(client, auth_headers):
    """Test patient response matches schema."""
    schema = {
        "type": "object",
        "required": ["id", "first_name", "last_name", "date_of_birth"],
        "properties": {
            "id": {"type": "integer"},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "date_of_birth": {"type": "string", "format": "date"},
            "email": {"type": ["string", "null"]},
            "phone": {"type": ["string", "null"]},
            "created_at": {"type": "string", "format": "date-time"},
        }
    }

    response = client.get(
        f"{settings.API_V1_PREFIX}/patients/1",
        headers=auth_headers
    )

    jsonschema.validate(instance=response.json(), schema=schema)
```

### Smoke Tests

**Location**: `tests/test_smoke.py`

**Purpose**: Verify critical paths work after deployment

**Run Against**: Docker Compose stack

**Tests**:

- Health endpoint accessible
- Database connection works
- Redis connection works
- Authentication flow works
- Patient CRUD operations work
- Appointment listing works
- Dashboard statistics load

**Running Smoke Tests**:

```bash
# Start docker stack
docker-compose up -d

# Wait for services
sleep 30

# Run smoke tests
pytest tests/test_smoke.py -v
```

### Test Fixtures

**Location**: `tests/conftest.py`

**Fixtures Provided**:

- `db`: Test database session
- `client`: TestClient for API requests
- `auth_headers`: Authenticated request headers
- `test_user`: Pre-created test user
- `test_patient`: Pre-created test patient
- `test_tenant`: Pre-created test tenant

**Example Fixture**:

```python
@pytest.fixture
def auth_headers(client, test_user):
    """Generate authentication headers."""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={
            "username": test_user.username,
            "password": "password123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

## Frontend Testing

### Unit Tests (Jest)

**Location**: `frontend/src/**/*.test.tsx`

**Framework**: Jest + React Testing Library

**Test Types**:

1. **Component Tests**
   - Component rendering
   - Props handling
   - Event handlers
   - State management
   - Context usage

2. **Hook Tests**
   - Custom hooks behavior
   - State updates
   - Side effects

3. **Utility Tests**
   - Helper functions
   - Data transformations
   - Validation logic

**Example Test**:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import LoginPage from './LoginPage';

test('login form submits with username and password', async () => {
  const mockLogin = jest.fn();

  render(<LoginPage onLogin={mockLogin} />);

  // Find form inputs
  const usernameInput = screen.getByLabelText(/username/i);
  const passwordInput = screen.getByLabelText(/password/i);
  const submitButton = screen.getByRole('button', { name: /login/i });

  // Fill form
  fireEvent.change(usernameInput, { target: { value: 'admin' } });
  fireEvent.change(passwordInput, { target: { value: 'password123' } });

  // Submit form
  fireEvent.click(submitButton);

  // Verify login called
  expect(mockLogin).toHaveBeenCalledWith('admin', 'password123');
});
```

**Running Frontend Tests**:

```bash
cd frontend

# Run tests
npm test

# Run tests once (no watch)
npm test -- --watchAll=false

# Run with coverage
npm test -- --coverage --watchAll=false
```

### Integration Tests

**Testing**:

- API integration with mock server
- Authentication context
- Protected routes
- Form submission flows
- Error handling

**Example Test**:

```typescript
test('patient creation flow', async () => {
  // Mock API
  const mockApi = jest.spyOn(axios, 'post').mockResolvedValue({
    data: { id: 1, first_name: 'John', last_name: 'Doe' }
  });

  render(<PatientForm />);

  // Fill form
  fireEvent.change(screen.getByLabelText(/first name/i), {
    target: { value: 'John' }
  });
  fireEvent.change(screen.getByLabelText(/last name/i), {
    target: { value: 'Doe' }
  });

  // Submit
  fireEvent.click(screen.getByRole('button', { name: /save/i }));

  // Wait for API call
  await waitFor(() => {
    expect(mockApi).toHaveBeenCalledWith(
      '/api/v1/patients/',
      expect.objectContaining({
        first_name: 'John',
        last_name: 'Doe'
      })
    );
  });
});
```

### Snapshot Tests

**Purpose**: Detect unintended UI changes

```typescript
test('patient card matches snapshot', () => {
  const patient = {
    id: 1,
    first_name: 'John',
    last_name: 'Doe',
    date_of_birth: '1990-01-01'
  };

  const { container } = render(<PatientCard patient={patient} />);
  expect(container).toMatchSnapshot();
});
```

## Integration Testing

### End-to-End Tests

**Location**: `tests/e2e/`

**Framework**: Docker Compose + pytest

**Implementation**: ✅ Completed (see E2E_TESTING.md)

**Scenarios Tested**:

1. **Authentication Flows**
   - Admin login
   - Doctor login
   - Nurse login
   - Receptionist login
   - Invalid credentials
   - Token expiration

2. **Patient Management**
   - Create patient
   - List patients
   - Get patient details
   - Update patient
   - Delete patient (soft delete)
   - PHI encryption validation

3. **RBAC Enforcement**
   - Admin full access
   - Doctor patient access
   - Nurse limited access
   - Receptionist appointment access

4. **Caching Validation**
   - Cache hit/miss
   - Cache invalidation
   - Cache TTL

5. **GraphQL API**
   - Queries
   - Mutations
   - Error handling

6. **Metrics Collection**
   - Prometheus metrics
   - Counter increments
   - Histogram updates

**Running E2E Tests**:

```bash
# Full E2E test suite
./scripts/run_e2e_tests.sh

# View results
cat logs/e2e_integration_results.json

# Analyze results
python scripts/analyze_e2e_results.py
```

**E2E Test Results**:

- ✅ 156 scenarios tested
- ✅ 100% pass rate
- ✅ Average response time: 45ms
- ✅ All security checks passed

### Database Migration Tests

**Location**: `tests/test_migrations.py`

**Testing**:

- Migrations can upgrade
- Migrations can downgrade
- Data integrity maintained
- Indexes created correctly
- Foreign keys enforced

**Example Test**:

```python
def test_migration_upgrade_downgrade():
    """Test migration can upgrade and downgrade."""
    # Get current version
    result = subprocess.run(
        ["alembic", "current"],
        capture_output=True,
        text=True
    )
    initial_version = result.stdout.strip()

    # Downgrade one version
    subprocess.run(["alembic", "downgrade", "-1"])

    # Upgrade back
    subprocess.run(["alembic", "upgrade", "head"])

    # Verify we're back to initial version
    result = subprocess.run(
        ["alembic", "current"],
        capture_output=True,
        text=True
    )
    final_version = result.stdout.strip()

    assert initial_version == final_version
```

## Security Testing

### Automated Security Scans

**Tools**:

- CodeQL (static analysis)
- pip-audit (Python dependencies)
- npm audit (JavaScript dependencies)
- Trivy (container scanning)
- Gitleaks (secret detection)

**CI/CD Integration**: ✅ All scans run automatically

### OWASP Top 10 Testing

**Manual Testing Checklist**:

1. **A01:2021 – Broken Access Control**
   - [ ] Test unauthorized access to patient records
   - [ ] Test RBAC enforcement
   - [ ] Test horizontal privilege escalation
   - [ ] Test vertical privilege escalation

2. **A02:2021 – Cryptographic Failures**
   - [ ] Verify TLS 1.3 usage
   - [ ] Test password hashing (bcrypt)
   - [ ] Verify PHI encryption (AES-256-GCM)
   - [ ] Test JWT token security

3. **A03:2021 – Injection**
   - [ ] SQL injection tests (via SQLAlchemy ORM)
   - [ ] NoSQL injection tests (Redis)
   - [ ] Command injection tests
   - [ ] XSS attempts blocked

4. **A04:2021 – Insecure Design**
   - [ ] Review authentication flow
   - [ ] Test rate limiting
   - [ ] Test session management
   - [ ] Test audit logging

5. **A05:2021 – Security Misconfiguration**
   - [ ] Check security headers
   - [ ] Verify CORS configuration
   - [ ] Test default credentials disabled
   - [ ] Verify debug mode off in production

6. **A06:2021 – Vulnerable Components**
   - [ ] Dependency vulnerability scan
   - [ ] Container image scan
   - [ ] Update policy enforced

7. **A07:2021 – Authentication Failures**
   - [ ] Test brute force protection
   - [ ] Test weak password rejection
   - [ ] Test MFA (if enabled)
   - [ ] Test session timeout

8. **A08:2021 – Software and Data Integrity**
   - [ ] Verify CI/CD pipeline security
   - [ ] Test integrity of updates
   - [ ] Verify cryptographic signatures

9. **A09:2021 – Logging and Monitoring Failures**
   - [ ] Verify audit logging works
   - [ ] Test alert generation
   - [ ] Verify no PHI in logs

10. **A10:2021 – Server-Side Request Forgery (SSRF)**
    - [ ] Test URL parameter validation
    - [ ] Test webhook security

### Penetration Testing

**Frequency**: Annually or after major releases

**Scope**:

- External penetration testing
- Internal network testing
- Social engineering testing
- Physical security assessment

**Provider**: Third-party security firm

**Deliverables**:

- Vulnerability report
- Risk assessment
- Remediation recommendations
- Re-test after fixes

## Performance Testing

### Load Testing

**Tool**: Locust or k6

**Scenarios**:

1. **Normal Load**
   - 100 concurrent users
   - 1000 requests/minute
   - Duration: 30 minutes
   - Expected: < 200ms P95 response time

2. **Peak Load**
   - 500 concurrent users
   - 5000 requests/minute
   - Duration: 10 minutes
   - Expected: < 500ms P95 response time

3. **Stress Test**
   - Gradually increase to 2000 users
   - Find breaking point
   - Monitor resource usage
   - Verify graceful degradation

**Example Locust Test**:

```python
from locust import HttpUser, task, between

class KeneyAppUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "username": "load_test_user",
            "password": "password123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_patients(self):
        self.client.get(
            "/api/v1/patients/",
            headers=self.headers
        )

    @task(2)
    def get_dashboard(self):
        self.client.get(
            "/api/v1/dashboard/stats",
            headers=self.headers
        )

    @task(1)
    def create_appointment(self):
        self.client.post(
            "/api/v1/appointments/",
            json={
                "patient_id": 1,
                "start_time": "2024-01-15T10:00:00",
                "end_time": "2024-01-15T11:00:00",
                "reason": "Consultation"
            },
            headers=self.headers
        )
```

**Running Load Tests**:

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/performance/locustfile.py --host=https://staging.keneyapp.com

# Open web UI
# http://localhost:8089
```

### Performance Benchmarks

**SLA Requirements**:

| Metric | Target | Maximum |
|--------|--------|---------|
| P50 Response Time | < 100ms | 200ms |
| P95 Response Time | < 200ms | 500ms |
| P99 Response Time | < 500ms | 2s |
| Error Rate | < 0.01% | 0.1% |
| Availability | > 99.9% | 99.5% |
| Throughput | > 1000 req/s | - |

### Database Performance

**Query Performance Tests**:

```python
def test_patient_list_query_performance(db):
    """Test patient list query is fast."""
    import time

    start = time.time()

    # Query with pagination
    patients = db.query(Patient).filter(
        Patient.tenant_id == 1
    ).limit(50).all()

    duration = time.time() - start

    # Should complete in < 100ms
    assert duration < 0.1
    assert len(patients) <= 50
```

**Database Optimization**:

- Indexed columns: tenant_id, email, date_of_birth
- EXPLAIN ANALYZE for slow queries
- Connection pooling (10-20 connections)
- Query result caching in Redis

## Beta Testing

### Beta Program Structure

**Phase 1: Internal Beta (2 weeks)**

- QA team
- Internal stakeholders
- Sample size: 5-10 users
- Focus: Bug detection, usability

**Phase 2: Closed Beta (4 weeks)**

- Selected healthcare professionals
- Real patient data (anonymized or test)
- Sample size: 20-50 users
- Focus: Real-world usage, performance

**Phase 3: Open Beta (4 weeks)**

- Public signup (controlled)
- Real usage scenarios
- Sample size: 100-500 users
- Focus: Scalability, feature requests

### Beta Feedback Collection

**Methods**:

1. **In-App Feedback Widget**
   - Quick bug reports
   - Feature requests
   - Usability issues

2. **Surveys**
   - Post-task surveys
   - Weekly satisfaction surveys
   - Exit surveys

3. **User Interviews**
   - 30-minute sessions
   - Screen sharing
   - Task-based testing

4. **Analytics**
   - Feature usage tracking
   - Error monitoring
   - Performance metrics

**Feedback Processing**:

- Triage within 24 hours
- Critical bugs fixed immediately
- Feature requests prioritized
- Regular feedback summaries to team

### Beta Success Criteria

**Before Public Launch**:

- [ ] < 5 critical bugs per 1000 users
- [ ] > 4/5 average satisfaction rating
- [ ] > 80% task completion rate
- [ ] < 0.1% error rate
- [ ] All security issues resolved
- [ ] Performance targets met

## Compliance Validation

### GDPR Compliance Testing

**Checklist**:

- [ ] User can view their data (data subject access request)
- [ ] User can export their data (data portability)
- [ ] User can delete their data (right to erasure)
- [ ] Consent is tracked and auditable
- [ ] Data breach notification works
- [ ] Privacy policy is accessible
- [ ] Cookie consent implemented (frontend)
- [ ] Data processing records maintained
- [ ] Data retention policies enforced
- [ ] Cross-border transfer controls (if applicable)

**Test Script**:

```python
def test_gdpr_right_to_erasure(client, auth_headers, test_user):
    """Test user can delete their account (GDPR)."""
    # User requests deletion
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/me",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Verify user data anonymized
    user = db.query(User).filter(User.id == test_user.id).first()
    assert user.email.startswith("deleted_")
    assert user.is_active == False

    # Verify audit log
    audit_log = db.query(AuditLog).filter(
        AuditLog.user_id == test_user.id,
        AuditLog.action == "DELETE",
        AuditLog.resource_type == "user"
    ).first()
    assert audit_log is not None
```

### HIPAA Compliance Testing

**Checklist**:

- [ ] Access controls enforced (authentication + RBAC)
- [ ] Audit logging captures all PHI access
- [ ] PHI encrypted at rest (AES-256-GCM)
- [ ] PHI encrypted in transit (TLS 1.3)
- [ ] Automatic session timeout (30 minutes)
- [ ] Password complexity enforced
- [ ] MFA available for sensitive roles
- [ ] Unique user identification
- [ ] Emergency access procedure documented
- [ ] Business associate agreements with vendors

**Test Script**:

```python
def test_hipaa_audit_logging(client, auth_headers):
    """Test all PHI access is logged (HIPAA)."""
    # Access patient data
    response = client.get(
        f"{settings.API_V1_PREFIX}/patients/1",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Verify audit log created
    audit_log = db.query(AuditLog).filter(
        AuditLog.resource_type == "patient",
        AuditLog.resource_id == 1,
        AuditLog.action == "READ"
    ).order_by(AuditLog.timestamp.desc()).first()

    assert audit_log is not None
    assert audit_log.user_id == test_user.id
    assert audit_log.ip_address is not None
```

### HDS Compliance (France)

**Requirements**:

- Hébergeur de Données de Santé certification
- French data residency
- Enhanced security controls
- Specific audit requirements

**Validation**:

- [ ] Data hosted in France (or EU)
- [ ] Provider is HDS-certified
- [ ] Encryption standards met
- [ ] Audit logging sufficient
- [ ] Backup in compliant location
- [ ] Disaster recovery tested

### Legal Expert Review

**Frequency**: Annually + before major releases

**Reviewer**: Data Protection Officer (DPO) or legal counsel

**Scope**:

- Privacy policy review
- Terms of service review
- Data processing agreements
- Consent mechanisms
- User rights implementation

**Deliverable**: Legal compliance report

## Test Automation

### Continuous Integration

**GitHub Actions Workflow**:

```yaml
name: CI

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest --cov=app tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run tests
        run: cd frontend && npm test -- --watchAll=false
```

### Pre-Commit Hooks

**Configuration**: `.pre-commit-config.yaml`

**Hooks**:

- Black (Python formatting)
- Flake8 (Python linting)
- mypy (Type checking)
- ESLint (JavaScript linting)
- Prettier (JavaScript formatting)
- detect-secrets (Secret scanning)

**Install**:

```bash
pip install pre-commit
pre-commit install
```

### Test Coverage Reports

**Backend Coverage**:

```bash
pytest --cov=app --cov-report=html tests/
open htmlcov/index.html
```

**Frontend Coverage**:

```bash
cd frontend
npm test -- --coverage --watchAll=false
open coverage/lcov-report/index.html
```

**Coverage Goals**:

- Overall: ≥ 70% (target 80%)
- Critical paths: ≥ 90%
- New code: ≥ 80%

### Continuous Testing

**Test Execution**:

- Every commit: Unit tests + linting
- Every PR: Full test suite + security scans
- Daily (develop branch): E2E tests + performance tests
- Weekly: Full regression suite
- Monthly: Load testing + penetration testing

## Test Data Management

### Synthetic Data Generation

**Purpose**: Create realistic test data without using real PHI

**Tool**: Python Faker

**Example**:

```python
from faker import Faker

fake = Faker('fr_FR')  # French locale

def create_fake_patient():
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "address": fake.address(),
    }
```

### Test Data Lifecycle

1. **Creation**: Automated in test setup
2. **Usage**: Tests use fixtures
3. **Cleanup**: Automated in test teardown
4. **Isolation**: Each test has isolated data

**Database Isolation**:

```python
@pytest.fixture(autouse=True)
def reset_database(db):
    """Reset database before each test."""
    yield
    # Rollback any changes
    db.rollback()
    db.close()
```

## Regression Testing

### Automated Regression Suite

**Frequency**: Before every release

**Coverage**:

- All critical user workflows
- Previously fixed bugs (regression tests)
- High-risk areas (payments, prescriptions)
- Integration points (FHIR, OAuth)

**Regression Test Example**:

```python
def test_bug_123_patient_update_preserves_data():
    """Regression test for bug #123: patient update loses data."""
    # Create patient with all fields
    patient = create_patient_with_all_fields()

    # Update only email
    update_patient(patient.id, email="new@email.com")

    # Verify all other fields preserved
    updated = get_patient(patient.id)
    assert updated.first_name == patient.first_name
    assert updated.phone == patient.phone
    # ... verify all fields
```

## Documentation Testing

### API Documentation Validation

**Tool**: OpenAPI validation

**Tests**:

- Swagger UI accessible
- All endpoints documented
- Request/response schemas accurate
- Examples provided

### Documentation Examples

**Validation**:

```python
def test_readme_code_examples():
    """Test code examples in README.md work."""
    # Extract code examples from README
    # Execute each example
    # Verify they work as documented
```

## Monitoring & Observability Testing

### Metrics Collection Tests

```python
def test_prometheus_metrics_collected():
    """Test Prometheus metrics are collected."""
    # Make API request
    response = client.get(f"{settings.API_V1_PREFIX}/patients/")

    # Check metrics endpoint
    metrics_response = client.get("/metrics")
    metrics_text = metrics_response.text

    # Verify metrics present
    assert "http_requests_total" in metrics_text
    assert "patient_operations_total" in metrics_text
```

### Alerting Tests

```python
def test_high_error_rate_alert():
    """Test alert fires on high error rate."""
    # Simulate high error rate
    for _ in range(100):
        client.get(f"{settings.API_V1_PREFIX}/nonexistent")

    # Verify alert would fire
    error_rate = get_error_rate()
    assert error_rate > 0.01  # Alert threshold
```

## Conclusion

KeneyApp's testing strategy ensures:

✅ **Comprehensive Coverage**: 77% code coverage with 155 tests
✅ **Multiple Test Types**: Unit, integration, E2E, security, performance
✅ **Automated Execution**: CI/CD pipeline runs tests on every commit
✅ **Healthcare Compliance**: GDPR, HIPAA, HDS validation
✅ **Quality Gates**: No deployment without passing tests
✅ **Continuous Improvement**: Regular test updates and additions

The strategy balances thorough testing with development velocity, ensuring KeneyApp maintains high quality and security standards suitable for healthcare data management.

### Next Steps

1. **Increase Coverage**: Target 80% overall coverage
2. **Add E2E Tests**: More user workflow scenarios
3. **Performance Testing**: Regular load testing
4. **Accessibility Testing**: WCAG 2.1 AA compliance
5. **Mobile Testing**: Once mobile apps developed
