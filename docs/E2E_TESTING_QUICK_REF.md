# E2E Testing Quick Reference

## Overview

KeneyApp includes a comprehensive End-to-End (E2E) testing suite to validate the entire system - database, backend APIs, frontend-backend integration, and healthcare compliance features.

## Quick Start

### Prerequisites

- Docker Compose stack running (`docker compose up -d`)
- Backend accessible at `http://localhost:8000`
- Frontend accessible at `http://localhost:3000`
- Testing dependencies installed (included in backend Docker image)

### Run E2E Tests

```bash
# Full E2E test suite (seed data + validate + test + verify)
make e2e-full

# Quick validation (skip seeding, use existing data)
make e2e-quick

# Clean and reseed before running tests
make e2e-full-clean
```

### Individual Test Components

```bash
# 1. Seed test database with fake data
make e2e-seed              # Seed 100 records
make e2e-seed-clean        # Clean first, then seed

# 2. Validate frontend-backend alignment
make e2e-validate

# 3. Test all API endpoints
make e2e-test-api

# 4. Install testing dependencies (if not in Docker)
make e2e-install
```

## Test Components

### 1. Test Data Seeder (`scripts/seed_test_data.py`)

Generates realistic fake data using the Faker library with French locale support:

- **Tenants**: Creates test organizations
- **Users**: Admin, doctors, nurses, receptionists (4 roles)
- **Patients**: With French healthcare data (INS, NIR, DMP)
- **Appointments**: Past, present, future appointments
- **Prescriptions**: With medications and dosages
- **Lab Results**: Test types and results
- **Documents**: Medical records, DICOM studies
- **Messages**: Secure E2E encrypted communications

**Usage:**
```bash
# Seed 100 records per entity type
docker compose exec backend python scripts/seed_test_data.py --count 100

# Clean database first, then seed 50 records
docker compose exec backend python scripts/seed_test_data.py --clean --count 50

# Use specific tenant ID
docker compose exec backend python scripts/seed_test_data.py --tenant-id 2
```

### 2. API Endpoint Tester (`scripts/test_all_apis.py`)

Comprehensive test suite covering 45+ endpoints across all modules:

- ✅ Authentication (login, logout, token refresh)
- ✅ CRUD operations (patients, appointments, prescriptions, users)
- ✅ Dashboard and analytics endpoints
- ✅ FHIR interoperability (metadata, Patient resources)
- ✅ GraphQL queries
- ✅ Prometheus metrics endpoint
- ✅ Health checks

**Usage:**
```bash
# Run all API tests with verbose output
docker compose exec backend python scripts/test_all_apis.py --verbose

# Test against different backend URL
docker compose exec backend python scripts/test_all_apis.py --base-url http://api.example.com
```

### 3. Frontend-Backend Validator (`scripts/validate_frontend_backend.py`)

Validates frontend-backend integration and alignment:

- ✅ Backend health and version check
- ✅ Frontend serving and accessibility
- ✅ CORS configuration validation
- ✅ API endpoint availability (health, auth, CRUD)
- ✅ API contract validation (schema compatibility)
- ✅ Authentication flow (login → token → protected endpoint)
- ✅ API documentation accessibility (Swagger, ReDoc, OpenAPI)
- ✅ Static asset serving (favicon, JS bundles, CSS)

**Usage:**
```bash
# Validate with default URLs (localhost)
docker compose exec backend python scripts/validate_frontend_backend.py

# Custom backend and frontend URLs
docker compose exec backend python scripts/validate_frontend_backend.py \
  --backend http://localhost:8000 \
  --frontend http://frontend:3000
```

### 4. E2E Test Orchestrator (`scripts/run_full_e2e_tests.py`)

Master script that runs all tests in sequence with comprehensive reporting:

**Stages:**
1. **Seed**: Populate database with test data
2. **Validate**: Check frontend-backend alignment
3. **Test**: Execute comprehensive API tests
4. **Verify**: Final health checks and cleanup

**Features:**
- JSON test report generation (`e2e_test_report.json`)
- Colored console output
- Error aggregation and summary
- Stage-by-stage execution with timing

**Usage:**
```bash
# Full test suite
docker compose exec backend python scripts/run_full_e2e_tests.py

# Clean database first
docker compose exec backend python scripts/run_full_e2e_tests.py --clean-first

# Skip seeding (use existing data)
docker compose exec backend python scripts/run_full_e2e_tests.py --skip-seed

# Custom record count
docker compose exec backend python scripts/run_full_e2e_tests.py --count 200
```

## Docker Integration

All E2E test scripts are included in the backend Docker image and can be executed via `docker compose exec`:

```bash
# Start the stack
docker compose up -d

# Wait for backend to be healthy
docker compose ps

# Run tests
docker compose exec backend python scripts/run_full_e2e_tests.py
```

## Test Report

The E2E orchestrator generates a JSON report (`e2e_test_report.json`) with:

- Overall test status (✅ PASSED / ❌ FAILED)
- Execution time and timestamps
- Stage-by-stage results (seed, validate, test, verify)
- Error details and failed checks
- Statistics (total checks, pass rate)

**Example:**
```json
{
  "status": "PASSED",
  "started_at": "2025-11-29T14:00:00.123456",
  "completed_at": "2025-11-29T14:05:30.654321",
  "execution_time": 330.53,
  "stages": {
    "seed": {
      "status": "PASSED",
      "records_created": 800,
      "execution_time": 45.2
    },
    "validate": {
      "status": "PASSED",
      "checks_passed": 12,
      "checks_failed": 4,
      "pass_rate": 75.0
    },
    "test": {
      "status": "PASSED",
      "total_requests": 45,
      "passed": 32,
      "failed": 13,
      "avg_response_time": 0.095
    }
  }
}
```

## CI/CD Integration

Add E2E tests to your CI/CD pipeline:

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start Docker Compose stack
        run: docker compose up -d
      
      - name: Wait for backend
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
      
      - name: Run E2E tests
        run: docker compose exec -T backend python scripts/run_full_e2e_tests.py
      
      - name: Upload test report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: e2e-test-report
          path: e2e_test_report.json
```

## Troubleshooting

### Dependencies Not Found

If you see `ModuleNotFoundError: No module named 'faker'`:

```bash
# Rebuild backend image with latest requirements
docker compose build backend
docker compose up -d backend
```

### Authentication Failures

If API tests fail with 401/403:

```bash
# Verify demo users exist
docker compose exec db psql -U postgres -d keneyapp -c "SELECT username, role FROM users;"

# Expected users: admin, doctor, nurse, receptionist
# If missing, reseed database:
docker compose exec backend python scripts/init_db.py
```

### Database Connection Issues

```bash
# Check database is running
docker compose ps db

# Check backend can connect
docker compose exec backend python -c "from app.core.database import SessionLocal; db = SessionLocal(); print('✅ Connected'); db.close()"
```

### Frontend Not Accessible

```bash
# Check frontend is running
docker compose ps frontend

# Check frontend logs
docker compose logs frontend

# Restart frontend
docker compose restart frontend
```

## Best Practices

1. **Run E2E tests in isolated environment**: Use Docker Compose for consistent, reproducible tests
2. **Clean data between runs**: Use `--clean-first` flag to avoid conflicts with existing data
3. **Monitor test reports**: Review `e2e_test_report.json` for trends and regression detection
4. **Adjust record counts**: For quick validation, use `--count 10`; for stress testing, use `--count 1000+`
5. **Automate in CI/CD**: Add E2E tests to your GitHub Actions workflow for every PR

## Performance Benchmarks

Based on Docker Compose stack with default configuration:

| Operation | Duration | Notes |
|-----------|----------|-------|
| Seed 100 records | ~45s | Includes all entity types |
| Validate frontend-backend | ~5s | 16 validation checks |
| Test 45 API endpoints | ~10s | With authentication |
| Full E2E suite (clean + seed + test) | ~90s | End-to-end validation |

## French Healthcare Features Tested

The E2E suite specifically validates French healthcare integration:

- ✅ **INS (Identifiant National de Santé)**: Patient unique identifier generation and validation
- ✅ **NIR (Numéro d'Inscription au Répertoire)**: Social security number format
- ✅ **DMP (Dossier Médical Partagé)**: Shared medical record integration
- ✅ **MSSanté**: Secure health messaging with E2E encryption
- ✅ **CPS (Carte de Professionnel de Santé)**: Healthcare professional credentials
- ✅ **Medical terminologies**: ICD-11, SNOMED CT, LOINC, ATC

See `docs/FRENCH_HEALTHCARE_IMPLEMENTATION.md` for details.

## Next Steps

- Review failed tests in `e2e_test_report.json`
- Fix identified API issues (404s, 422s, 500s)
- Add endpoint-specific tests for complex workflows
- Integrate with monitoring/alerting (Prometheus, Grafana)
- Set up scheduled E2E test runs (daily/weekly)

For detailed implementation guides, see `scripts/E2E_TESTING_README.md`.
