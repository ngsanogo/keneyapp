# End-to-End (E2E) Integration Testing

This document describes the comprehensive E2E testing infrastructure for KeneyApp.

## Overview

The E2E testing framework provides:

- **Complete Stack Testing**: Tests all components in an isolated Docker environment
- **Structured Logging**: JSON-formatted results with performance metrics
- **Automated Analysis**: Python-based result analysis with recommendations
- **Production Parity**: Tests mimic real-world usage patterns

## Quick Start

### Run All E2E Tests

```bash
./scripts/run_e2e_tests.sh
```

This single command will:

1. ✅ Start isolated Docker environment (PostgreSQL, Redis, Backend, Celery)
2. ✅ Run comprehensive test suite
3. ✅ Collect logs and metrics
4. ✅ Analyze results and generate report
5. ✅ Provide cleanup options

### View Results

After running tests, check:

- **Analysis Report**: `logs/e2e_analysis_report.txt` (human-readable summary)
- **JSON Results**: `logs/e2e_integration_results.json` (machine-readable data)
- **Detailed Log**: `logs/e2e_integration_test.log` (test execution log)
- **JUnit XML**: `test_results/e2e_results.xml` (CI integration)

## What's Tested

### 1. Health Checks

- Root endpoint availability
- Health endpoint status
- API documentation access

### 2. Authentication

- Login for all user roles:
  - Super Admin
  - Admin (Tenant Owner)
  - Doctor
  - Nurse
  - Receptionist
- JWT token validation
- Token expiry handling

### 3. Patient Workflows

- **Create Patient** with PHI encryption
- **List Patients** with pagination
- **Get Patient** details
- **Update Patient** information
- **Delete Patient** (soft delete)
- **Tenant Isolation** validation

### 4. RBAC (Role-Based Access Control)

- Admin: Full CRUD permissions
- Doctor: Read access only
- Nurse: Forbidden on patient operations
- Receptionist: Forbidden on patient operations

### 5. Cache Validation

- Cache hit performance
- Cache invalidation on updates
- Cache warming strategies

### 6. GraphQL API

- Patient list queries
- Field selection
- Performance comparison with REST

### 7. Metrics & Monitoring

- Prometheus metrics endpoint
- Request counters
- Performance histograms

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    E2E Test Runner                          │
│  (tests/test_e2e_integration.py)                            │
│  ├── E2ETestLogger (structured logging)                     │
│  ├── Authentication Fixtures (5 roles)                      │
│  └── Test Classes (8 test suites)                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Docker Compose Environment                      │
│  (docker-compose.e2e.yml)                                   │
│  ├── PostgreSQL (port 5433)                                 │
│  ├── Redis (port 6380)                                      │
│  ├── Backend API (port 8000)                                │
│  ├── Celery Worker                                          │
│  └── E2E Test Container                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                Results & Analysis                            │
│  ├── logs/e2e_integration_results.json                      │
│  ├── logs/e2e_integration_test.log                          │
│  ├── test_results/e2e_results.xml                           │
│  └── logs/e2e_analysis_report.txt                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            Python Analyzer (optional)                        │
│  (scripts/analyze_e2e_results.py)                           │
│  ├── Summary Report                                         │
│  ├── Performance Analysis                                   │
│  ├── Failure Investigation                                  │
│  └── Recommendations                                        │
└─────────────────────────────────────────────────────────────┘
```

## Test Structure

### E2ETestLogger

Structured logging framework that captures:

- Test execution details
- Performance metrics (response times, operation durations)
- Errors and tracebacks
- Final summary statistics

### Test Classes

1. **TestE2EHealthChecks**: Basic endpoint availability
2. **TestE2EPatientWorkflows**: Full CRUD lifecycle
3. **TestE2ERBACEnforcement**: Permission validation
4. **TestE2ECacheValidation**: Cache behavior
5. **TestE2EGraphQL**: GraphQL API functionality
6. **TestE2EMetricsAndMonitoring**: Observability

## Performance Benchmarks

Expected performance (local Docker environment):

| Operation | Target | Warning Threshold |
|-----------|--------|-------------------|
| Authentication | < 200ms | > 500ms |
| Patient Create | < 300ms | > 500ms |
| Patient List | < 200ms | > 500ms |
| Patient Get | < 150ms | > 500ms |
| Patient Update | < 300ms | > 500ms |
| Cache Hit | < 50ms | > 200ms |
| GraphQL Query | < 200ms | > 500ms |

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run E2E Tests
  run: |
    ./scripts/run_e2e_tests.sh

- name: Upload Test Results
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: e2e-test-results
    path: |
      logs/e2e_integration_results.json
      logs/e2e_analysis_report.txt
      test_results/e2e_results.xml
```

### JUnit XML Output

The test suite generates JUnit XML for CI integration:

```bash
pytest tests/test_e2e_integration.py \
  --junitxml=test_results/e2e_results.xml
```

## Troubleshooting

### Tests Failing to Connect

**Issue**: `Connection refused` errors

**Solution**:

1. Check Docker services are running:

   ```bash
   docker-compose -f docker-compose.e2e.yml ps
   ```

2. Check backend logs:

   ```bash
   docker-compose -f docker-compose.e2e.yml logs backend
   ```

3. Verify health checks:

   ```bash
   curl http://localhost:8000/health
   ```

### Slow Test Execution

**Issue**: Tests take > 2 minutes

**Solution**:

1. Check Docker resources (CPU, memory)
2. Review performance metrics in results
3. Consider parallel execution:

   ```bash
   pytest tests/test_e2e_integration.py -n auto
   ```

### Authentication Failures

**Issue**: `401 Unauthorized` errors

**Solution**:

1. Check bootstrap admin is enabled:

   ```bash
   docker-compose -f docker-compose.e2e.yml exec backend \
     printenv ENABLE_BOOTSTRAP_ADMIN
   ```

2. Verify database seed data:

   ```bash
   docker-compose -f docker-compose.e2e.yml exec backend \
     python scripts/init_db.py
   ```

### Cache Issues

**Issue**: Cache hit rates < 50%

**Solution**:

1. Check Redis is running:

   ```bash
   docker-compose -f docker-compose.e2e.yml exec redis redis-cli ping
   ```

2. Verify cache keys:

   ```bash
   docker-compose -f docker-compose.e2e.yml exec redis \
     redis-cli KEYS "*"
   ```

## Development

### Adding New Tests

1. Add test method to appropriate test class in `tests/test_e2e_integration.py`
2. Use `e2e_logger` fixture for structured logging
3. Record performance metrics for operations
4. Follow existing patterns for assertions

Example:

```python
def test_new_feature(self, e2e_logger: E2ETestLogger, admin_auth: Dict):
    """Test new feature functionality"""
    e2e_logger.log_info("Testing new feature")

    start_time = time.time()

    # Make request
    response = requests.get(
        f"{BASE_URL}/api/v1/new-feature",
        headers=admin_auth["headers"]
    )

    duration_ms = (time.time() - start_time) * 1000
    e2e_logger.record_metric("new_feature_duration", duration_ms, "ms")

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data

    e2e_logger.log_test_result("test_new_feature", "passed", duration_ms / 1000)
```

### Extending Analysis

To add custom analysis in `scripts/analyze_e2e_results.py`:

1. Add method to `E2EResultsAnalyzer` class
2. Call method in `generate_full_report()`
3. Use structured data from JSON results

Example:

```python
def analyze_custom_metric(self) -> str:
    """Analyze custom metric"""
    lines = []
    lines.append("🔍 Custom Analysis")
    lines.append("-" * 80)

    # Extract data
    metrics = self.results.get('performance_metrics', {})
    custom_data = metrics.get('custom_metric', {})

    # Analyze
    if custom_data.get('value', 0) > threshold:
        lines.append("  ⚠️  Custom metric exceeds threshold")
    else:
        lines.append("  ✅ Custom metric within bounds")

    lines.append("")
    return "\n".join(lines)
```

## Best Practices

### Test Design

1. **Independence**: Each test should be independent and idempotent
2. **Cleanup**: Use fixtures and teardown to clean up test data
3. **Isolation**: Tests run in isolated Docker environment
4. **Observability**: Log important operations and metrics

### Performance

1. **Parallel Execution**: Use `pytest-xdist` for parallel tests
2. **Resource Limits**: Configure Docker resource constraints
3. **Caching**: Leverage Redis caching in tests
4. **Batching**: Group related operations when possible

### Security

1. **Credentials**: Use test-specific credentials (bootstrap admin)
2. **Isolation**: E2E environment uses separate ports (5433, 6380)
3. **Data**: Use synthetic test data, never production data
4. **Cleanup**: Always clean up sensitive data after tests

## Maintenance

### Regular Tasks

1. **Update Dependencies**: Keep test dependencies current
2. **Review Metrics**: Monitor performance trends over time
3. **Add Coverage**: Add tests for new features
4. **Optimize**: Refactor slow or flaky tests

### Monitoring Test Health

Track these metrics over time:

- Pass rate (target: 100%)
- Execution time (target: < 2 minutes)
- Flakiness rate (target: < 1%)
- Code coverage (target: > 80%)

## Resources

- Test Suite: `tests/test_e2e_integration.py`
- Docker Config: `docker-compose.e2e.yml`
- Test Container: `Dockerfile.e2e`
- Orchestration Script: `scripts/run_e2e_tests.sh`
- Analysis Script: `scripts/analyze_e2e_results.py`
- Architecture: `ARCHITECTURE.md`
- API Reference: `docs/API_REFERENCE.md`

## Support

For issues or questions:

1. Check this documentation
2. Review test logs in `logs/`
3. Check backend logs: `docker-compose -f docker-compose.e2e.yml logs backend`
4. Open GitHub issue with logs and results
