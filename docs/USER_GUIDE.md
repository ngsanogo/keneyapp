# User Guide

This guide explains how clinicians, admins, and staff use KeneyApp day to day. It covers onboarding, core workflows, and the features introduced in v3.0.

## Getting Started

1. **Sign in** with organization credentials or via configured OAuth2/OIDC provider (Google, Microsoft, Okta).
2. **Select your role** (Admin, Doctor, Nurse, Receptionist) if prompted; navigation adapts to your permissions.
3. **Complete profile** (contact info, specialties) to tailor notifications and dashboard widgets.
4. **Set preferences** (timezone, notification channels, language) from the profile/settings page.

## Navigation Overview

- **Dashboard:** Personalized KPIs, upcoming appointments, unread messages, and recent documents.
- **Patients:** Search, filter, and open patient charts; view demographics, history, allergies, and active plans.
- **Appointments:** Create, reschedule, cancel, and check-in patients with calendar and list views.
- **Prescriptions:** Create prescriptions with dosage, refills, and pharmacy notes; export or send electronically.
- **Messaging:** Secure, end-to-end encrypted threads with patients and internal teams; supports attachments.
- **Documents:** Upload, tag, and share lab results, imaging, vaccination records, and visit summaries.
- **Notifications:** Manage email/SMS preferences and view delivery history for reminders and digests.

## Core Workflows

### Patient Management

1. Search for a patient by name, MRN, or national identifier.
2. Review demographics, conditions, allergies, and medications.
3. Add notes or attach documents; updates are logged for auditability.
4. Share chart extracts securely via time-bound links when permitted.

### Appointment Scheduling

1. Open **Appointments** and click **New Appointment**.
2. Select patient, provider, location, and time; set status (scheduled, confirmed, completed, cancelled).
3. Enable reminders (email/SMS) and add internal notes.
4. Use calendar filters by provider, location, or modality (in-person/telemedicine).

### Prescriptions

1. From the patient chart, choose **New Prescription**.
2. Add medication, dosage, frequency, duration, and refill count; reference ATC codes when available.
3. Generate a printable/exportable prescription or send to the configured pharmacy integration.
4. Track renewal needs and document dispensing notes.

### Secure Messaging

1. Start a thread from the patient chart or messaging inbox.
2. Exchange messages with attachments; messages are encrypted end to end.
3. Mark critical updates for escalated notifications (email/SMS) when configured.

### Documents & Imaging

1. Upload PDFs, images, or structured results and tag them (lab, imaging, vaccination, referral, visit note).
2. Preview files, add context notes, and relate them to appointments or orders.
3. Create secure sharing links with expiration for external providers.

### Notifications

- Appointment reminders, result availability, and prescription renewals trigger notifications.
- Users can opt in/out per channel (email/SMS) and review a delivery log from the notifications center.

### Analytics (v3.0 Roadmap)

- View dashboards for patient throughput, no-show rate, prescription renewals, and messaging SLAs.
- Future releases add drill-downs and exportable KPI reports.

## Tips & Shortcuts

- **Keyboard navigation:** Use global search to jump to patients, appointments, or documents.
- **Filters:** Save common filters (e.g., provider, location) in appointments and documents.
- **Audit trail:** Key actions are logged; admins can export audit reports from the settings area.
- **Offline-safe drafts:** Draft notes, prescriptions, and messages persist until submitted.

## Support & Troubleshooting

- **Access issues:** Verify role assignment and OAuth provider access; contact an admin if menus are missing.
- **Performance:** Check connectivity, then consult [Performance Guide](PERFORMANCE_GUIDE.md) for client/server tips.
- **Incidents:** Follow the [Operations Runbook](OPERATIONS_RUNBOOK.md) and report critical issues via the incident hotline.

For developer-focused details, see the [Codebase Overview](CODEBASE_OVERVIEW.md). For deployment topics, start with the [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md).
