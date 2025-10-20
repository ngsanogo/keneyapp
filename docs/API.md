# KeneyApp API Documentation

## Overview

KeneyApp is a comprehensive healthcare data management platform that provides secure APIs for managing patients, appointments, prescriptions, and user authentication.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.keneyapp.com`

## Authentication

All API endpoints (except authentication and health checks) require JWT token authentication.

### Getting an Access Token

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## API Endpoints

### Health Checks

#### Basic Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "keneyapp-backend",
  "version": "1.0.0"
}
```

#### Detailed Health Check
```http
GET /health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "keneyapp-backend",
  "version": "1.0.0",
  "database": "connected",
  "environment": "production"
}
```

### Authentication

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

#### Get Current User
```http
GET /api/users/me
Authorization: Bearer <token>
```

### Patients

#### List Patients
```http
GET /api/patients?skip=0&limit=100
Authorization: Bearer <token>
```

#### Get Patient by ID
```http
GET /api/patients/{patient_id}
Authorization: Bearer <token>
```

#### Create Patient
```http
POST /api/patients
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "address": "123 Main St",
  "city": "Anytown",
  "state": "CA",
  "zip_code": "12345",
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "+1234567891",
  "medical_history": "No known allergies",
  "allergies": "None"
}
```

#### Update Patient
```http
PUT /api/patients/{patient_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "phone": "+1122334455",
  "address": "456 Oak Ave"
}
```

#### Delete Patient
```http
DELETE /api/patients/{patient_id}
Authorization: Bearer <token>
```

### Appointments

#### List Appointments
```http
GET /api/appointments?skip=0&limit=100
Authorization: Bearer <token>
```

#### Get Appointment by ID
```http
GET /api/appointments/{appointment_id}
Authorization: Bearer <token>
```

#### Create Appointment
```http
POST /api/appointments
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_id": 1,
  "doctor_id": 1,
  "appointment_date": "2024-01-20T10:00:00Z",
  "duration_minutes": 30,
  "status": "scheduled",
  "notes": "Regular checkup"
}
```

#### Update Appointment Status
```http
PUT /api/appointments/{appointment_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "confirmed",
  "notes": "Appointment confirmed"
}
```

### Users

#### List Users
```http
GET /api/users?skip=0&limit=100
Authorization: Bearer <token>
```

#### Get User by ID
```http
GET /api/users/{user_id}
Authorization: Bearer <token>
```

#### Create User
```http
POST /api/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "doctor@example.com",
  "username": "doctor1",
  "password": "securepassword",
  "full_name": "Dr. Jane Smith",
  "role": "doctor"
}
```

## Data Models

### Patient
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "address": "123 Main St",
  "city": "Anytown",
  "state": "CA",
  "zip_code": "12345",
  "emergency_contact_name": "Jane Doe",
  "emergency_contact_phone": "+1234567891",
  "medical_history": "No known allergies",
  "allergies": "None",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Appointment
```json
{
  "id": 1,
  "patient_id": 1,
  "doctor_id": 1,
  "appointment_date": "2024-01-20T10:00:00Z",
  "duration_minutes": 30,
  "status": "scheduled",
  "notes": "Regular checkup",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### User
```json
{
  "id": 1,
  "email": "admin@keneyapp.com",
  "username": "admin",
  "full_name": "System Administrator",
  "role": "admin",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- **API Endpoints**: 10 requests per second
- **Authentication**: 5 requests per second
- **Burst**: 20 requests (API), 10 requests (Auth)

## Security

- All API endpoints use HTTPS in production
- JWT tokens expire after 30 minutes (configurable)
- Passwords are hashed using bcrypt
- CORS is configured for allowed origins
- Rate limiting prevents abuse
- Security headers are included in responses

## SDKs and Examples

### Python Example
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = response.json()["access_token"]

# Get patients
headers = {"Authorization": f"Bearer {token}"}
patients = requests.get(
    "http://localhost:8000/api/patients",
    headers=headers
).json()
```

### JavaScript Example
```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'username=admin&password=admin123'
});
const { access_token } = await loginResponse.json();

// Get patients
const patientsResponse = await fetch('http://localhost:8000/api/patients', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const patients = await patientsResponse.json();
```

### cURL Examples
```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Get patients
curl -X GET "http://localhost:8000/api/patients" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Interactive Documentation

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`
