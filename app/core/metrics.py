"""
Prometheus metrics for monitoring.
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Response

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


def metrics_endpoint():
    """
    Endpoint to expose Prometheus metrics.

    Returns:
        Response with Prometheus metrics
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
