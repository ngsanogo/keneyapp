# KeneyApp Integration Roadmap

This document captures the current-state audit of the upstream GNU Health
repositories and lays out the backlog required to elevate KeneyApp to a
production-ready, enterprise healthcare information system.

It is meant to be a living plan: once an iteration is delivered we loop back,
update this document, and proceed to the next set of priorities.

---

## 1. Source Systems Audit

| Repository (tmp/…) | Primary Domain | Notable Capabilities | Integration Opportunities |
|--------------------|----------------|----------------------|---------------------------|
| **his** | Core HIS (Tryton server modules) | Extensive patient administration, hospitalisation, laboratory, billing, stock, insurance, HL7 listeners | Reuse data models, FHIR/HL7 event listeners, workflows for admissions/discharge, invoicing logic |
| **his-client** | GNU Health desktop client | GTK-based UI on top of Tryton services, patient charts, appointment views, lab results | Reference UX flows and terminology for role-specific dashboards; potential API parity requirements |
| **his-utils** | Deployment & operations | `gnuhealth-control`, installer scripts, backup & patching automation, testing harnesses | Seed backup/restore + maintenance scripts into KeneyApp DevOps toolchain |
| **mygnuhealth** | Personal health record (Go / Fyne) | Patient-facing app, wellness tracking, appointment follow-up | Provide roadmap for patient portal/mobile integration and data sharing consent workflows |
| **gnuh-health-thalamus / pywebdav3-server** | Telehealth middleware & document exchange | REST bridge, ICS calendar, WebDAV repository | Evaluate for interoperability, scheduling synchronisation, secure document storage |
| **futurepages / pages / testpages** | Static site content, documentation | Marketing website, documentation stubs | Use for public docs / help centre within KeneyApp |
| **ansible** | Infrastructure-as-code | Playbooks for GNU Health stack | Translate to Terraform/Helm where relevant; reuse security hardening tasks |

Additional notes:

- The GNU Health ecosystem leans heavily on Tryton modules (Python) for server-side logic; KeneyApp uses FastAPI/SQLAlchemy. We must map the business objects (patients, encounters, labs, invoices) and port the behaviour progressively.
- HL7/FHIR integrations exist (listeners, message processors). These should be analysed to design KeneyApp’s interoperability layer.
- Utility scripts (backups, patching, DB maintenance) can accelerate our DevOps/stability work.

---

## 2. Gap Analysis vs. KeneyApp

### Backend Capabilities

| Feature | Current KeneyApp | From GNU Health | Action Items |
|---------|------------------|-----------------|--------------|
| User & Role Management | Basic CRUD, JWT auth | Multi-role hierarchy, activity tracking, user provisioning tools | Expand RBAC matrix, add account lifecycle (create/disable/reset), MFA, audit reporting |
| Patient Master Data | Demographics, allergies, basic history | Detailed clinical history, encounters, insurance, family, social determinants | Extend schema (encounters, observations), implement relationship models, import utilities |
| Appointments | CRUD with status, reminders | Multi-resource scheduling, waiting lists, ICS sync | Enhance scheduling logic, incorporate provider availability, email/SMS notifications |
| Prescriptions | CRUD + interaction task placeholder | Medication templates, e-prescription workflows, stock linkage | Add medication catalogue, approval flow, digital signature, pharmacy integration |
| Analytics / KPIs | Basic dashboard counters | Clinical KPIs, financial, public health indicators | Build data mart / aggregated metrics, embed Grafana dashboards |
| Interoperability | Not yet (placeholders) | HL7 listeners, FHIR resources, telehealth bridge | Design API gateway, inbound/outbound connectors, message validation |
| Billing / Insurance | Missing | Insurance contracts, invoices, claims | Create financial modules, integrate with patient ledger |

### Frontend (React)

- Needs full navigation shell (multi-role dashboards).
- Implement patient chart UI (tabs: demographics, encounters, labs, prescriptions).
- Appointment calendar with drag & drop, resource filtering.
- Administration console (users, roles, audit logs, system configs).
- Reports/analytics w/ data visualisations (can embed Grafana or build custom).
- Accessibility (WCAG) & localisation (i18n) absent — must add.

### DevOps / Compliance

- CI/CD: GitHub Actions pipeline needs multi-stage testing (lint, unit, integration, security scans).
- Secrets management (Vault/KMS) & SOPS integration TBD.
- Database migrations + seeding automated (incl. backup & restore).
- Monitoring/alerting: Prometheus metrics exist but need alert rules & dashboards.
- Security: vulnerability scans (Snyk/Trivy), penetration testing, HIPAA audit trails.

---

## 3. Roadmap & Iterations

1. **Authentication & Authorization Hardening**
   - Full RBAC matrix, account lifecycle (create/disable/reset).
   - Multifactor authentication (TOTP/SMS).
   - Session management, device tracking, consent logging.

2. **Patient & Clinical Data Model Expansion**
   - Lift Tryton models for patients, encounters, observations, allergies, insurance.
   - Build migration scripts & validation tests.
   - API endpoints (REST + GraphQL) with proper access controls.

3. **Scheduling & Workflow**
   - Advanced appointment engine (resource calendars, multi-provider).
   - Reminder daemon (email/SMS push) integrated via Celery.
   - Waiting list management, triage priorities.

4. **Medication & Orders**
   - Medication catalogue, formulary management.

- Prescription workflow (draft/approve/dispense, interaction checks).
- E-signature integration, audit trails.

5. **Interoperability Layer**
   - FHIR resources (Patient, Encounter, Observation, MedicationRequest, etc.).
   - HL7 v2 listeners, message mapping from GNU Health modules.
   - External system connectors (Thalamus, telehealth, labs).

6. **Financials & Insurance**
   - Insurance policy management, billing, claim submissions.
   - Integration with accounting systems (optional).

7. **Frontend Experience**
   - Responsive UI for each role with localisation.
   - Patient chart, scheduling calendar, admin console.
   - Accessibility compliance audits.

8. **DevOps / Quality**
   - GitHub Actions pipeline with full test matrix (pytest, mypy, lint, Cypress).
   - Container hardening (Trivy), dependency auditing (pip-audit, npm audit).
   - Backup & disaster recovery scripts (inspired by `his-utils`).
   - Observability: dashboards & alerting policies.

Each iteration ends with:

- Updated documentation (API, runbooks, deployment).
- Automated tests covering new functionality.
- Docker build/run validation (local & CI).

---

## 4. Next Steps

1. Finalise detailed requirements per iteration (user stories, acceptance criteria).
2. Stand-up integration tests against seeded data (patients, users).
3. Start with Iteration 1 — Authentication & Authorization hardening:
   - Derive RBAC matrix from GNU Health roles.
   - Implement user lifecycle APIs & UI.
   - Add MFA & session audit logging.

Progress will be tracked directly in this document, updating sections as milestones are delivered.
