# Comprehensive Testing Strategy

This strategy establishes how KeneyApp validates functionality, reliability, and compliance across unit, integration, and end-to-end (E2E) levels. It defines what to test, where tests live, how they run locally and in CI, and the quality gates required before release.

## Goals and Ownership

- **Goals:** Catch regressions early, keep critical user journeys green, and maintain predictable release quality with actionable reports.
- **Owners:** Feature squads write and maintain unit/integration tests; DevOps maintains pipelines and test environments.
- **Coverage Targets:** ≥80% backend unit/integration coverage, ≥70% frontend unit/component coverage.

## Test Taxonomy and Distribution

| Layer | Scope | Location | Primary Commands | Expected Share |
| --- | --- | --- | --- | --- |
| **Unit** | Functions, classes, handlers with isolated dependencies | `tests/` (pytest, markers: `unit`) | `make test-unit` or `pytest -m unit` | ~60% |
| **Integration** | Service boundaries: DB, cache, queues, external adapters, and full API workflows | `tests/` (markers: `integration`, `e2e`) | `make test-integration` or `pytest -m integration` | ~40% |

## Environments and Pipelines

| Stage | What Runs | Purpose | Gate |
| --- | --- | --- | --- |
| **Local dev** | Focused `unit`/`integration` markers during feature work | Fast feedback while coding | Optional |
| **Pre-merge CI** | `make test` (backend unit/integration sans `slow`/`smoke`) + `frontend npm test`; static analysis | Block regressions on PRs | Required |
| **Nightly/regression** | `make test-all` (includes `--slow`), security and performance jobs | Broader coverage and drift detection | Required for release branch promotion |
| **Release cut** | Coverage check (`make test-cov`), manual QA sign-off | Final go/no-go | Required |

## Unit Testing Strategy

- **Scope:** Business rules, validation, utilities, service methods, and HTTP handlers with external calls mocked.
- **Location & markers:** `tests/` with `@pytest.mark.unit` where isolation is guaranteed.
- **Fixtures:** Reuse shared fixtures from `tests/conftest.py` for clients, auth, and seeded data; prefer factories/builders over hand-crafted payloads.
- **Guidelines:**
  - One behavior per test; assert business outcomes, not implementation details.
  - Mock external dependencies (DB, cache, HTTP) and keep runtime <1s/test.
  - Add regression tests for every bug fix before closing the issue.
- **Commands:** `make test-unit` for the full set, `pytest tests/test_patient_service.py::test_x -m unit -vv` for targeted runs.

## Integration Testing Strategy

- **Scope:** Interactions with PostgreSQL, Redis/cache, background workers, and cross-module flows (e.g., auth + RBAC + resource operations).
- **Location & markers:** `tests/` with `@pytest.mark.integration` and mixed suites that rely on real services.
- **Environment:**
  - Bring up dependencies with `docker compose up -d` (or `docker-compose.dev.yml` if preferred).
  - Use migration helpers/fixtures to seed schemas; clean state between tests using fixture-level rollbacks.
- **Guidelines:**
  - Validate schema/contract expectations (status codes, response shapes) and side-effects (DB rows, emitted events).
  - Exercise error paths (timeouts, invalid tokens, missing RBAC) and idempotency.
  - Keep tests parallel-safe; avoid global state and prefer per-test resources.
- **Commands:** `make test-integration` for the suite; `pytest -m integration tests/test_api_contracts.py -vv` for targeted checks.

## Cross-Cutting Practices

- **Test data:** Prefer factories/builders and fixture seeds; never re-use production secrets. Reset state via fixtures and teardown hooks.
- **Traceability:** Every user story/feature flag should link to: a unit test for core logic, and an integration test for service boundaries and user workflows.
- **Coverage gates:** Failing if backend/unit+integration coverage <80% (`make test-cov`), frontend coverage <70%.
- **Performance & security:** Include `pytest -m "performance and slow"` in nightly jobs; run `make security` weekly or on dependency bumps.
- **Reporting:** CI must publish coverage (HTML/LCOV) and pytest JUnit XML. Track flaky tests and quarantine with a ticket until resolved.

## How to Adopt for New Features

1. **Design phase:** Add acceptance criteria and map them to unit and integration test scenarios.
2. **Implementation:** Start with unit tests alongside code; add integration coverage once service contracts stabilize.
3. **Pre-PR:** Run `make test-unit` + `make test-integration` locally.
4. **PR review:** Block merge without tests for new behaviors; request coverage deltas for risky changes.
5. **PR review:** Block merge without tests for new behaviors; request coverage deltas for risky changes.
6. **Release:** Ensure nightly suite is green, coverage gates met, and reports archived before tagging.

## Quick Reference

```bash
# Backend unit tests
make test-unit

# Integration tests against local Docker stack
docker compose up -d
make test-integration

# Full backend + frontend fast path (excludes slow/smoke)
make test

# Coverage reports
make test-cov
```

