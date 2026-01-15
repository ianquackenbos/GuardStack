"""
GuardStack Observability Module

OpenTelemetry tracing, metrics, and logging.
"""

from guardstack.observability.telemetry import (
    setup_telemetry,
    instrument_fastapi,
    instrument_database,
    instrument_redis,
    instrument_httpx,
    instrument_celery,
    get_tracer,
    TracingMiddleware,
    trace_evaluation,
    trace_pillar,
    trace_connector,
    trace_guardrail,
    add_span_attribute,
    record_exception,
    set_span_status,
)

from guardstack.observability.metrics import (
    setup_metrics,
    get_meter,
    get_metrics,
    GuardStackMetrics,
)

__all__ = [
    # Telemetry
    "setup_telemetry",
    "instrument_fastapi",
    "instrument_database",
    "instrument_redis",
    "instrument_httpx",
    "instrument_celery",
    "get_tracer",
    "TracingMiddleware",
    "trace_evaluation",
    "trace_pillar",
    "trace_connector",
    "trace_guardrail",
    "add_span_attribute",
    "record_exception",
    "set_span_status",
    # Metrics
    "setup_metrics",
    "get_meter",
    "get_metrics",
    "GuardStackMetrics",
]
