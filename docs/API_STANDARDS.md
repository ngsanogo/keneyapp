# API Response Standards

## Standard Response Formats

All API endpoints follow consistent response patterns for predictability and ease of integration.

### Success Response (2xx)

```json
{
  "id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "created_at": "2025-12-08T10:30:00Z",
  "updated_at": "2025-12-08T10:30:00Z"
}
```

### Paginated Response

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

### Error Response (4xx/5xx)

```json
{
  "detail": "Resource not found",
  "status_code": 404,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### FHIR OperationOutcome (for FHIR endpoints)

```json
{
  "resourceType": "OperationOutcome",
  "issue": [{
    "severity": "error",
    "code": "not-found",
    "diagnostics": "Patient resource not found"
  }]
}
```

## Common Headers

### Request Headers

- `Authorization: Bearer <token>` - Required for authenticated endpoints
- `X-Correlation-ID: <uuid>` - Optional, for request tracing
- `Content-Type: application/json` - For POST/PUT/PATCH requests
- `Accept: application/json` - For JSON responses

### Response Headers

- `X-Correlation-ID` - Request correlation ID for tracing
- `X-RateLimit-Limit` - Rate limit ceiling
- `X-RateLimit-Remaining` - Remaining requests in window
- `X-RateLimit-Reset` - Time when rate limit resets
- `Cache-Control` - Caching directives
- `Content-Encoding: gzip` - Compression (for responses > 1KB)

## Rate Limiting

Default rate limits by endpoint type:

- **Authentication**: 5 requests/minute
- **Read operations**: 100 requests/minute
- **Write operations**: 10 requests/minute
- **Bulk operations**: 5 requests/minute

Rate limit headers included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702034400
```

## Filtering and Sorting

### Query Parameters

- `skip`: Number of records to skip (pagination offset)
- `limit`: Maximum records to return (max: 100)
- `sort_by`: Field name to sort by
- `sort_order`: `asc` or `desc`
- `search`: Full-text search term
- `date_from`: Filter by creation date (ISO 8601)
- `date_to`: Filter by creation date (ISO 8601)

Example:
```
GET /api/v1/patients?skip=0&limit=20&sort_by=last_name&sort_order=asc&search=john
```

## Caching

- **List endpoints**: Cached for 120 seconds
- **Detail endpoints**: Cached for 300 seconds
- **Cache invalidation**: Automatic on mutations

Cache headers:
```
Cache-Control: public, max-age=120
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

## Performance Optimizations

1. **Response Compression**: GZip compression for responses > 1KB
2. **Eager Loading**: Related entities loaded efficiently (no N+1 queries)
3. **Database Indexes**: All foreign keys and frequently queried fields indexed
4. **Connection Pooling**: Managed by SQLAlchemy
5. **Multi-level Caching**: Memory + Redis caching

## Security

- All PHI (Protected Health Information) encrypted at rest
- JWT tokens expire after 24 hours
- RBAC enforced on all endpoints
- Audit logging for all data access
- Rate limiting to prevent abuse
- CORS configured for allowed origins only
- Security headers on all responses

## Example Workflows

### Create Patient

```bash
POST /api/v1/patients
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1985-03-15",
  "gender": "female",
  "email": "jane.smith@example.com",
  "phone": "+1234567890"
}
```

Response:
```json
{
  "id": 456,
  "first_name": "Jane",
  "last_name": "Smith",
  "date_of_birth": "1985-03-15",
  "gender": "female",
  "email": "jane.smith@example.com",
  "phone": "+1234567890",
  "created_at": "2025-12-08T11:00:00Z",
  "tenant_id": 1
}
```

### Search Patients

```bash
GET /api/v1/patients/search?query=jane&skip=0&limit=10
Authorization: Bearer <token>
```

Response:
```json
{
  "items": [
    {
      "id": 456,
      "first_name": "Jane",
      "last_name": "Smith",
      ...
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

## Monitoring & Observability

- **Metrics**: Prometheus metrics at `/metrics`
- **Health Check**: `/health` for basic status
- **Readiness Check**: `/ready` for dependency status
- **Tracing**: OpenTelemetry for distributed tracing
- **Logging**: Structured JSON logs with correlation IDs

## Error Handling

HTTP Status Codes:
- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource doesn't exist
- `409 Conflict`: Duplicate resource
- `413 Content Too Large`: Request body too large
- `422 Unprocessable Content`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Dependencies unavailable
