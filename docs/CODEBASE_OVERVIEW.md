# Codebase Overview

This guide orients new contributors to the KeneyApp codebase, highlights key services, and links to deeper technical references.

## High-Level Architecture

- **Backend (FastAPI / Python):** REST and GraphQL APIs, business logic, background tasks, and data access.
- **Frontend (React + TypeScript):** Single-page app for clinicians, admins, and patients.
- **Data Layer:** PostgreSQL with Alembic migrations; Redis for caching, sessions, and Celery task queues.
- **Async Workloads:** Celery workers for notifications, document processing, analytics jobs, and long-running workflows.
- **Infrastructure:** Docker, Kubernetes manifests, Terraform modules, and GitHub Actions pipelines.
- **Observability:** Prometheus metrics, Grafana dashboards, structured logging, and alerting rules.

## Repository Layout

- `app/` — FastAPI application code
  - `core/` — settings, security (JWT, password hashing), database session management
  - `models/` — SQLAlchemy models for users, patients, appointments, prescriptions, messaging, and documents
  - `routers/` — REST/GraphQL endpoints with RBAC and validation
  - `schemas/` — Pydantic models used across APIs and background tasks
  - `services/` — domain services (notifications, documents, messaging, billing) to keep routers thin
  - `tasks/` — Celery tasks and scheduling helpers
- `frontend/` — React app
  - `src/components/` — UI primitives and shared widgets
  - `src/pages/` — routed pages for login, dashboard, patient records, appointments, prescriptions, and messaging
  - `src/contexts/` — auth/session providers, feature flags, theme settings
  - `src/services/` — API clients, analytics, and feature-specific data hooks
  - `src/styles/` — global styles and design tokens
- `tests/` — Backend unit/integration tests
- `k8s/` — Kubernetes manifests and Helm chart values
- `terraform/` — Infrastructure-as-code modules for cloud environments
- `monitoring/` — Prometheus/Grafana configuration and alert rules
- `scripts/` — Developer automation (linting, formatting, releases, data seeds)

## Key Flows and Features

- **Authentication & RBAC:** OAuth2/OIDC support, JWT sessions, role-based routes per Admin/Doctor/Nurse/Receptionist.
- **Patient Records:** CRUD APIs and UI for demographics, conditions, allergies, and medical history with FHIR-compatible schemas.
- **Appointments:** Scheduling, status updates, reminders, and calendar views.
- **Prescriptions:** Medication details, dosages, refills, and pharmacy export.
- **Secure Messaging:** End-to-end encrypted messaging with attachments between clinicians and patients.
- **Documents:** Uploads for lab results, imaging, and vaccination records with controlled sharing links.
- **Notifications:** Email/SMS digests for appointments, results availability, and prescription renewals.
- **Analytics:** Dashboards and KPI widgets (with roadmap for advanced analytics in v3.0).

## Development Workflow

- **Run locally:** `make up` (or see [Quick Start](QUICK_START.md)) to boot backend, frontend, and dependencies.
- **Lint & format:** `make lint` (Python + TypeScript), `make format` to apply standards from the [Coding Standards](CODING_STANDARDS.md).
- **Test:** `make test` for backend unit/integration tests; `make test-performance` for load tests where supported.
- **Database migrations:** Manage with Alembic; see `alembic/` and `alembic.ini` plus patterns in `app/migrations/`.
- **API evolution:** Follow [API Best Practices](API_BEST_PRACTICES.md) and keep schemas updated in `schemas/`.
- **Pull requests:** Apply [Git & GitHub Best Practices](guides/GIT_GITHUB_BEST_PRACTICES.md) and ensure checks pass before merge.

## Observability & Operations

- **Metrics:** Prometheus endpoints exposed by backend; dashboards defined in `monitoring/`.
- **Logging:** Structured JSON logs with PHI-safe filters; see `app/core/logging` (or equivalents) and the [Security Best Practices](SECURITY_BEST_PRACTICES.md).
- **Alerts:** Grafana/Prometheus rules for availability, latency, error rates, and worker backlogs.
- **Runbooks:** Use the [Operations Runbook](OPERATIONS_RUNBOOK.md) and [Disaster Recovery](DISASTER_RECOVERY.md) guides for production events.

## Additional References

- [Architecture Overview](ARCHITECTURE.md) for system design and deployment topology.
- [Technology Choices](TECHNOLOGY_CHOICES.md) for rationale behind the stack.
- [Testing Guide](TESTING_GUIDE.md) for quality gates.
- [Security Compliance](SECURITY_COMPLIANCE.md) and [Encryption Guide](ENCRYPTION_GUIDE.md) for regulatory alignment.
