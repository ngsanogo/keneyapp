# Quick Reference: New Features v3.2

## 🔔 Appointment Reminders

### Create Reminders
```python
# In appointment creation/update
from app.services.reminder_service import ReminderService

service = ReminderService(db)
reminders = service.create_reminders_for_appointment(
    appointment_id=appointment.id,
    tenant_id=tenant_id,
    channels=[ReminderChannel.EMAIL, ReminderChannel.SMS],
    hours_before=[24, 2]  # 24h and 2h before
)
```

### API Usage
```bash
# Create reminders
POST /api/v1/reminders/bulk
{
  "appointment_id": 123,
  "channels": ["email", "sms"],
  "hours_before": [24, 2]
}

# Get appointment reminders
GET /api/v1/reminders/appointment/123

# Cancel reminders
DELETE /api/v1/reminders/appointment/123

# Process due reminders (Admin)
POST /api/v1/reminders/process
```

---

## 📜 Medical History Timeline

### Frontend Usage
```tsx
import MedicalHistoryTimeline from './components/MedicalHistoryTimeline';

<MedicalHistoryTimeline
  patientId={123}
  startDate="2024-01-01"
  endDate="2024-12-31"
  eventTypes={['appointment', 'prescription']}
/>
```

### API Usage
```bash
# Get timeline
GET /api/v1/patients/123/history?start_date=2024-01-01&end_date=2024-12-31&sort=desc

# With filters
GET /api/v1/patients/123/history?event_types[]=appointment&event_types[]=prescription
```

### Event Types
- `appointment` - Appointments with doctors
- `prescription` - Medication prescriptions
- `lab_result` - Lab test results
- `document` - Medical documents
- `note` - Clinical notes

---

## 💊 Prescription Refill Workflow

### Models Available
```python
from app.models.prescription_refill import (
    PrescriptionRefillRequest,
    RefillRequestStatus
)

# Status workflow
PENDING → APPROVED → FULFILLED
        ↓
      DENIED
```

### Create Refill Request (Patient)
```python
request = PrescriptionRefillRequest(
    tenant_id=tenant_id,
    prescription_id=prescription.id,
    patient_id=patient.id,
    doctor_id=prescription.doctor_id,
    reason="Running low on medication",
    patient_notes="Need for next week",
    pharmacy_name="CVS Pharmacy",
    pharmacy_phone="555-1234"
)
db.add(request)
db.commit()
```

### Review Request (Doctor)
```python
request.status = RefillRequestStatus.APPROVED
request.reviewed_by_id = doctor.id
request.reviewed_at = datetime.now()
request.review_notes = "Approved for one refill"
db.commit()
```

---

## 🏥 Database Migrations

### Apply Migrations
```bash
# Upgrade to latest
alembic upgrade head

# Check current version
alembic current

# View history
alembic history

# Downgrade one version
alembic downgrade -1
```

### New Tables
1. `appointment_reminders` - Automated reminders
2. `prescription_refill_requests` - Refill workflow (schema ready)

---

## 🧪 Testing

### Run Backend Tests
```bash
# All tests
pytest tests/ -v

# Specific feature
pytest tests/test_reminder_service.py -v

# With coverage
pytest tests/test_reminder_service.py --cov=app.services.reminder_service
```

### Run Frontend Tests
```bash
cd frontend

# All tests
npm test

# Specific component
npm test -- MedicalHistoryTimeline

# Coverage
npm test -- --coverage
```

---

## ⚙️ Celery Configuration

### Add to celeryconfig.py
```python
from celery.schedules import crontab

beat_schedule = {
    'process-appointment-reminders': {
        'task': 'process_appointment_reminders',
        'schedule': crontab(minute='*/15'),
    },
}
```

### Run Celery
```bash
# Worker
celery -A app.core.celery_app worker --loglevel=info

# Beat scheduler
celery -A app.core.celery_app beat --loglevel=info

# Both (development)
celery -A app.core.celery_app worker --beat --loglevel=info
```

---

## 🎨 Frontend Components

### Medical History Timeline Props
```typescript
interface MedicalHistoryTimelineProps {
  patientId: number;           // Required
  startDate?: string;          // Optional: YYYY-MM-DD
  endDate?: string;            // Optional: YYYY-MM-DD
  eventTypes?: string[];       // Optional: filter types
}
```

### Event Object Structure
```typescript
interface TimelineEvent {
  id: number | string;
  date: string;               // ISO 8601
  type: 'appointment' | 'prescription' | 'lab_result' | 'document' | 'note';
  title: string;
  description: string;
  doctor?: string;
  status?: string;
  metadata?: Record<string, any>;
}
```

---

## 🔐 Authorization

### Reminder Endpoints
- `POST /reminders/bulk` - Admin, Doctor, Receptionist
- `GET /reminders/appointment/{id}` - Admin, Doctor, Receptionist
- `DELETE /reminders/appointment/{id}` - Admin, Doctor, Receptionist
- `POST /reminders/process` - **Admin only**

### History Endpoint
- `GET /patients/{id}/history` - Admin, Doctor, Nurse

### Refill Endpoints (Planned)
- `POST /refill-requests/` - Patient, Admin, Doctor
- `POST /refill-requests/{id}/review` - Doctor, Admin
- `GET /refill-requests/` - All (filtered by role)

---

## 🚨 Common Issues & Solutions

### Reminder Not Sending
1. Check Celery worker is running
2. Verify notification service configuration
3. Check reminder status in database
4. Review error logs

### Timeline Not Loading
1. Verify patient ID is correct
2. Check authentication token
3. Ensure patient has events
4. Check browser console for errors

### Database Migration Failed
1. Check current migration version: `alembic current`
2. Verify database connection
3. Review migration file for errors
4. Downgrade and retry: `alembic downgrade -1 && alembic upgrade head`

---

## 📊 Monitoring

### Key Metrics to Track
- Reminder success rate
- Average reminder delivery time
- Timeline API response time
- Refill request approval time
- Patient engagement metrics

### Logging
```python
import logging
logger = logging.getLogger(__name__)

# Examples
logger.info(f"Created {count} reminders for appointment {id}")
logger.error(f"Failed to send reminder {id}: {error}")
```

---

## 🎯 Performance Tips

### Backend
1. Use database indexes (already added)
2. Implement caching for timeline data
3. Paginate large result sets
4. Use background tasks for heavy operations

### Frontend
1. Implement virtual scrolling for long timelines
2. Lazy load timeline events
3. Cache API responses
4. Debounce filter changes

---

## 📱 Mobile Responsiveness

All frontend components are mobile-responsive:
- **Desktop:** Full layout with all features
- **Tablet:** Optimized 2-column layout
- **Mobile:** Single column with touch-friendly controls

Breakpoints:
- Desktop: > 768px
- Tablet: 768px - 480px
- Mobile: < 480px

---

## 🔄 Workflow Examples

### Complete Appointment Flow
1. Create appointment
2. Auto-create reminders (24h, 2h before)
3. Celery processes due reminders
4. Notification sent to patient
5. Patient receives email/SMS
6. Appointment recorded in timeline

### Prescription Refill Flow
1. Patient views prescriptions
2. Patient requests refill
3. Doctor receives notification
4. Doctor reviews and approves/denies
5. If approved, pharmacy notified
6. Refill recorded in timeline

---

## 📞 Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. Review error messages
3. Consult API documentation: `/docs`
4. Check test cases for examples

---

*Last Updated: November 30, 2025*
