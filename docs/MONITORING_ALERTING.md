# Monitoring and Alerting Guide

## Overview

This guide describes the monitoring and alerting infrastructure for KeneyApp, including metrics collection, dashboards, alert rules, and incident response procedures.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Application   │────▶│  Prometheus  │────▶│   Grafana   │
│    (Metrics)    │     │  (Collector) │     │ (Dashboard) │
└─────────────────┘     └──────────────┘     └─────────────┘
                               │
                               │
                        ┌──────▼──────┐
                        │   Alert     │
                        │   Manager   │
                        └──────┬──────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
       │   PagerDuty │  │    Slack   │  │    Email   │
       └─────────────┘  └────────────┘  └────────────┘
```

## Metrics Collection

### Application Metrics

KeneyApp exposes metrics at the `/metrics` endpoint in Prometheus format.

**Endpoint**: `http://api.yourdomain.com/metrics`

#### Available Metrics

**HTTP Metrics**

```
# Total requests
http_requests_total{method="GET", endpoint="/api/v1/patients", status="200"}

# Request duration (histogram)
http_request_duration_seconds{method="GET", endpoint="/api/v1/patients"}
http_request_duration_seconds_bucket{le="0.1", method="GET", endpoint="/api/v1/patients"}
http_request_duration_seconds_sum{method="GET", endpoint="/api/v1/patients"}
http_request_duration_seconds_count{method="GET", endpoint="/api/v1/patients"}
```

**Business Metrics**

```
# Patient operations
patient_operations_total{operation="create"}
patient_operations_total{operation="update"}
patient_operations_total{operation="delete"}

# Appointments
appointment_bookings_total{status="scheduled"}
appointment_bookings_total{status="completed"}
appointment_bookings_total{status="cancelled"}

# Prescriptions
prescription_created_total
```

**System Metrics**

```
# Active users
active_users

# Database connections
database_connections{state="idle"}
database_connections{state="active"}
```

### Prometheus Configuration

**Location**: `monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    environment: 'prod'

scrape_configs:
  # KeneyApp Backend
  - job_name: 'keneyapp-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # PostgreSQL Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node Exporter (System metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - '/etc/prometheus/alert-rules.yml'
```

## Grafana Dashboards

### Main Dashboard

**Location**: `monitoring/grafana-dashboard.json`

**Panels:**

1. **API Performance**
   - Request Rate (req/s)
   - Response Time (p50, p95, p99)
   - Error Rate (%)

2. **Database Health**
   - Connection Pool Usage
   - Query Duration
   - Transaction Rate

3. **Redis Cache**
   - Hit Rate
   - Memory Usage
   - Key Count

4. **System Resources**
   - CPU Usage
   - Memory Usage
   - Disk I/O

### Business KPI Dashboard

**Location**: `monitoring/grafana-business-kpi-dashboard.json`

**Panels:**

1. **Patient Management**
   - New Patients Today
   - Total Active Patients
   - Patient Registration Rate

2. **Appointments**
   - Scheduled Today
   - Completion Rate
   - Cancellation Rate
   - Average Duration

3. **Prescriptions**
   - Prescriptions Created Today
   - Total Active Prescriptions
   - Top Medications

4. **User Activity**
   - Active Users
   - Login Rate
   - Failed Login Attempts

### Setting Up Grafana

```bash
# Access Grafana
http://grafana.yourdomain.com
# Default: admin/admin (change on first login)

# Add Prometheus Data Source
1. Configuration → Data Sources → Add data source
2. Select Prometheus
3. URL: http://prometheus:9090
4. Click Save & Test

# Import Dashboards
1. Create → Import
2. Upload JSON files from monitoring/ directory
3. Select Prometheus data source
4. Click Import
```

## Alert Rules

**Location**: `monitoring/alert-rules.yml`

### Critical Alerts

#### API Down

```yaml
- alert: APIDown
  expr: up{job="keneyapp-backend"} == 0
  for: 1m
  labels:
    severity: critical
    service: backend
  annotations:
    summary: "API is down"
    description: "KeneyApp API has been down for more than 1 minute"
    runbook: "https://github.com/ISData-consulting/keneyapp/blob/main/docs/INCIDENT_RESPONSE.md#api-down"
```

#### High Error Rate

```yaml
- alert: HighErrorRate
  expr: |
    rate(http_requests_total{status=~"5.."}[5m]) /
    rate(http_requests_total[5m]) > 0.05
  for: 5m
  labels:
    severity: critical
    service: backend
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
```

#### Database Connection Pool Exhausted

```yaml
- alert: DatabaseConnectionPoolExhausted
  expr: database_connections{state="active"} / database_connections_total > 0.9
  for: 2m
  labels:
    severity: critical
    service: database
  annotations:
    summary: "Database connection pool almost exhausted"
    description: "{{ $value | humanizePercentage }} of connections are in use"
```

### High Priority Alerts

#### High Response Time

```yaml
- alert: HighResponseTime
  expr: |
    histogram_quantile(0.95,
      rate(http_request_duration_seconds_bucket[5m])
    ) > 1.0
  for: 10m
  labels:
    severity: high
    service: backend
  annotations:
    summary: "High response time (p95)"
    description: "95th percentile response time is {{ $value }}s (threshold: 1s)"
```

#### Low Cache Hit Rate

```yaml
- alert: LowCacheHitRate
  expr: |
    rate(redis_keyspace_hits_total[5m]) /
    (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) < 0.7
  for: 15m
  labels:
    severity: high
    service: cache
  annotations:
    summary: "Low Redis cache hit rate"
    description: "Cache hit rate is {{ $value | humanizePercentage }} (threshold: 70%)"
```

#### High Memory Usage

```yaml
- alert: HighMemoryUsage
  expr: |
    (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.85
  for: 5m
  labels:
    severity: high
    service: system
  annotations:
    summary: "High memory usage"
    description: "Memory usage is {{ $value | humanizePercentage }}"
```

### Medium Priority Alerts

#### Failed Login Attempts

```yaml
- alert: HighFailedLoginAttempts
  expr: increase(failed_login_attempts_total[5m]) > 10
  for: 5m
  labels:
    severity: medium
    service: security
  annotations:
    summary: "High number of failed login attempts"
    description: "{{ $value }} failed login attempts in the last 5 minutes"
```

#### Celery Queue Building Up

```yaml
- alert: CeleryQueueBacklog
  expr: celery_queue_length > 100
  for: 10m
  labels:
    severity: medium
    service: celery
  annotations:
    summary: "Celery queue building up"
    description: "Queue length is {{ $value }} (threshold: 100)"
```

## Alert Manager Configuration

**Location**: `/etc/alertmanager/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@isdataconsulting.com'
  smtp_auth_username: 'alerts@isdataconsulting.com'
  smtp_auth_password: '<password>'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default-receiver'

  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true

    # All alerts go to Slack
    - match_re:
        severity: critical|high|medium
      receiver: 'slack-alerts'
      continue: true

    # High and critical alerts go to email
    - match_re:
        severity: critical|high
      receiver: 'email-ops'

receivers:
  - name: 'default-receiver'
    slack_configs:
      - api_url: '<slack-webhook-url>'
        channel: '#keneyapp-alerts'
        title: 'KeneyApp Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '<pagerduty-service-key>'
        description: '{{ .CommonAnnotations.summary }}'

  - name: 'slack-alerts'
    slack_configs:
      - api_url: '<slack-webhook-url>'
        channel: '#keneyapp-alerts'
        title: '{{ .CommonLabels.severity | toUpper }}: {{ .CommonAnnotations.summary }}'
        text: |
          {{ range .Alerts }}
          *Description:* {{ .Annotations.description }}
          *Runbook:* {{ .Annotations.runbook }}
          {{ end }}
        color: '{{ if eq .CommonLabels.severity "critical" }}danger{{ else if eq .CommonLabels.severity "high" }}warning{{ else }}good{{ end }}'

  - name: 'email-ops'
    email_configs:
      - to: 'ops@isdataconsulting.com'
        headers:
          subject: 'KeneyApp Alert: {{ .CommonAnnotations.summary }}'
        html: |
          <h3>{{ .CommonAnnotations.summary }}</h3>
          <p><strong>Severity:</strong> {{ .CommonLabels.severity }}</p>
          {{ range .Alerts }}
          <p>{{ .Annotations.description }}</p>
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'high'
    equal: ['alertname', 'cluster', 'service']
```

## Custom Metrics

### Adding Custom Metrics

**Example: Track custom business event**

```python
# In app/core/metrics.py
from prometheus_client import Counter

custom_metric = Counter(
    'custom_event_total',
    'Total custom events',
    ['event_type', 'status']
)

# Usage in code
from app.core.metrics import custom_metric

def my_function():
    try:
        # ... business logic ...
        custom_metric.labels(event_type='payment', status='success').inc()
    except Exception as e:
        custom_metric.labels(event_type='payment', status='failure').inc()
        raise
```

## Log Aggregation

### Structured Logging

KeneyApp uses structured JSON logging with correlation IDs.

**Example Log Entry:**

```json
{
  "timestamp": "2024-10-31T22:00:00.000Z",
  "level": "INFO",
  "correlation_id": "abc123-def456-789",
  "event": "patient_created",
  "user_id": 123,
  "patient_id": 456,
  "duration_ms": 45.23,
  "message": "Patient created successfully"
}
```

### ELK Stack Integration

```yaml
# Filebeat configuration
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"
      - decode_json_fields:
          fields: ["message"]
          target: ""
          overwrite_keys: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "keneyapp-logs-%{+yyyy.MM.dd}"
```

## Health Checks

### Application Health Check

**Endpoint**: `/health`

**Response:**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  },
  "timestamp": "2024-10-31T22:00:00Z"
}
```

### Liveness and Readiness Probes

**Kubernetes Configuration:**

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 3
```

## Monitoring Best Practices

### 1. Define SLIs and SLOs

**Service Level Indicators (SLIs):**

- Availability: % of successful requests
- Latency: Response time (p50, p95, p99)
- Error rate: % of failed requests

**Service Level Objectives (SLOs):**

- Availability: 99.9% uptime
- Latency: p95 < 500ms, p99 < 1000ms
- Error rate: < 1%

### 2. Alert on Symptoms, Not Causes

✅ Good: "API response time > 1s"
❌ Bad: "CPU usage > 80%"

### 3. Reduce Alert Fatigue

- Set appropriate thresholds
- Use alert grouping
- Implement alert inhibition
- Regular alert review

### 4. Runbooks for Alerts

Every alert should have:

- Clear description
- Impact assessment
- Troubleshooting steps
- Escalation procedure
- Link to runbook

### 5. Regular Review

- Weekly: Review alert history
- Monthly: Update thresholds
- Quarterly: Review SLOs
- Annually: Architecture review

## Incident Response Integration

When an alert fires:

1. **Alert Triggered** → PagerDuty/Slack notification
2. **On-call Acknowledges** → Within 15 minutes
3. **Initial Assessment** → Follow runbook
4. **Escalate if Needed** → To technical lead
5. **Resolve and Document** → Post-mortem within 24h

See [INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md) for detailed procedures.

## Dashboard Access

### Production

- Grafana: <https://grafana.keneyapp.com>
- Prometheus: <https://prometheus.keneyapp.com> (Internal only)
- Alert Manager: <https://alerts.keneyapp.com> (Internal only)

### Staging

- Grafana: <https://grafana.staging.keneyapp.com>
- Prometheus: <https://prometheus.staging.keneyapp.com>

## Useful Queries

### PromQL Examples

**Request rate (per second):**

```promql
rate(http_requests_total[5m])
```

**Error rate (percentage):**

```promql
rate(http_requests_total{status=~"5.."}[5m]) /
rate(http_requests_total[5m]) * 100
```

**Response time p95:**

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Active database connections:**

```promql
database_connections{state="active"}
```

**Cache hit rate:**

```promql
rate(redis_keyspace_hits_total[5m]) /
(rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) * 100
```

## Support

For monitoring questions:

- Slack: #monitoring
- Email: <devops@isdataconsulting.com>

---

**Document Version**: 1.0.0
**Last Updated**: 2024-10-31
**Review**: Quarterly
