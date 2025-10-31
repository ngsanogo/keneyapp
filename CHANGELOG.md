# Changelog

All notable changes to KeneyApp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
