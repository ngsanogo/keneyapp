"""
Prometheus metrics for monitoring.
"""

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Request counters
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

# Response time histogram
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Healthcare-specific metrics
patient_operations_total = Counter(
    "patient_operations_total", "Total patient operations", ["operation"]
)

appointment_bookings_total = Counter(
    "appointment_bookings_total", "Total appointment bookings", ["status"]
)

prescription_created_total = Counter(
    "prescription_created_total", "Total prescriptions created"
)

active_users = Gauge("active_users", "Number of currently active users")

database_connections = Gauge(
    "database_connections", "Number of active database connections"
)

# Business KPI Metrics
daily_active_patients = Gauge(
    "daily_active_patients", "Number of unique patients with activity today"
)

appointment_completion_rate = Gauge(
    "appointment_completion_rate",
    "Percentage of appointments completed vs scheduled",
    ["time_period"],  # day, week, month
)

prescription_fulfillment_rate = Gauge(
    "prescription_fulfillment_rate",
    "Percentage of prescriptions fulfilled",
    ["time_period"],
)

patient_satisfaction_score = Gauge(
    "patient_satisfaction_score", "Average patient satisfaction score (0-10)"
)

appointment_no_show_rate = Gauge(
    "appointment_no_show_rate",
    "Percentage of appointments with no-show status",
    ["time_period"],
)

average_wait_time_minutes = Histogram(
    "average_wait_time_minutes",
    "Average patient wait time in minutes",
    buckets=[5, 10, 15, 30, 45, 60, 90, 120],
)

appointments_by_status = Gauge(
    "appointments_by_status",
    "Number of appointments by status",
    ["status"],  # scheduled, completed, cancelled, no_show
)

prescriptions_by_status = Gauge(
    "prescriptions_by_status",
    "Number of prescriptions by status",
    ["status"],  # active, completed, cancelled
)

patients_by_risk_level = Gauge(
    "patients_by_risk_level",
    "Number of patients by risk level",
    ["risk_level"],  # low, medium, high
)

# System Health Metrics
api_error_rate = Gauge(
    "api_error_rate",
    "Percentage of API requests resulting in errors",
    ["error_type"],  # 4xx, 5xx
)

authentication_failures_total = Counter(
    "authentication_failures_total",
    "Total failed authentication attempts",
    ["reason"],  # invalid_credentials, mfa_failed, account_locked
)

unauthorized_access_attempts = Counter(
    "unauthorized_access_attempts",
    "Total unauthorized access attempts",
    ["resource_type"],
)

# Compliance Metrics
audit_log_entries_total = Counter(
    "audit_log_entries_total",
    "Total audit log entries created",
    ["action_type"],  # create, read, update, delete
)

data_export_requests_total = Counter(
    "data_export_requests_total",
    "Total GDPR data export requests",
    ["status"],  # success, failed
)

encryption_operations_total = Counter(
    "encryption_operations_total",
    "Total encryption/decryption operations",
    ["operation"],  # encrypt, decrypt
)

# App Status
app_status_checks_total = Counter(
    "app_status_checks_total",
    "Total app status checks",
    ["tenant_id"],
)


def metrics_endpoint() -> Response:
    """
    Endpoint to expose Prometheus metrics.

    Returns:
        Response with Prometheus metrics
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
