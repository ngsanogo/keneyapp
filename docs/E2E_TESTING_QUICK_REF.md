# E2E Testing Quick Reference

## Run Tests

```bash
# Run full E2E test suite
./scripts/run_e2e_tests.sh

# Run without cleanup (for debugging)
./scripts/run_e2e_tests.sh
# Choose 'n' when prompted for cleanup

# Run specific test class
docker-compose -f docker-compose.e2e.yml run --rm e2e_tests \
  pytest tests/test_e2e_integration.py::TestE2EPatientWorkflows -v

# Run with parallel execution
docker-compose -f docker-compose.e2e.yml run --rm e2e_tests \
  pytest tests/test_e2e_integration.py -n auto
```

## View Results

```bash
# View analysis report
cat logs/e2e_analysis_report.txt

# View JSON results
cat logs/e2e_integration_results.json | jq .

# View detailed log
tail -f logs/e2e_integration_test.log

# View specific metrics
cat logs/e2e_integration_results.json | jq '.performance_metrics'

# View failures only
cat logs/e2e_integration_results.json | jq '.tests[] | select(.status == "failed")'
```

## Debug

```bash
# Check service status
docker-compose -f docker-compose.e2e.yml ps

# View backend logs
docker-compose -f docker-compose.e2e.yml logs backend

# View all logs
docker-compose -f docker-compose.e2e.yml logs

# Access backend shell
docker-compose -f docker-compose.e2e.yml exec backend /bin/bash

# Check database
docker-compose -f docker-compose.e2e.yml exec postgres \
  psql -U keneyapp -d keneyapp_test -c "SELECT COUNT(*) FROM patients;"

# Check Redis
docker-compose -f docker-compose.e2e.yml exec redis redis-cli KEYS "*"
```

## Cleanup

```bash
# Stop and remove containers
docker-compose -f docker-compose.e2e.yml down -v

# Remove all test artifacts
rm -rf logs/ test_results/

# Full cleanup (including images)
docker-compose -f docker-compose.e2e.yml down -v --rmi local
```

## Common Issues

### Connection Refused
```bash
# Wait for services to be healthy
docker-compose -f docker-compose.e2e.yml up -d
sleep 30
docker-compose -f docker-compose.e2e.yml ps
```

### Tests Hanging
```bash
# Check for port conflicts
lsof -i :8000 -i :5433 -i :6380

# Kill existing containers
docker-compose -f docker-compose.e2e.yml down -v
docker-compose -f docker-compose.yml down -v
```

### Database Not Seeded
```bash
# Manually run seed script
docker-compose -f docker-compose.e2e.yml exec backend \
  python scripts/init_db.py
```

### Performance Issues
```bash
# Check Docker resources
docker stats

# Run single-threaded
pytest tests/test_e2e_integration.py -v

# Profile specific test
pytest tests/test_e2e_integration.py::TestE2EPatientWorkflows::test_patient_crud_workflow \
  --profile
```

## Test Coverage

```bash
# Generate coverage report
docker-compose -f docker-compose.e2e.yml run --rm e2e_tests \
  pytest tests/test_e2e_integration.py --cov=app --cov-report=html

# View coverage
open htmlcov/index.html
```

## CI Integration

### GitHub Actions
```yaml
- name: E2E Tests
  run: ./scripts/run_e2e_tests.sh

- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: e2e-results
    path: |
      logs/e2e_*.json
      logs/e2e_*.txt
      test_results/*.xml
```

### Environment Variables
```bash
# Override base URL
export E2E_BASE_URL=http://custom-host:8000

# Enable verbose logging
export E2E_VERBOSE=1

# Set timeout
export E2E_TIMEOUT=300
```

## Performance Targets

| Metric | Target | Warning |
|--------|--------|---------|
| Total Duration | < 2 min | > 3 min |
| Auth Time | < 200ms | > 500ms |
| Patient CRUD | < 300ms | > 500ms |
| Cache Hit | < 50ms | > 200ms |
| Pass Rate | 100% | < 95% |

## Useful Commands

```bash
# Watch logs in real-time
docker-compose -f docker-compose.e2e.yml logs -f

# Check test execution time
cat logs/e2e_integration_results.json | jq '.total_duration_seconds'

# Count test cases
cat logs/e2e_integration_results.json | jq '.summary'

# List slow operations
cat logs/e2e_integration_results.json | \
  jq '.performance_metrics | to_entries | sort_by(.value.value) | reverse | .[0:5]'

# Get failure rate
cat logs/e2e_integration_results.json | \
  jq '.summary.failed / .summary.total * 100'

# Export results for spreadsheet
cat logs/e2e_integration_results.json | \
  jq -r '.tests[] | [.name, .status, .duration_seconds] | @csv' > tests.csv
```
