# Changelog

All notable changes to KeneyApp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Continuous Improvement Cycle Iteration 4

#### CI/CD
- Updated Codecov uploads to use the v5 `files` input and tolerate transient failures, restoring backend/frontend job stability.
- Upgraded GitHub CodeQL actions to v3 and guarded the analysis job against forked pull requests where security events cannot be published.
- Adopted the latest `actions/setup-python@v5` across workflows for consistent toolchain provisioning.

#### Infrastructure
- Aligned backend Docker image with the supported Python 3.11 base to match local/runtime environments and ensure prebuilt database drivers are available during builds.

### Added - Continuous Improvement Cycle Iteration 3

#### Security & Dependencies
- Updated Starlette to 0.49.1 to fix CVE (GHSA-7f5h-v6xp-fcq8) - CPU exhaustion vulnerability in FileResponse Range parsing
- Updated Strawberry-GraphQL to 0.257.0 to fix CSRF and type confusion vulnerabilities (PYSEC-2024-171, GHSA-5xh2-23cc-5jc6)
- Updated FastAPI to 0.115.5 for latest security patches
- Updated python-multipart to 0.0.12 for security improvements
- Integrated pip-audit in CI/CD pipeline with scheduled weekly scans
- Added comprehensive security scanning workflow with:
  - Dependency vulnerability scanning (pip-audit, safety, npm audit)
  - Secret scanning (Gitleaks, detect-secrets)
  - Container security scanning (Trivy)
  - SARIF report upload to GitHub Security

#### Observability & Monitoring
- Added comprehensive business KPI metrics:
  - Daily active patients tracking
  - Appointment completion rate (daily/weekly/monthly)
  - Prescription fulfillment rate
  - No-show rate monitoring
  - Patient risk level distribution
  - Appointments and prescriptions by status
- Added security & compliance metrics:
  - Authentication failures tracking
  - Unauthorized access attempts
  - Audit log activity monitoring
  - Data export requests tracking
  - Encryption operations counter
- Created metrics collector service for automated KPI updates
- Added Celery background task for periodic metrics collection
- Created enhanced Grafana Business KPI Dashboard with:
  - Real-time patient metrics
  - Appointment and prescription analytics
  - Security incident tracking
  - Compliance monitoring

#### Process & Documentation
- Implemented product backlog management system (BACKLOG.md)
- Established continuous improvement cycle framework with:
  - Priority-based backlog (Critical/High/Medium/Low)
  - Effort estimation methodology (S/M/L/XL)
  - Iteration planning process
  - Progress tracking system
- Documented 13 backlog items for future iterations
- Established backlog management process and prioritization framework

### Changed
- Enhanced CI/CD pipeline with scheduled security scans (weekly on Mondays)
- Improved dependency management with automated vulnerability detection
- Enhanced monitoring capabilities with business-focused metrics

### Security
- Fixed critical CPU exhaustion vulnerability in Starlette (file serving)
- Fixed CSRF vulnerability in Strawberry-GraphQL
- Fixed type confusion vulnerability in GraphQL relay integration
- Automated security scanning integrated into development workflow
#### Security & Compliance
- Hardened `require_roles` to normalize role input (lists or variadic) while preserving implicit `super_admin` access, preventing configuration typos from silently relaxing authorization.

#### Testing
- Added focused unit coverage for the RBAC dependency to assert list handling, denial behavior, and `super_admin` bypass rules.

#### Tooling & DX
- Reduced mypy noise around RBAC usage by improving dependency typing, making type-checking output more actionable for developers.

### Added - Continuous Improvement Cycle Iteration 2

#### Security & Compliance
- Automatic bootstrap of a default tenant and administrator (behind `ENABLE_BOOTSTRAP_ADMIN`) to keep contract tests and smoke tests deterministic while preserving the ability to disable it in hardened environments.
- RBAC guard now grants `super_admin` accounts implicit access to protected routes, aligning authorization with organizational policies.

#### API
- Login endpoint now emits proper validation errors (`422`) when username or password is missing, improving client contract guarantees.

#### Documentation
- Documented the bootstrap administrator controls in `.env.example`, `.env`, `README.md`, and `SECURITY.md`.

### Added - Continuous Improvement Cycle Iteration 1

#### Observability & Monitoring
- Structured JSON logging middleware with correlation IDs for distributed tracing
- Request/response logging with timing information
- Enhanced Prometheus alerting rules covering:
  - Application health (error rates, response times, uptime)
  - Database performance (connections, query times, availability)
  - Infrastructure (CPU, memory, container restarts)
  - Cache performance (hit rates, Redis memory)
  - Celery task queue health
  - Business metrics anomaly detection
  - Security alerts (authentication failures, unauthorized access)
  - Compliance monitoring (audit logs, certificate expiry)
  - Data quality alerts
- X-Correlation-ID header support for request tracing across services

#### Documentation
- Comprehensive incident response playbook with:
  - Incident classification and severity levels
  - Step-by-step response procedures
  - Security incident protocols (including HIPAA/GDPR breach response)
  - Service outage troubleshooting
  - Database issue resolution
  - Post-incident review templates
  - Emergency contacts and escalation paths
- Detailed operations runbook covering:
  - Daily health check procedures
  - Deployment procedures (blue-green, hotfix, rollback)
  - Database operations (maintenance, backup, restore, migrations)
  - Monitoring and alerting guidelines
  - Backup and recovery procedures
  - Scaling operations (horizontal and vertical)
  - Certificate management
  - Troubleshooting guides
  - Security procedures

#### Testing
- Comprehensive tests for correlation ID middleware (6 new tests)
- Test coverage maintained at 77%

#### Security & Dependencies
- Updated requirements.txt with fixed versions for vulnerable packages:
  - cryptography upgraded to 44.0.1 (fixes OpenSSL vulnerability)
  - certifi upgraded to 2024.7.4 (removes untrusted root certificates)
  - jinja2 upgraded to 3.1.4 (fixes XSS vulnerability)
  - idna upgraded to 3.7 (fixes DoS vulnerability)
  - urllib3 upgraded to 2.2.3 (security fixes)
  - requests upgraded to 2.32.0 (security fixes)
  - werkzeug upgraded to 3.0.6 (security fixes)
  - configobj upgraded to 5.0.9 (fixes ReDoS vulnerability)

### Changed
- Enhanced application middleware stack with correlation ID tracking
- Improved logging format for better observability
- Enhanced CI/CD workflow with better caching and parallel jobs
- Improved README with better organization and quick links
- Backend code formatted with Black for consistency

### Fixed
- Code formatting issues in backend files
- Security vulnerabilities in dependencies

## [2.0.0] - 2024-01-15

### Added
- OAuth2/OIDC authentication support (Google, Microsoft, Okta)
- Data encryption at rest with AES-256-GCM
- GraphQL API alongside REST
- HL7 FHIR R4 interoperability support
- Comprehensive audit logging for GDPR/HIPAA compliance
- Redis caching for performance optimization
- Celery background task processing
- Prometheus metrics and monitoring
- Grafana dashboards for visualization
- Kubernetes deployment manifests with HPA
- Terraform scripts for AWS, Azure, and GCP
- Rate limiting to prevent API abuse
- Enhanced security headers (XSS, CSRF, CSP)
- Multi-factor authentication (MFA) support
- Horizontal auto-scaling capabilities
- Health check endpoints for load balancers
- Flower for Celery task monitoring

### Changed
- Upgraded to Python 3.11 and FastAPI latest version
- Enhanced role-based access control system
- Improved database query performance
- Migrated to React 18 with TypeScript
- Enhanced error handling and logging
- Updated API documentation with new endpoints

### Security
- Implemented data encryption at rest
- Added comprehensive audit logging
- Enhanced authentication with OAuth2/OIDC
- Added rate limiting to prevent abuse
- Implemented security headers (XSS, CSRF, CSP)
- Added MFA support for enhanced security

## [1.0.0] - 2023-12-01

### Added
- Initial release of KeneyApp
- Patient management system
- Appointment scheduling
- Prescription management
- Dashboard with health metrics
- Multi-role support (Admin, Doctor, Nurse, Receptionist)
- JWT-based authentication
- PostgreSQL database integration
- React frontend with TypeScript
- Docker and Docker Compose support
- API documentation with Swagger UI
- Basic CI/CD with GitHub Actions

### Core Features
- Complete patient record system
- Medical history and allergy tracking
- Emergency contact management
- Appointment status tracking
- Digital prescription system
- Real-time dashboard statistics
- Role-based access control
- RESTful API
- Responsive web interface

---

## Release Types

### Major Version (X.0.0)
- Breaking changes that require migration
- Significant architectural changes
- Major feature additions

### Minor Version (x.X.0)
- New features (backward compatible)
- Significant improvements
- New API endpoints

### Patch Version (x.x.X)
- Bug fixes
- Security patches
- Minor improvements
- Documentation updates

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

---

## Support

For questions or issues, please contact: contact@isdataconsulting.com
