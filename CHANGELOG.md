# Changelog

All notable changes to KeneyApp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.0] - 2025-11-02 - Complete Medical Record System 🏥

### Added - Major Features

#### 💬 Secure Messaging System

- End-to-end encrypted messaging between patients and healthcare providers
- Message encryption with AES-256-GCM at rest
- Threaded conversations with automatic grouping
- Read/unread status tracking
- Urgent message flagging
- Document attachments support
- Soft delete functionality per user
- API endpoints: `/api/v1/messages/`
- New model: `Message` with encryption support
- Migration: `010_add_messages.py`
- Rate limiting: 30 sends/min, 60 reads/min
- Full audit logging of all message operations

#### 📄 Medical Document Management

- Complete document storage system for medical files
- Supported formats: PDF, JPEG, PNG, DICOM, DOCX, TXT
- Document types: lab results, imaging, prescriptions, consultation notes, vaccination records, insurance, ID documents
- Features:
  - Secure file upload with 50 MB limit
  - SHA-256 checksum for integrity verification
  - Duplicate detection
  - Local and S3-compatible storage
  - OCR-ready infrastructure
  - Rich metadata (description, tags, associations)
  - Soft delete with archival
- API endpoints: `/api/v1/documents/`
- New model: `MedicalDocument` with comprehensive metadata
- Migration: `011_add_medical_documents.py`
- Rate limiting: 20 uploads/min, 30 downloads/min
- Full audit logging of uploads and downloads

#### 🔔 Automated Notification System

- Multi-channel notifications (Email + SMS)
- Notification types:
  - Appointment reminders (24h advance)
  - Lab results availability
  - Prescription renewal reminders (7 days advance)
  - Vaccination reminders
  - New message notifications
- Email support: SMTP (Gmail, SendGrid, AWS SES)
- SMS support: Twilio integration
- Celery background tasks:
  - `send_upcoming_appointment_reminders` (daily)
  - `send_lab_results_notifications` (on-demand)
  - `send_prescription_renewal_reminders` (daily)
  - `send_new_message_notification` (on-demand)
- New service: `NotificationService` with unified interface
- Configurable via environment variables

#### 🔗 Controlled Medical Record Sharing

- Temporary secure sharing with time-limited tokens
- Features:
  - Secure random tokens (secrets.token_urlsafe)
  - Optional 6-digit PIN protection
  - Configurable expiration (1h - 30 days)
  - Access count limits
  - Email restrictions
  - IP tracking and audit logging
- Sharing scopes:
  - `full_record`: Complete medical history
  - `appointments_only`: Appointments only
  - `prescriptions_only`: Prescriptions only
  - `documents_only`: Documents only
  - `custom`: Custom resource selection
- Use cases: External consultations, emergencies, insurance claims, family access
- API endpoints: `/api/v1/shares/` (including public access endpoint)
- New model: `MedicalRecordShare` with consent tracking
- Migration: `012_add_medical_record_shares.py`
- Rate limiting: 10 shares/hour, 20 accesses/hour
- Patient consent required for all shares

### Added - Dependencies

- `twilio==9.3.7` - SMS notifications via Twilio
- `python-magic==0.4.27` - MIME type detection for documents
- `Pillow==11.0.0` - Image processing for medical imaging

### Added - Database Migrations

- `010_add_messages.py` - Messages table with encryption support
- `011_add_medical_documents.py` - Medical documents storage table
- `012_add_medical_record_shares.py` - Medical record sharing system

### Added - API Endpoints

**Messaging**

- `POST /api/v1/messages/` - Send encrypted message
- `GET /api/v1/messages/` - List messages (inbox + sent)
- `GET /api/v1/messages/stats` - Messaging statistics
- `GET /api/v1/messages/conversation/{user_id}` - Full conversation
- `GET /api/v1/messages/{id}` - Message details (auto-mark as read)
- `POST /api/v1/messages/{id}/read` - Mark as read
- `DELETE /api/v1/messages/{id}` - Soft delete

**Documents**

- `POST /api/v1/documents/upload` - Upload medical document
- `GET /api/v1/documents/patient/{id}` - Patient's documents
- `GET /api/v1/documents/stats` - Storage statistics
- `GET /api/v1/documents/{id}` - Document metadata
- `GET /api/v1/documents/{id}/download` - Download file
- `PATCH /api/v1/documents/{id}` - Update metadata
- `DELETE /api/v1/documents/{id}` - Archive document

**Sharing**

- `POST /api/v1/shares/` - Create share link
- `GET /api/v1/shares/` - List user's shares
- `POST /api/v1/shares/access` - Access shared record (public)
- `GET /api/v1/shares/{id}` - Share details
- `DELETE /api/v1/shares/{id}` - Revoke share

### Added - Documentation

- `docs/NEW_FEATURES_V3.md` - Complete guide to all new features
- `docs/QUICK_START_V3.md` - Quick start guide for developers
- Updated API documentation with new endpoints
- Added usage examples for all features

### Security - Enhanced

- ✅ Message encryption at rest (AES-256-GCM)
- ✅ Document integrity verification (SHA-256)
- ✅ Secure random tokens for sharing (secrets.token_urlsafe)
- ✅ PIN protection for shared records
- ✅ Comprehensive audit logging for all PHI access
- ✅ Rate limiting on all new endpoints
- ✅ RGPD/HIPAA/HDS compliance maintained
- ✅ No PHI in logs or error messages
- ✅ IP tracking for shared record access

### Changed

- Enhanced `User` model with message relationships
- Enhanced `Patient` model with document relationship
- Updated `app/main.py` to include new routers
- Extended Celery tasks with notification jobs
- Updated `requirements.txt` with new dependencies

### Performance

- Optimized database indexes for messages, documents, and shares
- Composite indexes for common query patterns
- Redis caching ready for document metadata
- Async file upload processing

### Compliance

- Full RGPD compliance with consent tracking
- HIPAA-compliant audit trails
- HDS-ready architecture
- Patient data portability support
- Right to erasure (soft deletes)

### Roadmap - Completed

- ✅ Secure messaging system
- ✅ Medical document management
- ✅ Automated notifications
- ✅ Controlled record sharing

### Roadmap - Q2 2026

- 📊 Advanced analytics and professional dashboards
- 💳 Payment integration (Stripe/PayPal)
- 📹 Telemedicine module (WebRTC/Twilio Video)
- 📱 React Native mobile app

## [2.0.0] - 2024-10-31 - Production Release 🚀

### Added - Production Finalization

#### Security Enhancements

- Updated `python-jose` from 3.3.0 to 3.4.0 (fixes PYSEC-2024-232, PYSEC-2024-233)
- Updated `python-multipart` from 0.0.12 to 0.0.18 (fixes GHSA-59g5-xgcq-4qw3)
- Updated `fastapi` to 0.115.6 for latest security patches
- Created `security.txt` file for vulnerability disclosure program
- Added comprehensive production security checklist

#### Documentation

- Created `PRODUCTION_CHECKLIST.md` with 32 comprehensive sections covering:
  - Pre-deployment security verification (7 sections)
  - Infrastructure deployment (6 sections)
  - Monitoring & observability (4 sections)
  - Compliance & legal (4 sections)
  - Performance & scalability (3 sections)
  - Backup & disaster recovery (2 sections)
  - Maintenance & support (3 sections)
  - Final verification (3 sections)
- Added security vulnerability disclosure process
- Documented emergency contacts and escalation procedures

### Fixed - Production Finalization

- Fixed deprecated `datetime.utcnow()` calls in tests (Python 3.12+ compatibility)
- Replaced with `datetime.now(timezone.utc)` for timezone-aware datetime handling
- Resolved dependency conflicts between FastAPI and Starlette versions
- All 104 unit tests now passing without deprecation warnings

### Changed - Production Finalization

- Frontend dependencies installed and verified (npm install successful)
- Frontend production build tested and working (70.14 kB gzipped)
- Updated Python dependencies to latest secure versions
- Enhanced security posture for production deployment

### Security

- **Zero known vulnerabilities** in Python dependencies (pip-audit clean with ignored system packages)
- All security patches applied and tested
- Production deployment checklist ensures security best practices

### Added - Continuous Improvement Cycle Iteration 5

#### Type Safety & Testing Infrastructure

- Established mypy baseline configuration with gradual typing approach
- Created comprehensive smoke test suite (`tests/test_smoke.py`) with 8 test classes and 15+ tests covering:
  - Health checks and API documentation
  - Authentication flows (login, token validation, user profile)
  - Patient management (list, create, retrieve)
  - Appointment listing
  - Dashboard statistics
  - Access control and authorization
- Integrated mypy type checking into CI/CD pipeline with continue-on-error for gradual adoption
- Added smoke tests to CI/CD pipeline running against docker compose stack
- Configured strict type checking for core modules (`app.core.*`, `app.routers.*`)

#### Documentation Enhancements

- Added comprehensive CI/CD pipeline architecture diagram in `ARCHITECTURE.md` showing:
  - Complete pipeline flow from source control to deployment
  - Security scanning integration (CodeQL, pip-audit, Trivy, Gitleaks)
  - Testing stages (unit, integration, contract, smoke tests)
  - Deployment stages (staging, production)
- Enhanced README testing section with:
  - Smoke test usage documentation
  - Complete CI/CD testing pipeline overview
  - Test coverage metrics (77%, 65 tests)
  - Test types descriptions
- Created `ITERATION_5_SUMMARY.md` documenting all iteration 5 achievements

#### Process & Backlog Management

- Updated `BACKLOG.md` with iteration 5 completion status
- Moved completed items (BACK-501, BACK-502, BACK-503) to completed section
- Added iteration 4 completed items to backlog history

### Changed - Continuous Improvement Cycle Iteration 5

- Updated `requirements.txt` to use `strawberry-graphql[fastapi]>=0.260.0` for better pydantic compatibility
- Enhanced CI workflow with mypy type checking step
- Enhanced CI workflow with smoke test execution after docker compose validation

### Added - Continuous Improvement Cycle Iteration 4

#### CI/CD

- Updated Codecov uploads to use the v5 `files` input and tolerate transient failures, restoring backend/frontend job stability.
- Upgraded GitHub CodeQL actions to v3 and guarded the analysis job against forked pull requests where security events cannot be published.
- Adopted the latest `actions/setup-python@v5` across workflows for consistent toolchain provisioning.
- Fixed backend CodeQL job triggering on forked pull requests by gating the workflow on same-repo events only.
- Added a docker-compose smoke test job that builds the stack, waits for health, and surfaces backend logs on failure.

#### Infrastructure

- Aligned backend Docker image with the supported Python 3.11 base to match local/runtime environments and ensure prebuilt database drivers are available during builds.
- Hardened Alembic migrations to no-op when base tables are provisioned later by SQLAlchemy metadata, allowing greenfield environments to bootstrap without schema conflicts.
- Removed deprecated `version` declaration from `docker-compose.yml` to silence warnings on Compose v2.

#### Frontend

- Removed legacy default `React` import from the error boundary to restore TypeScript build compatibility with the new JSX transform.

#### Security & Dependencies

- Pinned `bcrypt` to 4.1.2 to remain compatible with Passlib and avoid runtime attribute errors during container start-up.

#### Documentation

- Documented tenant-aware seeding expectations and CI automation in `docs/DEVELOPMENT.md`.

### Added - Continuous Improvement Cycle Iteration 3

#### Security & Dependencies

- Updated Starlette to 0.41.2 (latest version compatible with FastAPI 0.115.x) including the fix for CVE GHSA-7f5h-v6xp-fcq8 (FileResponse Range parsing CPU exhaustion)
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

For questions or issues, please contact: <contact@isdataconsulting.com>
