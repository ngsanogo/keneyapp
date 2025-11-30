# Batch Operations API Reference

## Overview

The Batch Operations API enables atomic bulk operations on patient records, allowing creation, update, and deletion of multiple patients in a single transaction. All operations are tenant-scoped and include comprehensive audit logging.

## Base URL

```
/api/v1/batch
```

## Authentication

All endpoints require JWT authentication via Bearer token:

```
Authorization: Bearer <your_jwt_token>
```

## Rate Limiting

- **Create/Update/Delete**: 10 requests per minute per user

## Endpoints

### Create Multiple Patients

Create multiple patient records in a single atomic transaction.

**Endpoint:** `POST /batch/patients`

**Request Body:**

```json
[
  {
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "phone": "+1234567890",
    "email": "john.doe@example.com",
    "address": "123 Main St, City, State 12345",
    "medical_history": "No known conditions",
    "allergies": "Penicillin"
  },
  {
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1985-05-15",
    "gender": "female",
    "phone": "+1234567891",
    "email": "jane.smith@example.com"
  }
]
```

**Success Response (201 Created):**

```json
{
  "created": 2,
  "total": 2,
  "patients": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "1990-01-01",
      "gender": "male",
      "phone": "+1234567890",
      "email": "john.doe@example.com",
      "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "first_name": "Jane",
      "last_name": "Smith",
      "date_of_birth": "1985-05-15",
      "gender": "female",
      "phone": "+1234567891",
      "email": "jane.smith@example.com",
      "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Error Response (422 Unprocessable Entity):**

Transaction is rolled back if any validation fails:

```json
{
  "detail": [
    {
      "loc": ["body", 0, "date_of_birth"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/api/v1/batch/patients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "first_name": "John",
      "last_name": "Doe",
      "date_of_birth": "1990-01-01",
      "gender": "male",
      "phone": "+1234567890",
      "email": "john.doe@example.com"
    }
  ]'
```

### Update Multiple Patients

Update multiple patient records atomically.

**Endpoint:** `PUT /batch/patients`

**Request Body:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "+9999999999",
    "email": "newemail@example.com"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "address": "456 Oak Ave, City, State 54321"
  }
]
```

**Success Response (200 OK):**

```json
{
  "updated": 2,
  "patients": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Doe",
      "phone": "+9999999999",
      "email": "newemail@example.com",
      "updated_at": "2024-01-15T10:35:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "first_name": "Jane",
      "last_name": "Smith",
      "address": "456 Oak Ave, City, State 54321",
      "updated_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

**Error Response (404 Not Found):**

If any patient ID is not found or doesn't belong to current tenant:

```json
{
  "detail": "Patient 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**cURL Example:**

```bash
curl -X PUT http://localhost:8000/api/v1/batch/patients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "phone": "+9999999999"
    }
  ]'
```

### Delete Multiple Patients

Delete multiple patient records.

**Endpoint:** `DELETE /batch/patients`

**Request Body:**

```json
[
  "550e8400-e29b-41d4-a716-446655440000",
  "660e8400-e29b-41d4-a716-446655440001",
  "770e8400-e29b-41d4-a716-446655440002"
]
```

**Success Response (200 OK):**

```json
{
  "deleted": 2,
  "requested": 3
}
```

Note: `deleted` may be less than `requested` if some patients don't exist or don't belong to current tenant.

**cURL Example:**

```bash
curl -X DELETE http://localhost:8000/api/v1/batch/patients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001"
  ]'
```

## Transactional Behavior

All batch operations are **atomic**:

- **Success**: All records are created/updated/deleted
- **Failure**: Transaction is rolled back, no changes are made

This ensures data consistency when performing bulk operations.

## Audit Logging

All batch operations are logged with:

- Action type (CREATE, UPDATE, DELETE)
- User ID and tenant ID
- Timestamp
- Details (sanitized, no PHI in plain text)

Example audit log:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": "user-123",
  "tenant_id": "tenant-456",
  "action": "CREATE",
  "resource_type": "patient",
  "resource_id": "550e8400-e29b-41d4-a716-446655440000",
  "details": {
    "batch_operation": true,
    "batch_position": 0,
    "batch_total": 2
  }
}
```

## Metrics

Prometheus metrics are incremented for each operation:

```
patient_operations_total{action="create", tenant_id="tenant-456"} 2
patient_operations_total{action="update", tenant_id="tenant-456"} 2
patient_operations_total{action="delete", tenant_id="tenant-456"} 2
```

## Cache Invalidation

Batch operations trigger cache invalidation for:

- `patients:list:*` - Patient list cache
- `patients:detail:{id}` - Individual patient cache
- `dashboard:*` - Dashboard statistics cache

## Tenant Isolation

All operations are scoped to the authenticated user's tenant:

- Patient IDs must belong to current tenant
- Results only include patients from current tenant
- Super Admin can access all tenants

## Error Handling

### 401 Unauthorized

Missing or invalid JWT token:

```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found

Patient not found or tenant mismatch:

```json
{
  "detail": "Patient {id} not found"
}
```

### 422 Unprocessable Entity

Validation error in request body:

```json
{
  "detail": [
    {
      "loc": ["body", 0, "first_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 429 Too Many Requests

Rate limit exceeded:

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

### 500 Internal Server Error

Unexpected server error:

```json
{
  "detail": "Internal server error"
}
```

## Best Practices

### Batch Size

- **Recommended**: 10-100 records per batch
- **Maximum**: 500 records per batch (soft limit)
- Larger batches may timeout or consume excessive resources

### Error Recovery

1. Monitor response codes
2. On failure, check validation errors
3. Retry with corrected data
4. Use single-record endpoints for difficult cases

### Performance

- Use batch operations for bulk imports/updates
- Avoid batching when only 1-2 records need changes
- Consider pagination for very large datasets

### Security

- Always use HTTPS in production
- Rotate JWT tokens regularly
- Never log or expose sensitive patient data
- Validate input data before sending

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create multiple patients
patients = [
    {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "phone": "+1234567890",
        "email": "john.doe@example.com"
    },
    {
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1985-05-15",
        "gender": "female",
        "phone": "+1234567891",
        "email": "jane.smith@example.com"
    }
]

response = requests.post(
    f"{BASE_URL}/batch/patients",
    json=patients,
    headers=headers
)

if response.status_code == 201:
    result = response.json()
    print(f"Created {result['created']} patients")
    for patient in result['patients']:
        print(f"  - {patient['first_name']} {patient['last_name']} (ID: {patient['id']})")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

## JavaScript/TypeScript Client Example

```typescript
const BASE_URL = 'http://localhost:8000/api/v1';
const TOKEN = 'your-jwt-token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// Create multiple patients
const patients = [
  {
    first_name: 'John',
    last_name: 'Doe',
    date_of_birth: '1990-01-01',
    gender: 'male',
    phone: '+1234567890',
    email: 'john.doe@example.com'
  },
  {
    first_name: 'Jane',
    last_name: 'Smith',
    date_of_birth: '1985-05-15',
    gender: 'female',
    phone: '+1234567891',
    email: 'jane.smith@example.com'
  }
];

const response = await fetch(`${BASE_URL}/batch/patients`, {
  method: 'POST',
  headers,
  body: JSON.stringify(patients)
});

if (response.ok) {
  const result = await response.json();
  console.log(`Created ${result.created} patients`);
  result.patients.forEach(patient => {
    console.log(`  - ${patient.first_name} ${patient.last_name} (ID: ${patient.id})`);
  });
} else {
  const error = await response.json();
  console.error(`Error: ${response.status} - ${error.detail}`);
}
```

## Testing

Run comprehensive test suite:

```bash
# Backend tests
pytest tests/routers/test_batch.py -v

# Test with coverage
pytest tests/routers/test_batch.py --cov=app.routers.batch --cov-report=term-missing
```

## Monitoring

Monitor batch operations via:

- **Metrics**: Prometheus `/metrics` endpoint
- **Logs**: Structured JSON logs with correlation IDs
- **Audit**: Database audit log table
- **Health**: `/health` and `/ready` endpoints

## Support

For issues or questions:

- Check logs in `logs/app.log`
- Review audit logs in database
- Check Prometheus metrics for operation counts
- Consult main API documentation: `docs/API_REFERENCE.md`
