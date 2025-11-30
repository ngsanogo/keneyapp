# New Features Guide - v3.1.0

This guide documents the new features added to KeneyApp in version 3.1.0, focusing on enhanced user experience, analytics, and notification management.

## Table of Contents

1. [Advanced Patient Search](#advanced-patient-search)
2. [Enhanced Notification System](#enhanced-notification-system)
3. [Custom Date Range Analytics](#custom-date-range-analytics)
4. [Patient Data Export](#patient-data-export)
5. [Bulk Operations](#bulk-operations)

---

## Advanced Patient Search

### Overview

The advanced patient search feature allows healthcare providers to find patients using multiple filter criteria beyond basic text search.

### Endpoint

```http
POST /api/v1/patients/search/advanced
```

### Features

- **Text Search**: Search across name, email, phone, and address
- **Demographics**: Filter by gender, age range, date of birth
- **Location**: Filter by city or country
- **Medical Flags**: Find patients with/without allergies or medical history
- **Date Ranges**: Filter by record creation or update dates
- **Sorting**: Sort by various fields (name, DOB, email, dates)
- **Pagination**: Standard pagination support

### Request Example

```json
{
  "search": "John",
  "gender": "male",
  "min_age": 30,
  "max_age": 50,
  "has_allergies": true,
  "city": "Paris",
  "sort_by": "last_name",
  "sort_order": "asc",
  "page": 1,
  "page_size": 20
}
```

### Response

Returns a paginated list of patients matching all specified criteria:

```json
{
  "items": [...],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### Use Cases

- Find all diabetic patients over 60
- Locate patients with specific allergies for recall campaigns
- Search patients by location for regional health programs
- Filter newly registered patients within a date range

---

## Enhanced Notification System

### Overview

A comprehensive notification management system with multi-channel support, user preferences, and notification history tracking.

### Features

#### 1. Notification Channels

- **Email**: Traditional email notifications
- **SMS**: Text message alerts (requires Twilio configuration)
- **Push**: Browser/mobile push notifications
- **WebSocket**: Real-time in-app notifications

#### 2. Notification Types

- Appointment reminders and confirmations
- Lab results availability
- Prescription renewal reminders
- Message notifications
- Document sharing alerts
- System and security alerts

#### 3. User Preferences

Users can customize their notification preferences per channel and type.

### Endpoints

#### Get Notifications

```http
GET /api/v1/notifications/
```

Query parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50)
- `unread_only`: Boolean to filter unread notifications
- `type`: Filter by notification type

#### Get Notification Statistics

```http
GET /api/v1/notifications/stats
```

Returns:
```json
{
  "total": 150,
  "unread": 12,
  "by_type": {
    "appointment_reminder": 45,
    "lab_results_ready": 30,
    "message_received": 75
  },
  "by_status": {
    "sent": 130,
    "read": 138,
    "pending": 12
  }
}
```

#### Mark as Read

```http
POST /api/v1/notifications/mark-read
```

Request:
```json
{
  "notification_ids": [1, 2, 3]
}
```

#### Get/Update Preferences

```http
GET /api/v1/notifications/preferences
PUT /api/v1/notifications/preferences
```

Preference options:
```json
{
  "email_enabled": true,
  "email_appointment_reminders": true,
  "email_lab_results": true,
  "sms_enabled": false,
  "push_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00"
}
```

#### Send Bulk Notifications (Admin/Doctor Only)

```http
POST /api/v1/notifications/send
```

Request:
```json
{
  "user_ids": [1, 2, 3],
  "type": "appointment_reminder",
  "channels": ["email", "push"],
  "title": "Appointment Reminder",
  "message": "You have an appointment tomorrow at 10:00 AM",
  "action_url": "/appointments/123",
  "respect_preferences": true
}
```

### Quiet Hours

Users can set quiet hours during which non-critical notifications won't be sent. Security and system alerts override quiet hours.

---

## Custom Date Range Analytics

### Overview

Enhanced analytics with flexible custom date ranges for better insights into healthcare operations.

### New Endpoints

#### Custom Period Metrics

```http
GET /api/v1/analytics/custom-period
```

Query parameters:
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)

**Flexible Date Handling:**
- Both dates: Exact range
- Only `date_from`: From date to now
- Only `date_to`: 30 days before to date_to
- Neither: Last 30 days (default)

Response:
```json
{
  "period_start": "2024-01-01",
  "period_end": "2024-01-31",
  "total_patients": 1250,
  "new_patients": 45,
  "total_appointments": 320,
  "completed_appointments": 285,
  "cancelled_appointments": 15,
  "pending_appointments": 20,
  "total_prescriptions": 245,
  "unique_doctors_seen": 8
}
```

#### Age Distribution

```http
GET /api/v1/analytics/age-distribution
```

Returns patient counts across 9 age ranges (0-10, 11-20, ..., 81+):

```json
{
  "labels": ["0-10", "11-20", "21-30", ...],
  "values": [45, 78, 120, ...]
}
```

#### Doctor Performance (Admin Only)

```http
GET /api/v1/analytics/doctor-performance
```

Query parameters:
- `date_from`: Optional start date
- `date_to`: Optional end date

Response:
```json
{
  "doctor_names": ["Dr. Smith", "Dr. Johnson"],
  "appointments_count": [145, 132],
  "completion_rate": [95.2, 87.8],
  "average_rating": [4.5, 4.5]
}
```

### Use Cases

- Compare performance across quarters
- Analyze seasonal patient trends
- Generate custom period reports for stakeholders
- Monitor doctor workload and efficiency
- Track age demographics for targeted health programs

---

## Patient Data Export

### Overview

Export patient data in multiple formats for reporting, analysis, and compliance.

### Endpoint

```http
GET /api/v1/patients/export/{format}
```

### Supported Formats

- **CSV**: Comma-separated values for spreadsheet applications
- **PDF**: Formatted report suitable for printing
- **JSON**: Structured data for integration

### Query Parameters

- `search`: Text search filter
- `include_sensitive`: Include medical history and allergies (Admin/Doctor only)

### Example Requests

```bash
# Export all patients as CSV
GET /api/v1/patients/export/csv

# Export filtered patients with sensitive data
GET /api/v1/patients/export/pdf?search=diabetes&include_sensitive=true

# Export for integration
GET /api/v1/patients/export/json
```

### Security

- Only authorized roles can export
- Sensitive data (medical history, allergies, emergency contacts) requires special permission
- All exports are logged in audit trail
- Files include timestamp in filename

### File Naming

- CSV: `patients_export_YYYYMMDD_HHMMSS.csv`
- PDF: `patients_report_YYYYMMDD_HHMMSS.pdf`
- JSON: `patients_export_YYYYMMDD_HHMMSS.json`

---

## Bulk Operations

### Overview

Perform operations on multiple records simultaneously for efficiency.

### Bulk Delete Patients

```http
POST /api/v1/patients/bulk/delete
```

Request:
```json
{
  "patient_ids": [1, 2, 3, 4, 5],
  "confirm": true
}
```

Response:
```json
{
  "success": true,
  "total": 5,
  "successful": 5,
  "failed": 0,
  "errors": [],
  "message": "Successfully deleted 5 patients."
}
```

### Constraints

- Maximum 100 patients per request
- Requires confirmation flag
- Admin access only
- Failed deletions are reported with reasons
- Partial success supported

### Error Handling

If some deletions fail:

```json
{
  "success": false,
  "total": 5,
  "successful": 3,
  "failed": 2,
  "errors": [
    {
      "patient_id": 4,
      "error": "Patient not found or access denied"
    },
    {
      "patient_id": 5,
      "error": "Cannot delete patient with active appointments"
    }
  ],
  "message": "Successfully deleted 3 patients. 2 failed."
}
```

---

## Migration Guide

### Database Migration

Run the Alembic migration to add notification tables:

```bash
# Set environment variable for autogenerate
$env:ALEMBIC_AUTOGENERATE="1"

# Run migration
alembic upgrade head
```

### Environment Variables

Add to `.env` if using SMS notifications:

```env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
```

### Testing

Run the new test suites:

```bash
# Test notifications
pytest tests/test_notifications.py -v

# Test enhanced analytics
pytest tests/test_analytics_enhanced.py -v
```

---

## Performance Considerations

### Caching

All new features leverage the existing caching infrastructure:

- Patient search results are cached with parameter-based keys
- Analytics queries cache for 60-300 seconds
- Notification preferences cached per user

### Rate Limiting

New endpoints follow project rate limiting standards:

- Patient search: 50/minute
- Notification endpoints: 50-100/minute
- Bulk operations: 5/minute
- Analytics: 100/minute

### Pagination

All list endpoints support pagination:

- Default page size: 50
- Maximum page size: 200 (100 for exports)

---

## Security & Compliance

### Audit Logging

All new features include comprehensive audit logging:

- Patient searches logged with filter criteria
- Notification sends tracked with recipients
- Bulk operations logged with success/failure details
- Analytics queries logged with date ranges
- Exports logged with scope and sensitive data flag

### RBAC

Role-based access control enforced:

- **Admin**: Full access to all features
- **Doctor**: Access to notifications, analytics, exports (with sensitive data)
- **Nurse**: Limited notification and analytics access
- **Receptionist**: Basic notification and search access

### Data Privacy

- PHI encrypted at rest
- Notification preferences stored securely
- Export sensitive data requires additional permission
- Audit trail for all data access

---

## Frontend Integration

### Patient Search Component

```typescript
// Example usage in React
const searchPatients = async (filters) => {
  const response = await fetch('/api/v1/patients/search/advanced', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(filters)
  });
  return response.json();
};
```

### Notification Center

```typescript
// Get user notifications
const getNotifications = async (page = 1, unreadOnly = false) => {
  const params = new URLSearchParams({
    page: page.toString(),
    unread_only: unreadOnly.toString()
  });
  
  const response = await fetch(`/api/v1/notifications/?${params}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};

// Mark notifications as read
const markAsRead = async (notificationIds) => {
  await fetch('/api/v1/notifications/mark-read', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ notification_ids: notificationIds })
  });
};
```

### Analytics Dashboard

```typescript
// Get custom period metrics
const getCustomMetrics = async (dateFrom, dateTo) => {
  const params = new URLSearchParams();
  if (dateFrom) params.append('date_from', dateFrom);
  if (dateTo) params.append('date_to', dateTo);
  
  const response = await fetch(`/api/v1/analytics/custom-period?${params}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};
```

---

## Troubleshooting

### Notifications Not Sending

1. Check SMTP/Twilio configuration in `.env`
2. Verify user notification preferences
3. Check audit logs for delivery failures
4. Ensure quiet hours not blocking sends

### Analytics Performance

1. Use specific date ranges instead of defaults
2. Enable caching in production
3. Consider indexing on frequently queried date fields
4. Limit data requests during peak hours

### Bulk Operations Timing Out

1. Reduce batch size below maximum
2. Check database connection pool
3. Consider using background tasks for large batches
4. Monitor system resources during operations

---

## Roadmap

### Planned Enhancements

- [ ] Push notification support via FCM/APNS
- [ ] Email templates customization
- [ ] Advanced analytics with ML predictions
- [ ] Scheduled bulk operations
- [ ] Notification delivery retry logic
- [ ] Export scheduling and automation

---

## Support

For questions or issues with new features:

- Check the [main documentation](../README.md)
- Review [API documentation](API_REFERENCE.md)
- Open an issue on [GitHub](https://github.com/ngsanogo/keneyapp/issues)
- Refer to [DEVELOPMENT.md](DEVELOPMENT.md) for contribution guidelines
