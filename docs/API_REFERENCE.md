# API Reference

Complete API reference for KeneyApp.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.keneyapp.com` (example)

## Authentication

Most endpoints require authentication using JWT tokens.

### Getting a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token

Include the token in the Authorization header:

```http
GET /api/v1/patients/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## API Endpoints

### Authentication

#### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "john.doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "role": "doctor"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "username": "john.doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "doctor",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "john.doe",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "username": "john.doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "doctor",
  "is_active": true
}
```

---

### Patients

#### List Patients

```http
GET /api/v1/patients/?skip=0&limit=100
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum records to return (default: 100, max: 1000)
- `search` (optional): Search by name or email

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1985-03-15",
    "email": "jane.smith@example.com",
    "phone": "+1234567890",
    "address": "123 Main St, City, State",
    "created_at": "2024-01-10T08:00:00Z"
  }
]
```

#### Get Patient

```http
GET /api/v1/patients/{patient_id}
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1985-03-15",
  "email": "jane.smith@example.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State",
  "medical_history": "No known allergies",
  "emergency_contact": "John Smith: +1987654321",
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Create Patient

```http
POST /api/v1/patients/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1985-03-15",
  "email": "jane.smith@example.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1985-03-15",
  "email": "jane.smith@example.com",
  "phone": "+1234567890",
  "address": "123 Main St, City, State",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Update Patient

```http
PUT /api/v1/patients/{patient_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "phone": "+1234567899",
  "address": "456 Oak Ave, City, State"
}
```

**Response:** `200 OK`

#### Delete Patient

```http
DELETE /api/v1/patients/{patient_id}
Authorization: Bearer {token}
```

**Response:** `204 No Content`

---

### Appointments

#### List Appointments

```http
GET /api/v1/appointments/?skip=0&limit=100
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum records to return
- `patient_id` (optional): Filter by patient
- `status` (optional): Filter by status (scheduled, completed, cancelled)
- `date_from` (optional): Filter from date (ISO 8601)
- `date_to` (optional): Filter to date (ISO 8601)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "patient_id": 1,
    "doctor_id": 2,
    "appointment_date": "2024-01-20T14:00:00Z",
    "status": "scheduled",
    "reason": "Annual checkup",
    "notes": "Patient is feeling well",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Create Appointment

```http
POST /api/v1/appointments/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "patient_id": 1,
  "doctor_id": 2,
  "appointment_date": "2024-01-20T14:00:00Z",
  "reason": "Annual checkup",
  "notes": "Patient requested morning appointment"
}
```

**Response:** `201 Created`

#### Update Appointment

```http
PUT /api/v1/appointments/{appointment_id}
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "status": "completed",
  "notes": "Checkup completed. Patient healthy."
}
```

**Response:** `200 OK`

---

### Prescriptions

#### List Prescriptions

```http
GET /api/v1/prescriptions/?skip=0&limit=100
Authorization: Bearer {token}
```

**Query Parameters:**
- `skip` (optional): Number of records to skip
- `limit` (optional): Maximum records to return
- `patient_id` (optional): Filter by patient
- `active_only` (optional): Show only active prescriptions

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "patient_id": 1,
    "doctor_id": 2,
    "medication_name": "Amoxicillin",
    "dosage": "500mg",
    "frequency": "3 times daily",
    "duration": "7 days",
    "start_date": "2024-01-15",
    "end_date": "2024-01-22",
    "refills_allowed": 0,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Create Prescription

```http
POST /api/v1/prescriptions/
Authorization: Bearer {token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "patient_id": 1,
  "medication_name": "Amoxicillin",
  "dosage": "500mg",
  "frequency": "3 times daily",
  "duration": "7 days",
  "start_date": "2024-01-15",
  "refills_allowed": 0,
  "instructions": "Take with food"
}
```

**Response:** `201 Created`

---

### Dashboard

#### Get Dashboard Statistics

```http
GET /api/v1/dashboard/stats
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "total_patients": 1250,
  "total_appointments": 3450,
  "total_prescriptions": 2890,
  "appointments_today": 15,
  "appointments_upcoming": 45,
  "active_prescriptions": 780,
  "new_patients_this_month": 32
}
```

---

### OAuth2 / OIDC

#### Initiate OAuth Flow

```http
GET /api/v1/oauth/authorize/{provider}
```

**Path Parameters:**
- `provider`: OAuth provider (`google`, `microsoft`, `okta`)

**Response:** `302 Redirect` to OAuth provider

#### OAuth Callback

```http
GET /api/v1/oauth/callback/{provider}?code={authorization_code}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### FHIR Endpoints

#### Get Patient (FHIR)

```http
GET /api/v1/fhir/Patient/{patient_id}
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "resourceType": "Patient",
  "id": "1",
  "name": [
    {
      "use": "official",
      "family": "Smith",
      "given": ["Jane"]
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "+1234567890",
      "use": "mobile"
    }
  ],
  "birthDate": "1985-03-15"
}
```

#### Get Appointment (FHIR)

```http
GET /api/v1/fhir/Appointment/{appointment_id}
Authorization: Bearer {token}
```

**Response:** `200 OK` (FHIR Appointment resource)

#### Get FHIR Capability Statement

```http
GET /api/v1/fhir/metadata
```

**Response:** `200 OK` (FHIR CapabilityStatement)

---

### GraphQL

#### GraphQL Endpoint

```http
POST /graphql
Authorization: Bearer {token}
Content-Type: application/json
```

**Example Query:**
```graphql
query {
  patients(limit: 10) {
    id
    firstName
    lastName
    email
    appointments {
      id
      appointmentDate
      status
    }
  }
}
```

**Response:** `200 OK`
```json
{
  "data": {
    "patients": [
      {
        "id": 1,
        "firstName": "Jane",
        "lastName": "Smith",
        "email": "jane.smith@example.com",
        "appointments": [
          {
            "id": 1,
            "appointmentDate": "2024-01-20T14:00:00Z",
            "status": "scheduled"
          }
        ]
      }
    ]
  }
}
```

---

## Health & Monitoring

### Health Check

```http
GET /health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "2.0.0"
}
```

### Metrics (Prometheus)

```http
GET /metrics
```

**Response:** Prometheus metrics format

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "ERROR_CODE"
}
```

### Common HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `204 No Content` - Success with no response body
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate email)
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Example Error Response

```json
{
  "detail": "Patient with email jane.smith@example.com already exists",
  "error_code": "DUPLICATE_EMAIL"
}
```

---

## Rate Limiting

- **Rate Limit**: 100 requests per minute per IP address
- **Headers**:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

---

## Pagination

List endpoints support pagination using `skip` and `limit` parameters:

```http
GET /api/v1/patients/?skip=0&limit=50
```

**Response includes:**
```json
{
  "items": [...],
  "total": 1250,
  "skip": 0,
  "limit": 50
}
```

---

## Interactive Documentation

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`

---

## Code Examples

### Python (requests)

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login',
    json={'username': 'john.doe', 'password': 'password'}
)
token = response.json()['access_token']

# Get patients
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/patients/',
    headers=headers
)
patients = response.json()
```

### JavaScript (axios)

```javascript
import axios from 'axios';

// Login
const loginResponse = await axios.post('/api/v1/auth/login', {
  username: 'john.doe',
  password: 'password'
});
const token = loginResponse.data.access_token;

// Get patients
const patientsResponse = await axios.get('/api/v1/patients/', {
  headers: { Authorization: `Bearer ${token}` }
});
const patients = patientsResponse.data;
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john.doe","password":"password"}'

# Get patients
curl -X GET http://localhost:8000/api/v1/patients/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## Additional Resources

- [OpenAPI Specification](http://localhost:8000/api/v1/openapi.json)
- [FHIR Documentation](./FHIR_GUIDE.md)
- [OAuth Guide](./OAUTH_GUIDE.md)
- [Main Documentation](../README.md)
