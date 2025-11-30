**Appointments API**
- **List:** `GET /api/v1/appointments/` — Optional `patient_id`
- **Detail:** `GET /api/v1/appointments/{appointment_id}`
- **Create:** `POST /api/v1/appointments/` — Body: `AppointmentCreate`
- **Update:** `PUT /api/v1/appointments/{appointment_id}` — Body: `AppointmentUpdate`
- **Delete:** `DELETE /api/v1/appointments/{appointment_id}`

**Schemas**
- `AppointmentCreate`: `patient_id`, `doctor_id`, `scheduled_at`, optional `reason`, `location`
- `AppointmentUpdate`: optional `scheduled_at`, `reason`, `location`
- `AppointmentResponse`: `id`, `tenant_id`, fields above, `created_at`, `updated_at`

**Security & RBAC**
- Reads: Admin, Doctor, Nurse
- Writes: Admin, Doctor, Receptionist
- Enforces `tenant_id` from JWT; audited; rate-limited; cached
