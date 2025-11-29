"""OpenTelemetry distributed tracing configuration.

This module provides distributed tracing capabilities for observability.
Traces can be exported to OTLP collectors (e.g., Jaeger, Tempo) or console.
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings

logger = logging.getLogger(__name__)

_tracer_provider: Optional[TracerProvider] = None


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing with configured exporters.

    Configuration is controlled via environment variables:
    - OTEL_ENABLED: Enable/disable tracing (default: false)
    - OTEL_EXPORTER_TYPE: Exporter type - "otlp", "jaeger", or "console" (default: "console")
    - OTEL_EXPORTER_ENDPOINT: OTLP/Jaeger collector endpoint
    - OTEL_SERVICE_NAME: Service name for traces (default: "keneyapp")
    - OTEL_SERVICE_VERSION: Service version (default: "1.0.0")
    """
    global _tracer_provider

    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry tracing is disabled")
        return

    # Create resource with service metadata
    resource = Resource.create(
        {
            SERVICE_NAME: settings.OTEL_SERVICE_NAME,
            SERVICE_VERSION: settings.OTEL_SERVICE_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )

    # Initialize tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Configure span exporter based on type
    exporter_type = settings.OTEL_EXPORTER_TYPE.lower()

    if exporter_type == "otlp":
        if not settings.OTEL_EXPORTER_ENDPOINT:
            logger.warning(
                "OTLP exporter selected but OTEL_EXPORTER_ENDPOINT not set, "
                "falling back to console exporter"
            )
            exporter = ConsoleSpanExporter()
        else:
            logger.info(
                f"Configuring OTLP exporter to {settings.OTEL_EXPORTER_ENDPOINT}"
            )
            exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)

    elif exporter_type == "jaeger":
        if not settings.OTEL_EXPORTER_ENDPOINT:
            logger.warning(
                "Jaeger exporter selected but OTEL_EXPORTER_ENDPOINT not set, "
                "falling back to console exporter"
            )
            exporter = ConsoleSpanExporter()
        else:
            # Parse Jaeger endpoint (expects format: host:port)
            try:
                agent_host, agent_port_str = settings.OTEL_EXPORTER_ENDPOINT.split(":")
                agent_port = int(agent_port_str)
                logger.info(f"Configuring Jaeger exporter to {agent_host}:{agent_port}")
                exporter = JaegerExporter(
                    agent_host_name=agent_host,
                    agent_port=agent_port,
                )
            except (ValueError, AttributeError) as e:
                logger.error(
                    f"Invalid Jaeger endpoint format: {settings.OTEL_EXPORTER_ENDPOINT}. "
                    f"Expected 'host:port'. Error: {e}. Falling back to console exporter."
                )
                exporter = ConsoleSpanExporter()

    else:  # console or unknown
        if exporter_type != "console":
            logger.warning(
                f"Unknown OTEL_EXPORTER_TYPE '{exporter_type}', using console exporter"
            )
        logger.info("Configuring console exporter for traces")
        exporter = ConsoleSpanExporter()

    # Add batch span processor
    _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))

    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    logger.info(
        f"OpenTelemetry tracing initialized "
        f"(service={settings.OTEL_SERVICE_NAME}, "
        f"exporter={exporter_type})"
    )


def instrument_app(app) -> None:
    """Instrument FastAPI application and dependencies with OpenTelemetry.

    Args:
        app: FastAPI application instance to instrument
    """
    if not settings.OTEL_ENABLED:
        return

    logger.info("Instrumenting FastAPI application with OpenTelemetry")

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Instrument SQLAlchemy (database queries)
    try:
        from app.core.database import engine

        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("Instrumented SQLAlchemy engine")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")

    # Instrument Redis (cache operations)
    try:
        RedisInstrumentor().instrument()
        logger.info("Instrumented Redis client")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")


def get_tracer(name: str = __name__):
    """Get a tracer instance for manual span creation.

    Args:
        name: Tracer name, typically __name__ of the calling module

    Returns:
        Tracer instance for creating spans

    Example:
        >>> from app.core.tracing import get_tracer
        >>> tracer = get_tracer(__name__)
        >>> with tracer.start_as_current_span("my-operation"):
        ...     # Your code here
        ...     pass
    """
    return trace.get_tracer(name)


def shutdown_tracing() -> None:
    """Gracefully shutdown tracing and flush pending spans."""
    global _tracer_provider

    if _tracer_provider is not None:
        logger.info("Shutting down OpenTelemetry tracing")
        _tracer_provider.shutdown()
        _tracer_provider = None
