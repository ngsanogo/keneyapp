# Comprehensive Testing Strategy

This strategy establishes how KeneyApp validates functionality, reliability, and compliance across unit, integration, and end-to-end (E2E) levels. It defines what to test, where tests live, how they run locally and in CI, and the quality gates required before release.

## Goals and Ownership

- **Goals:** Catch regressions early, keep critical user journeys green, and maintain predictable release quality with actionable reports.
- **Owners:** Feature squads write and maintain unit/integration tests; QA/Automation owns Playwright E2E coverage; DevOps maintains pipelines and test environments.
- **Coverage Targets:** ≥80% backend unit/integration coverage, ≥70% frontend unit/component coverage, and 100% pass rate on critical-path E2E suites.

## Test Taxonomy and Distribution

| Layer | Scope | Location | Primary Commands | Expected Share |
| --- | --- | --- | --- | --- |
| **Unit** | Functions, classes, handlers with isolated dependencies | `tests/` (pytest, markers: `unit`) | `make test-unit` or `pytest -m unit` | ~60% |
| **Integration** | Service boundaries: DB, cache, queues, external adapters | `tests/` (markers: `integration`) | `make test-integration` or `pytest -m integration` | ~25% |
| **E2E** | Full user workflows in browser against running stack | `e2e/` (Playwright) | `npm run test:e2e` / `./scripts/run_e2e_tests.sh` | ~15% |

## Environments and Pipelines

| Stage | What Runs | Purpose | Gate |
| --- | --- | --- | --- |
| **Local dev** | Focused `unit`/`integration` markers; targeted Playwright specs during feature work | Fast feedback while coding | Optional |
| **Pre-merge CI** | `make test` (backend unit/integration sans `slow`/`smoke`) + `frontend npm test`; static analysis; Playwright smoke (`auth.spec.ts`, `patients.spec.ts` critical paths) | Block regressions on PRs | Required |
| **Nightly/regression** | `make test-all` (includes `--slow`), full Playwright suite (`npm run test:e2e`), security and performance jobs | Broader coverage and drift detection | Required for release branch promotion |
| **Release cut** | Coverage check (`make test-cov`), E2E rerun on tagged image, manual QA sign-off | Final go/no-go | Required |

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

## End-to-End (Playwright) Strategy

- **Scope:** Browser-level validation of critical flows: authentication, patient onboarding, document upload/sharing, and v3 feature set (`e2e/*.spec.ts`).
- **Environment:**
  - Bring the stack up with `docker compose -f docker-compose.e2e.yml up -d --build` (or `./scripts/run_e2e_tests.sh` which orchestrates setup and teardown).
  - Use seeded demo users/tenants from the e2e compose file; avoid modifying seeds in specs.
- **Suites:**
  - **Smoke:** `auth.spec.ts` (login/logout), `patients.spec.ts` (core CRUD) — must run on every PR.
  - **Regression:** `v3-features.spec.ts` and any new feature specs — run nightly and before releases.
- **Commands:**
  - Headless CI: `npm run test:e2e`
  - Local debug: `npm run test:e2e:headed` or `npm run test:e2e:ui`
  - Targeted spec: `npx playwright test e2e/patients.spec.ts --grep "uploads"`
- **Artifacts:** Collect HTML reports from Playwright (`playwright-report/`) and upload to CI for failure triage.

## Cross-Cutting Practices

- **Test data:** Prefer factories/builders and fixture seeds; never re-use production secrets. Reset state via fixtures and teardown hooks.
- **Traceability:** Every user story/feature flag should link to: a unit test for core logic, an integration test for service boundaries, and (if user-facing) an E2E scenario.
- **Coverage gates:** Failing if backend/unit+integration coverage <80% (`make test-cov`), frontend coverage <70%, or smoke E2E fails.
- **Performance & security:** Include `pytest -m "performance and slow"` in nightly jobs; run `make security` weekly or on dependency bumps.
- **Reporting:** CI must publish coverage (HTML/LCOV), pytest JUnit XML, and Playwright HTML reports. Track flaky tests and quarantine with a ticket until resolved.

## How to Adopt for New Features

1. **Design phase:** Add acceptance criteria and map them to unit, integration, and (if needed) E2E scenarios.
2. **Implementation:** Start with unit tests alongside code; add integration coverage once service contracts stabilize.
3. **E2E addition:** For any new user-visible flow, extend existing Playwright specs or add a dedicated one with fixtures.
4. **Pre-PR:** Run `make test-unit` + `make test-integration` and the relevant Playwright spec locally (headed/quiet as needed).
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

# Playwright smoke/regression
npm install  # first time
npm run test:e2e
./scripts/run_e2e_tests.sh  # orchestrated Docker + Playwright

# Coverage reports
make test-cov
```

