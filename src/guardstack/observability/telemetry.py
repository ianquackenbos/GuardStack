"""
OpenTelemetry Configuration

Distributed tracing and observability for GuardStack.
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.trace import Status, StatusCode

from guardstack.core.config import settings

logger = logging.getLogger(__name__)


def setup_telemetry(
    service_name: str = "guardstack-api",
    otlp_endpoint: Optional[str] = None,
    enable_console: bool = False,
) -> TracerProvider:
    """
    Configure OpenTelemetry for the application.
    
    Args:
        service_name: Name of the service for tracing
        otlp_endpoint: OTLP collector endpoint (e.g., "http://jaeger:4317")
        enable_console: Enable console span exporter for debugging
    
    Returns:
        Configured TracerProvider
    """
    # Create resource with service info
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "service.version": settings.VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })
    
    # Initialize tracer provider
    provider = TracerProvider(resource=resource)
    
    # Add OTLP exporter if endpoint configured
    if otlp_endpoint or settings.OTLP_ENDPOINT:
        endpoint = otlp_endpoint or settings.OTLP_ENDPOINT
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP exporter configured: {endpoint}")
    
    # Add console exporter for debugging
    if enable_console or settings.OTEL_CONSOLE_EXPORT:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("Console span exporter enabled")
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Configure propagator for distributed tracing
    set_global_textmap(B3MultiFormat())
    
    return provider


def instrument_fastapi(app):
    """Instrument FastAPI application."""
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,ready,metrics",
        tracer_provider=trace.get_tracer_provider(),
    )
    logger.info("FastAPI instrumented for tracing")


def instrument_database(engine):
    """Instrument SQLAlchemy for database tracing."""
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        tracer_provider=trace.get_tracer_provider(),
    )
    logger.info("SQLAlchemy instrumented for tracing")


def instrument_redis():
    """Instrument Redis for cache tracing."""
    RedisInstrumentor().instrument(
        tracer_provider=trace.get_tracer_provider(),
    )
    logger.info("Redis instrumented for tracing")


def instrument_httpx():
    """Instrument HTTPX for outbound HTTP tracing."""
    HTTPXClientInstrumentor().instrument(
        tracer_provider=trace.get_tracer_provider(),
    )
    logger.info("HTTPX instrumented for tracing")


def instrument_celery():
    """Instrument Celery for task tracing."""
    CeleryInstrumentor().instrument(
        tracer_provider=trace.get_tracer_provider(),
    )
    logger.info("Celery instrumented for tracing")


def get_tracer(name: str = "guardstack") -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)


class TracingMiddleware:
    """
    Custom middleware for enhanced tracing.
    
    Adds custom attributes and handles errors.
    """
    
    def __init__(self, app):
        self.app = app
        self.tracer = get_tracer("guardstack.middleware")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request info
        path = scope.get("path", "")
        method = scope.get("method", "")
        
        with self.tracer.start_as_current_span(
            f"{method} {path}",
            kind=trace.SpanKind.SERVER,
        ) as span:
            # Add custom attributes
            span.set_attribute("http.route", path)
            span.set_attribute("guardstack.version", settings.VERSION)
            
            # Extract user info from scope if available
            if "user" in scope:
                user = scope["user"]
                span.set_attribute("user.id", getattr(user, "id", "anonymous"))
                span.set_attribute("user.org", getattr(user, "organization_id", ""))
            
            try:
                await self.app(scope, receive, send)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


def trace_evaluation(evaluation_id: str, model_id: str, pillars: list[str]):
    """
    Create a span for evaluation tracking.
    
    Returns a context manager for the evaluation span.
    """
    tracer = get_tracer("guardstack.evaluations")
    
    return tracer.start_as_current_span(
        "evaluation.run",
        attributes={
            "evaluation.id": evaluation_id,
            "model.id": model_id,
            "evaluation.pillars": ",".join(pillars),
            "evaluation.pillar_count": len(pillars),
        },
        kind=trace.SpanKind.INTERNAL,
    )


def trace_pillar(pillar_name: str, model_id: str):
    """Create a span for pillar evaluation."""
    tracer = get_tracer("guardstack.pillars")
    
    return tracer.start_as_current_span(
        f"pillar.{pillar_name}",
        attributes={
            "pillar.name": pillar_name,
            "model.id": model_id,
        },
        kind=trace.SpanKind.INTERNAL,
    )


def trace_connector(connector_type: str, operation: str):
    """Create a span for connector operations."""
    tracer = get_tracer("guardstack.connectors")
    
    return tracer.start_as_current_span(
        f"connector.{operation}",
        attributes={
            "connector.type": connector_type,
            "connector.operation": operation,
        },
        kind=trace.SpanKind.CLIENT,
    )


def trace_guardrail(guardrail_name: str, action: str):
    """Create a span for guardrail enforcement."""
    tracer = get_tracer("guardstack.guardrails")
    
    return tracer.start_as_current_span(
        f"guardrail.{action}",
        attributes={
            "guardrail.name": guardrail_name,
            "guardrail.action": action,
        },
        kind=trace.SpanKind.INTERNAL,
    )


def add_span_attribute(key: str, value) -> None:
    """Add attribute to current span."""
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def record_exception(exception: Exception) -> None:
    """Record exception on current span."""
    span = trace.get_current_span()
    if span:
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


def set_span_status(code: StatusCode, description: str = "") -> None:
    """Set status on current span."""
    span = trace.get_current_span()
    if span:
        span.set_status(Status(code, description))
