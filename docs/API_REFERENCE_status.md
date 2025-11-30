# Status Endpoint

- Path: `/api/v1/status`
- Method: `GET`
- Auth: Requires authenticated user (JWT)
- Rate Limit: `100/minute`
- Metrics: Increments `app_status_checks_total{tenant_id=...}`
- Audit: Logs `read` action on `status`

## Response

```json
{
  "version": "<app version>",
  "environment": "<env>",
  "uptime_seconds": "<seconds>"
}
```

## Frontend Page

- Route: `/status`
- Displays version, environment, and uptime for authenticated users.
