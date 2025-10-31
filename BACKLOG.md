# Product Backlog - KeneyApp

This document tracks the prioritized backlog of improvements for KeneyApp following the continuous improvement cycle methodology.

## Backlog Structure

Each item includes:
- **ID**: Unique identifier
- **Category**: Bug / Tech Debt / Feature / Security / Compliance
- **Priority**: Critical / High / Medium / Low
- **Effort**: S (Small: 1-2h) / M (Medium: 3-8h) / L (Large: 1-3 days) / XL (Extra Large: >3 days)
- **Status**: Backlog / In Progress / Done / Blocked
- **Iteration**: Target iteration number

---

## Iteration 4 (Current) - Focus: Runtime Reliability

### Critical Priority

#### [BACK-401] CI/CD: Docker Compose smoke tests
- **Category**: Security
- **Priority**: Critical
- **Effort**: S
- **Status**: Done
- **Description**: Add a GitHub Actions job that builds the docker-compose stack and performs health checks to catch runtime regressions early.
- **Acceptance Criteria**:
  - Job runs on PRs and main/develop pushes
  - Backend health endpoint successfully polled
  - Logs surfaced when the backend fails to start

#### [BACK-402] Data Integrity: Tenant-aware seed script
- **Category**: Tech Debt
- **Priority**: Critical
- **Effort**: S
- **Status**: Done
- **Description**: Ensure sample data created by `scripts/init_db.py` respects tenant constraints introduced by migrations.
- **Acceptance Criteria**:
  - Seed script provisions a default tenant when absent
  - All seeded entities (users, patients, appointments, prescriptions) carry `tenant_id`
  - Script remains idempotent and safe to re-run

### High Priority

#### [BACK-403] Security: Align bcrypt with Passlib expectations
- **Category**: Security
- **Priority**: High
- **Effort**: S
- **Status**: Done
- **Description**: Pin bcrypt to the latest version compatible with Passlib to avoid runtime import errors in containers.
- **Acceptance Criteria**:
  - Dependency conflict resolved (`bcrypt==4.1.2`)
  - Backend containers start without `__about__` attribute errors
  - Documented in changelog and dependency policy

#### [BACK-404] Documentation: Multi-tenant seeding guidelines
- **Category**: Documentation
- **Priority**: High
- **Effort**: S
- **Status**: Done
- **Description**: Update developer docs to explain tenant-aware seeding expectations and automated workflows.
- **Acceptance Criteria**:
  - `docs/DEVELOPMENT.md` includes multi-tenant seeding section
  - Guidance references CI smoke tests and start script behaviour

---

## Iteration 3 (Completed) - Focus: Automation & Quality

### Critical Priority

#### [BACK-301] Security: Update vulnerable dependencies
- **Category**: Security
- **Priority**: Critical
- **Effort**: S
- **Status**: In Progress
- **Description**: Update Starlette (0.41.2) and Strawberry-GraphQL (0.257.0) to fix known CVEs
- **Acceptance Criteria**:
  - All dependencies updated to secure versions
  - pip-audit reports 0 vulnerabilities
  - All tests pass after update
- **Related**: GHSA-7f5h-v6xp-fcq8, PYSEC-2024-171

#### [BACK-302] CI/CD: Integrate automated security scanning
- **Category**: Security
- **Priority**: Critical
- **Effort**: M
- **Status**: Backlog
- **Description**: Add pip-audit and safety checks to CI/CD pipeline
- **Acceptance Criteria**:
  - pip-audit runs in CI on every PR
  - Build fails on high/critical vulnerabilities
  - Weekly scheduled scan via GitHub Actions
- **Dependencies**: BACK-301

### High Priority

#### [BACK-303] Tech Debt: Improve type hints coverage
- **Category**: Tech Debt
- **Priority**: High
- **Effort**: L
- **Status**: Backlog
- **Description**: Add comprehensive type hints to core modules, improve mypy coverage to 95%+
- **Acceptance Criteria**:
  - mypy runs with --strict mode
  - No type errors in app/core, app/models, app/routers
  - Type hints in all public functions
- **Benefits**: Better IDE support, fewer runtime errors, improved maintainability

#### [BACK-304] Observability: Business metrics dashboard
- **Category**: Feature
- **Priority**: High
- **Effort**: M
- **Status**: Backlog
- **Description**: Add business KPI metrics (daily active patients, appointment completion rate, prescription fulfillment)
- **Acceptance Criteria**:
  - New Prometheus metrics for business KPIs
  - Grafana dashboard with business metrics
  - Alerts for anomalies in KPIs
- **Related**: Existing Prometheus integration

#### [BACK-305] Testing: Performance test suite
- **Category**: Tech Debt
- **Priority**: High
- **Effort**: M
- **Status**: Backlog
- **Description**: Add Locust-based performance tests to establish baseline and prevent regressions
- **Acceptance Criteria**:
  - Performance tests for critical endpoints
  - CI integration with performance thresholds
  - Baseline metrics documented
  - Load test scenarios (100, 500, 1000 concurrent users)

#### [BACK-306] Documentation: API versioning strategy
- **Category**: Tech Debt
- **Priority**: High
- **Effort**: S
- **Status**: Backlog
- **Description**: Document and implement API versioning strategy for backward compatibility
- **Acceptance Criteria**:
  - API_VERSIONING.md created
  - Deprecation policy defined
  - Version headers documented
  - Migration guides for API consumers

### Medium Priority

#### [BACK-307] Feature: Patient data export (GDPR)
- **Category**: Compliance
- **Priority**: Medium
- **Effort**: M
- **Status**: Backlog
- **Description**: Implement GDPR-compliant patient data export in machine-readable format
- **Acceptance Criteria**:
  - Export endpoint returns complete patient data
  - Formats: JSON, PDF, CSV
  - Audit logging for export requests
  - Rate limiting to prevent abuse

#### [BACK-308] Tech Debt: Database query optimization
- **Category**: Tech Debt
- **Priority**: Medium
- **Effort**: M
- **Status**: Backlog
- **Description**: Add database indexes, optimize N+1 queries, implement query caching
- **Acceptance Criteria**:
  - Query performance improved by 30%
  - Slow query log analysis
  - Missing indexes added
  - SQLAlchemy lazy loading reviewed

#### [BACK-309] Security: Implement CSP reporting
- **Category**: Security
- **Priority**: Medium
- **Effort**: S
- **Status**: Backlog
- **Description**: Add Content Security Policy violation reporting endpoint
- **Acceptance Criteria**:
  - CSP report-uri configured
  - Violation logging implemented
  - Dashboard for CSP violations
  - Alerts for suspicious patterns

#### [BACK-310] Feature: Appointment reminder system
- **Category**: Feature
- **Priority**: Medium
- **Effort**: L
- **Status**: Backlog
- **Description**: Automated email/SMS reminders for upcoming appointments
- **Acceptance Criteria**:
  - Celery task for reminder scheduling
  - Email template for reminders
  - SMS integration (optional)
  - Opt-out mechanism
  - Audit logging

### Low Priority

#### [BACK-311] Tech Debt: Frontend unit test coverage
- **Category**: Tech Debt
- **Priority**: Low
- **Effort**: L
- **Status**: Backlog
- **Description**: Increase frontend test coverage from current to 80%+
- **Acceptance Criteria**:
  - All components have unit tests
  - Critical user flows have integration tests
  - Coverage report in CI

#### [BACK-312] Feature: Multi-language support (i18n)
- **Category**: Feature
- **Priority**: Low
- **Effort**: XL
- **Status**: Backlog
- **Description**: Add internationalization support for French, English, Spanish
- **Acceptance Criteria**:
  - react-i18next integration
  - Translation files for 3 languages
  - Language switcher in UI
  - Backend validation messages translated

#### [BACK-313] Tech Debt: API request/response logging
- **Category**: Tech Debt
- **Priority**: Low
- **Effort**: S
- **Status**: Backlog
- **Description**: Enhanced request/response logging with body sanitization (PII masking)
- **Acceptance Criteria**:
  - Request/response bodies logged (sanitized)
  - PII fields masked
  - Performance impact < 5ms
  - Configurable log levels

---

## Iteration 5 (Current) - Focus: Type Safety & Testing Depth

### High Priority

#### [BACK-501] Tooling: Establish mypy baseline
- **Category**: Tech Debt
- **Priority**: High
- **Effort**: M
- **Status**: Done
- **Description**: Introduce a mypy configuration with gradual strictness and eliminate existing type errors in core modules.
- **Acceptance Criteria**:
  - ✅ `mypy.ini` committed with targeted module list
  - ✅ CI job executes mypy and fails on regressions
  - ✅ app/core and app/routers pass type checking

#### [BACK-502] Testing: Add API smoke tests for docker stack
- **Category**: Testing
- **Priority**: High
- **Effort**: S
- **Status**: Done
- **Description**: Build upon the docker compose job to exercise critical API flows (login + patient listing).
- **Acceptance Criteria**:
  - ✅ pytests or curl scripts executed against running stack
  - ✅ Smoke suite documented and reusable locally

### Medium Priority

#### [BACK-503] Documentation: Architecture & Pipeline diagrams refresh
- **Category**: Documentation
- **Priority**: Medium
- **Effort**: S
- **Status**: Done
- **Description**: Update architecture diagrams and CI workflow description to reflect new automation steps.
- **Acceptance Criteria**:
  - ✅ Mermaid diagrams cover docker smoke validation path
  - ✅ README highlights new CI stages

---

## Completed Items

### Iteration 5 (Completed)
- [BACK-501] ✅ Established mypy baseline with gradual typing
- [BACK-502] ✅ Added comprehensive API smoke tests for docker stack
- [BACK-503] ✅ Updated architecture diagrams with CI/CD pipeline

### Iteration 4 (Completed)
- [BACK-401] ✅ CI/CD: Docker Compose smoke tests
- [BACK-402] ✅ Data Integrity: Tenant-aware seed script
- [BACK-403] ✅ Security: Align bcrypt with Passlib expectations
- [BACK-404] ✅ Documentation: Multi-tenant seeding guidelines

### Iteration 3 (Completed)
- [BACK-301] ✅ Security: Update vulnerable dependencies
- [BACK-302] ✅ CI/CD: Integrate automated security scanning

### Iteration 2 (Completed)
- [BACK-201] ✅ Bootstrap admin and tenant configuration
- [BACK-202] ✅ RBAC super_admin implicit access
- [BACK-203] ✅ Login endpoint validation improvements
- [BACK-204] ✅ Documentation updates for security controls

### Iteration 1 (Completed)
- [BACK-101] ✅ Structured JSON logging with correlation IDs
- [BACK-102] ✅ Enhanced Prometheus alerting rules
- [BACK-103] ✅ Incident response playbook
- [BACK-104] ✅ Operations runbook
- [BACK-105] ✅ Security dependency updates
- [BACK-106] ✅ Correlation ID middleware tests

---

## Backlog Management Process

### Adding Items
1. Create unique ID: BACK-[Iteration][Sequential Number]
2. Fill all required fields (Category, Priority, Effort, Description)
3. Define clear acceptance criteria
4. Estimate effort (S/M/L/XL)
5. Add to appropriate priority section

### Prioritization Framework
- **Critical**: Security vulnerabilities, data loss risks, compliance violations, production outages
- **High**: Performance issues, major bugs, key features, significant tech debt
- **Medium**: Minor bugs, nice-to-have features, moderate tech debt
- **Low**: Enhancements, documentation improvements, minor optimizations

### Effort Estimation
- **S (Small)**: 1-2 hours - Simple changes, config updates, minor fixes
- **M (Medium)**: 3-8 hours - Moderate features, refactoring, testing
- **L (Large)**: 1-3 days - Complex features, major refactoring, integration
- **XL (Extra Large)**: >3 days - Major features, architectural changes

### Iteration Planning
1. Select 3-5 items for next iteration
2. Balance across categories (bugs, features, tech debt, security)
3. Consider dependencies between items
4. Align with business priorities
5. Ensure team capacity matches effort estimates

### Progress Tracking
- Update status: Backlog → In Progress → Done/Blocked
- Document blockers and resolutions
- Track actual vs. estimated effort
- Move completed items to "Completed Items" section

---

## Next Iteration Planning

### Iteration 4 (Planned)
**Theme**: Performance & Scalability
- Database optimization (BACK-308)
- Performance testing (BACK-305)
- Caching improvements
- Load testing

### Iteration 5 (Planned)
**Theme**: Compliance & Features
- GDPR data export (BACK-307)
- Appointment reminders (BACK-310)
- Enhanced audit logging
- Compliance reporting

---

## References
- [Contributing Guide](CONTRIBUTING.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)
