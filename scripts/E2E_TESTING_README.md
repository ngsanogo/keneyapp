# KeneyApp End-to-End Testing Suite

Comprehensive testing suite for validating KeneyApp's full stack: backend API, frontend, database, and integration.

## 📋 Overview

This testing suite provides:

1. **Test Data Generation** - Create realistic fake data for testing
2. **API Testing** - Comprehensive testing of all REST and GraphQL endpoints
3. **Frontend-Backend Validation** - Verify integration and alignment
4. **End-to-End Orchestration** - Run complete test workflows

## 🚀 Quick Start

### Prerequisites

```bash
# Install testing dependencies
pip install -r requirements-e2e-tests.txt

# Ensure services are running
docker compose up -d

# Wait for services to be healthy
docker compose ps
```

### Run Complete E2E Test Suite

```bash
# Run everything - seeds data, validates, and tests
python scripts/run_full_e2e_tests.py

# Run with custom patient count
python scripts/run_full_e2e_tests.py --patient-count 200

# Clean existing data first
python scripts/run_full_e2e_tests.py --clean-first

# Skip data seeding (use existing data)
python scripts/run_full_e2e_tests.py --skip-seed
```

## 📊 Individual Test Scripts

### 1. Seed Test Data

Generate realistic fake data for testing:

```bash
# Generate 100 test patients with related data
python scripts/seed_test_data.py --count 100

# Generate for specific tenant
python scripts/seed_test_data.py --count 50 --tenant-id 1

# Clean all test data
python scripts/seed_test_data.py --clean-only

# Clean and regenerate
python scripts/seed_test_data.py --clean --count 100
```

**What it generates:**
- Patients with French healthcare identifiers (INS, NIR)
- Users (doctors, nurses, receptionists, admins)
- Appointments (scheduled, completed, cancelled)
- Prescriptions with medications
- Medical documents
- Realistic French names, addresses, phone numbers

### 2. Test All APIs

Comprehensive API endpoint testing:

```bash
# Test all endpoints
python scripts/test_all_apis.py

# With custom backend URL
python scripts/test_all_apis.py --base-url http://localhost:8000

# Verbose output
python scripts/test_all_apis.py --verbose
```

**What it tests:**
- ✅ Authentication flow (login, JWT tokens)
- ✅ Patient CRUD operations
- ✅ Appointment management
- ✅ Prescription handling
- ✅ User management
- ✅ Tenant operations
- ✅ Dashboard statistics
- ✅ Lab tests
- ✅ Medical documents
- ✅ Secure messaging
- ✅ FHIR R4 endpoints
- ✅ GraphQL queries
- ✅ Prometheus metrics

**Output:**
```
🚀 KeneyApp API Comprehensive Test Suite
================================================================================
✅ POST   /api/v1/auth/login                      [200] 0.125s
✅ GET    /api/v1/patients                        [200] 0.034s
✅ POST   /api/v1/patients                        [201] 0.089s
...
📊 Test Results Summary
================================================================================
Total Requests:  45
✅ Passed:        42 (93.3%)
❌ Failed:        3 (6.7%)
Avg Response:    0.056s
```

### 3. Validate Frontend-Backend Alignment

Ensure frontend and backend are properly integrated:

```bash
# Validate integration
python scripts/validate_frontend_backend.py

# With custom URLs
python scripts/validate_frontend_backend.py \
  --backend http://localhost:8000 \
  --frontend http://localhost:3000
```

**What it validates:**
- ✅ Backend health and accessibility
- ✅ Frontend serving and assets
- ✅ CORS configuration
- ✅ Critical API endpoints exist
- ✅ API response schemas
- ✅ Authentication flow
- ✅ Static asset accessibility
- ✅ API documentation (Swagger, ReDoc)

**Output:**
```
🔍 Frontend-Backend Alignment Validation
================================================================================
✅ Backend Health: Backend is running: KeneyApp v1.0.0
✅ Frontend Health: Frontend is serving HTML correctly
✅ CORS Headers: CORS headers are configured
✅ Authentication: Login returns access token
✅ Token Authentication: Token works for protected endpoints
...
📊 Validation Summary
================================================================================
✅ All validations passed! Frontend and backend are properly aligned.
```

## 📈 Test Reports

The E2E orchestrator generates detailed JSON reports:

```bash
# Reports are saved to test_reports/
test_reports/
  e2e_report_20251129_143022.json
  e2e_report_20251129_145315.json
```

**Report structure:**
```json
{
  "timestamp": "2025-11-29T14:30:22",
  "duration_seconds": 45.3,
  "environment": {
    "backend_url": "http://localhost:8000",
    "frontend_url": "http://localhost:3000",
    "python_version": "3.12.0",
    "patient_count": 100
  },
  "summary": {
    "total_stages": 4,
    "passed": 4,
    "failed": 0,
    "success_rate": "100.0%"
  },
  "results": {
    "Seed Data": {"success": true, "output_sample": "..."},
    "Frontend-Backend Validation": {"success": true, "output_sample": "..."},
    "API Tests": {"success": true, "output_sample": "..."},
    "Database Check": {"success": true, "output_sample": "..."}
  }
}
```

## 🎯 Use Cases

### Development Workflow

```bash
# After making changes, run quick validation
python scripts/test_all_apis.py

# Validate frontend changes
python scripts/validate_frontend_backend.py

# Full regression test
python scripts/run_full_e2e_tests.py --skip-seed
```

### CI/CD Pipeline

```bash
# In GitHub Actions / GitLab CI
- name: E2E Tests
  run: |
    docker compose up -d
    sleep 10
    pip install -r requirements-e2e-tests.txt
    python scripts/run_full_e2e_tests.py --patient-count 50
```

### Load Testing Preparation

```bash
# Generate large dataset for load testing
python scripts/seed_test_data.py --count 1000

# Verify system handles load
python scripts/test_all_apis.py --verbose
```

### Demo Environment Setup

```bash
# Create realistic demo data
python scripts/seed_test_data.py --clean --count 50

# Verify everything works
python scripts/validate_frontend_backend.py
```

## 🔧 Configuration

### Environment Variables

Test scripts respect these environment variables:

```bash
# Backend URL
export API_BASE_URL=http://localhost:8000

# Frontend URL
export FRONTEND_URL=http://localhost:3000

# Database connection (for seeding)
export DATABASE_URL=postgresql://keneyapp:keneyapp123@localhost:5432/keneyapp
```

### Custom Test Data

Modify `scripts/seed_test_data.py` to customize:

- Patient demographics
- Medical conditions and allergies
- Appointment patterns
- Prescription types
- French healthcare identifiers

## 📊 Performance Benchmarks

Expected performance for E2E suite:

| Stage | Duration | Success Rate |
|-------|----------|--------------|
| Seed 100 patients | ~10s | 100% |
| API Tests (45 endpoints) | ~30s | >95% |
| Frontend Validation | ~5s | 100% |
| **Total E2E Suite** | **~45s** | **>95%** |

## 🐛 Troubleshooting

### "Backend is not reachable"

```bash
# Check if backend is running
docker compose ps keneyapp_backend

# Check backend logs
docker logs keneyapp_backend --tail 50

# Restart backend
docker compose restart backend
```

### "Authentication failed"

```bash
# Verify admin user exists
docker exec keneyapp_backend python scripts/init_db.py

# Check credentials in test scripts (default: admin/admin123)
```

### "Database connection failed"

```bash
# Check database is healthy
docker compose ps keneyapp_db

# Check database logs
docker logs keneyapp_db --tail 50

# Verify migrations are applied
docker exec keneyapp_backend alembic current
```

### "No patients found"

```bash
# Seed test data
python scripts/seed_test_data.py --count 100

# Or run full E2E which includes seeding
python scripts/run_full_e2e_tests.py --clean-first
```

## 🎓 Best Practices

1. **Run tests before commits**
   ```bash
   python scripts/test_all_apis.py
   ```

2. **Clean test data regularly**
   ```bash
   python scripts/seed_test_data.py --clean-only
   ```

3. **Use appropriate patient counts**
   - Development: 10-50 patients
   - Testing: 100-200 patients
   - Demo: 50-100 patients
   - Load testing: 1000+ patients

4. **Review test reports**
   ```bash
   cat test_reports/e2e_report_*.json | jq .summary
   ```

5. **Monitor performance trends**
   - Track average response times
   - Watch for degradation over time
   - Identify slow endpoints

## 🔐 Security Testing

The test suite includes basic security validation:

- ✅ JWT token authentication
- ✅ Role-based access control
- ✅ CORS configuration
- ✅ Protected endpoint access

For comprehensive security testing, use additional tools:
- `bandit` for Python security issues
- `npm audit` for frontend vulnerabilities
- OWASP ZAP for penetration testing

## 📚 Additional Resources

- [Testing Guide](../docs/TESTING_GUIDE.md)
- [Development Guide](../docs/DEVELOPMENT.md)
- [API Documentation](http://localhost:8000/api/v1/docs)
- [Architecture Overview](../ARCHITECTURE.md)

## 🤝 Contributing

Improvements to the test suite are welcome:

1. Add new test scenarios
2. Improve test data realism
3. Add performance benchmarks
4. Enhance reporting
5. Add new validation checks

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## 📝 License

Part of KeneyApp - see main [LICENSE](../LICENSE) file.
