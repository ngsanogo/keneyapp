# API Best Practices for KeneyApp

## Overview

This guide provides best practices for consuming and implementing the KeneyApp API, ensuring reliability, performance, and security.

## Table of Contents

1. [Authentication](#authentication)
2. [Request Guidelines](#request-guidelines)
3. [Response Handling](#response-handling)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Pagination](#pagination)
7. [Caching](#caching)
8. [Webhooks](#webhooks)
9. [API Versioning](#api-versioning)
10. [Testing](#testing)

## Authentication

### JWT Token Management

#### Obtaining a Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Using the Token

```bash
curl -X GET http://localhost:8000/api/v1/patients/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### Token Best Practices

- Store tokens securely (httpOnly cookies or secure storage)
- Never log tokens or expose them in URLs
- Implement token refresh before expiration
- Handle 401 responses by re-authenticating

```typescript
// Frontend example
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## Request Guidelines

### HTTP Methods

Follow RESTful conventions:

- **GET**: Retrieve resources (idempotent)
- **POST**: Create new resources
- **PUT**: Update entire resource
- **PATCH**: Partial update
- **DELETE**: Remove resource

### Headers

#### Required Headers

```http
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN
```

#### Optional Headers

```http
Accept: application/json
Accept-Language: en-US
User-Agent: KeneyApp-Client/1.0
```

### Request Body

#### Good Example

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "phone": "+1234567890"
}
```

#### Best Practices

- Use camelCase for JavaScript clients, snake_case for Python
- Include only required and modified fields
- Validate data on client side before sending
- Use ISO 8601 format for dates: `YYYY-MM-DD`
- Use ISO 8601 format for timestamps: `YYYY-MM-DDTHH:MM:SSZ`

## Response Handling

### Status Codes

#### Success Codes

- **200 OK**: Request succeeded
- **201 Created**: Resource created successfully
- **204 No Content**: Request succeeded, no content to return

#### Client Error Codes

- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate email)
- **422 Unprocessable Entity**: Validation error

#### Server Error Codes

- **500 Internal Server Error**: Server-side error
- **503 Service Unavailable**: Service temporarily unavailable

### Response Format

#### Success Response

```json
{
  "id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Error Response

```json
{
  "detail": "Email already registered"
}
```

#### Validation Error Response

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

## Error Handling

### Client-Side Error Handling

```typescript
try {
  const response = await api.post('/patients/', patientData);
  console.log('Patient created:', response.data);
} catch (error) {
  if (error.response) {
    // Server responded with error status
    switch (error.response.status) {
      case 400:
        console.error('Invalid data:', error.response.data);
        break;
      case 401:
        console.error('Authentication required');
        // Redirect to login
        break;
      case 403:
        console.error('Insufficient permissions');
        break;
      case 409:
        console.error('Resource conflict:', error.response.data.detail);
        break;
      case 422:
        console.error('Validation errors:', error.response.data.detail);
        break;
      default:
        console.error('Server error:', error.response.data);
    }
  } else if (error.request) {
    // Request made but no response received
    console.error('Network error - no response from server');
  } else {
    // Error setting up request
    console.error('Request error:', error.message);
  }
}
```

### Retry Logic

```typescript
async function apiRequestWithRetry(
  requestFn: () => Promise<any>,
  maxRetries = 3,
  delay = 1000
): Promise<any> {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;

      // Don't retry client errors (4xx)
      if (error.response?.status >= 400 && error.response?.status < 500) {
        throw error;
      }

      // Wait before retrying
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
      }
    }
  }

  throw lastError;
}

// Usage
const patients = await apiRequestWithRetry(() => api.get('/patients/'));
```

## Rate Limiting

### Understanding Rate Limits

KeneyApp implements rate limiting to prevent abuse:

- **Default**: 100 requests per minute per IP
- **Authentication**: 10 requests per minute
- **Create Operations**: 10 requests per minute
- **Read Operations**: 100 requests per minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

### Handling Rate Limits

```typescript
async function makeRequestWithRateLimit(requestFn: () => Promise<any>): Promise<any> {
  try {
    const response = await requestFn();
    return response;
  } catch (error) {
    if (error.response?.status === 429) {
      // Rate limit exceeded
      const resetTime = parseInt(error.response.headers['x-ratelimit-reset']);
      const waitTime = resetTime - Math.floor(Date.now() / 1000);

      console.log(`Rate limit exceeded. Waiting ${waitTime} seconds...`);
      await new Promise(resolve => setTimeout(resolve, waitTime * 1000));

      // Retry request
      return await requestFn();
    }
    throw error;
  }
}
```

### Rate Limit Best Practices

1. **Implement Exponential Backoff**

```typescript
async function exponentialBackoff(
  requestFn: () => Promise<any>,
  maxRetries = 5
): Promise<any> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      if (error.response?.status !== 429 || i === maxRetries - 1) {
        throw error;
      }
      const delay = Math.min(1000 * Math.pow(2, i), 30000);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

2. **Batch Requests**

```typescript
// Bad - Makes 100 separate requests
for (const patientId of patientIds) {
  await api.get(`/patients/${patientId}`);
}

// Good - Use pagination or batch endpoints
const patients = await api.get('/patients/', {
  params: { ids: patientIds.join(',') }
});
```

3. **Cache Results**

```typescript
const cache = new Map();

async function getCachedPatient(patientId: number): Promise<any> {
  if (cache.has(patientId)) {
    return cache.get(patientId);
  }

  const patient = await api.get(`/patients/${patientId}`);
  cache.set(patientId, patient.data);

  // Clear cache after 5 minutes
  setTimeout(() => cache.delete(patientId), 5 * 60 * 1000);

  return patient.data;
}
```

## Pagination

### List Endpoints

All list endpoints support pagination:

```bash
GET /api/v1/patients/?skip=0&limit=100
```

### Pagination Parameters

- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (default: 100, max: 100)

### Example Implementation

```typescript
interface PaginationParams {
  skip?: number;
  limit?: number;
}

async function getAllPatients(): Promise<any[]> {
  const allPatients: any[] = [];
  let skip = 0;
  const limit = 100;

  while (true) {
    const response = await api.get('/patients/', {
      params: { skip, limit }
    });

    const patients = response.data;
    allPatients.push(...patients);

    // If we got fewer than limit, we've reached the end
    if (patients.length < limit) {
      break;
    }

    skip += limit;
  }

  return allPatients;
}
```

### Cursor-Based Pagination (Future Enhancement)

```typescript
// Recommended for large datasets
interface CursorPagination {
  data: any[];
  next_cursor: string | null;
  has_more: boolean;
}

async function getPatientsWithCursor(cursor?: string): Promise<CursorPagination> {
  const response = await api.get('/patients/', {
    params: { cursor, limit: 100 }
  });
  return response.data;
}
```

## Caching

### Client-Side Caching

```typescript
class APICache {
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private ttl: number = 5 * 60 * 1000; // 5 minutes

  get(key: string): any | null {
    const cached = this.cache.get(key);
    if (!cached) return null;

    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  set(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  invalidate(pattern: string): void {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}

const apiCache = new APICache();

// Usage
const cacheKey = '/patients/123';
let patient = apiCache.get(cacheKey);

if (!patient) {
  const response = await api.get('/patients/123');
  patient = response.data;
  apiCache.set(cacheKey, patient);
}
```

### Cache Invalidation

```typescript
// Invalidate cache after updates
async function updatePatient(id: number, data: any): Promise<any> {
  const response = await api.put(`/patients/${id}`, data);

  // Invalidate related caches
  apiCache.invalidate(`/patients/${id}`);
  apiCache.invalidate('/patients/');
  apiCache.invalidate('/dashboard/');

  return response.data;
}
```

## Webhooks

### Future Enhancement: Webhook Support

```typescript
// Register webhook for patient creation
await api.post('/webhooks/', {
  url: 'https://your-app.com/webhook/patient-created',
  events: ['patient.created', 'patient.updated'],
  secret: 'your-webhook-secret'
});

// Verify webhook signature
import crypto from 'crypto';

function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return signature === expectedSignature;
}
```

## API Versioning

### Current Version

- Base URL: `/api/v1/`
- Version: 1.0

### Version Strategy

- URL-based versioning: `/api/v1/`, `/api/v2/`
- Backward compatibility maintained for at least one major version
- Deprecation notices provided 6 months in advance

### Migration Example

```typescript
// Support multiple API versions
const API_VERSION = process.env.API_VERSION || 'v1';

const api = axios.create({
  baseURL: `http://localhost:8000/api/${API_VERSION}/`
});

// Handle version-specific logic
function createPatient(data: any) {
  if (API_VERSION === 'v1') {
    return api.post('/patients/', data);
  } else if (API_VERSION === 'v2') {
    // v2 might have different field names
    return api.post('/patients/', {
      ...data,
      // Map v1 fields to v2 fields if needed
    });
  }
}
```

## Testing

### Unit Testing API Calls

```typescript
// Using Jest and axios-mock-adapter
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { createPatient } from './api';

describe('API Client', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(axios);
  });

  afterEach(() => {
    mock.restore();
  });

  it('should create a patient successfully', async () => {
    const patientData = {
      first_name: 'John',
      last_name: 'Doe',
      email: 'john@example.com'
    };

    mock.onPost('/api/v1/patients/').reply(201, {
      id: 123,
      ...patientData
    });

    const result = await createPatient(patientData);
    expect(result.id).toBe(123);
    expect(result.email).toBe('john@example.com');
  });

  it('should handle validation errors', async () => {
    mock.onPost('/api/v1/patients/').reply(422, {
      detail: [{ loc: ['body', 'email'], msg: 'Invalid email' }]
    });

    await expect(createPatient({})).rejects.toThrow();
  });
});
```

### Integration Testing

```python
# Backend integration tests
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_patient_workflow():
    # 1. Login
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create patient
    response = client.post("/api/v1/patients/", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "date_of_birth": "1990-01-15",
        "gender": "male",
        "phone": "+1234567890"
    }, headers=headers)
    assert response.status_code == 201
    patient_id = response.json()["id"]

    # 3. Get patient
    response = client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"
```

## Performance Tips

1. **Use Compression**

```typescript
import axios from 'axios';
import zlib from 'zlib';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Accept-Encoding': 'gzip, deflate'
  }
});
```

2. **Parallel Requests**

```typescript
// Bad - Sequential
const patient = await api.get('/patients/1');
const appointments = await api.get('/appointments/?patient_id=1');
const prescriptions = await api.get('/prescriptions/?patient_id=1');

// Good - Parallel
const [patient, appointments, prescriptions] = await Promise.all([
  api.get('/patients/1'),
  api.get('/appointments/?patient_id=1'),
  api.get('/prescriptions/?patient_id=1')
]);
```

3. **Request Cancellation**

```typescript
const controller = new AbortController();

// Cancel request after 5 seconds
setTimeout(() => controller.abort(), 5000);

try {
  const response = await api.get('/patients/', {
    signal: controller.signal
  });
} catch (error) {
  if (error.name === 'AbortError') {
    console.log('Request cancelled');
  }
}
```

## Resources

- [API Documentation](http://localhost:8000/api/v1/docs)
- [OpenAPI Schema](http://localhost:8000/api/v1/openapi.json)
- [GraphQL Playground](http://localhost:8000/graphql)
- [Rate Limiting Guide](./RATE_LIMITING.md)
- [Security Best Practices](./SECURITY_BEST_PRACTICES.md)

## Conclusion

Following these best practices will help you build robust, performant, and reliable integrations with the KeneyApp API. Always refer to the official API documentation for the most up-to-date information.
