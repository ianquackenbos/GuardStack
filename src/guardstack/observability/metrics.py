"""
OpenTelemetry Metrics

Custom metrics for GuardStack monitoring.
"""

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from guardstack.core.config import settings


def setup_metrics(
    service_name: str = "guardstack-api",
    otlp_endpoint: str | None = None,
) -> MeterProvider:
    """
    Configure OpenTelemetry metrics.
    
    Args:
        service_name: Name of the service
        otlp_endpoint: OTLP collector endpoint
    
    Returns:
        Configured MeterProvider
    """
    resource = Resource.create({
        SERVICE_NAME: service_name,
        "service.version": settings.VERSION,
    })
    
    readers = []
    
    # Add OTLP exporter
    if otlp_endpoint or settings.OTLP_ENDPOINT:
        endpoint = otlp_endpoint or settings.OTLP_ENDPOINT
        otlp_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
        readers.append(PeriodicExportingMetricReader(otlp_exporter))
    
    # Add console exporter for debugging
    if settings.OTEL_CONSOLE_EXPORT:
        console_exporter = ConsoleMetricExporter()
        readers.append(PeriodicExportingMetricReader(console_exporter))
    
    provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(provider)
    
    return provider


def get_meter(name: str = "guardstack") -> metrics.Meter:
    """Get a meter instance."""
    return metrics.get_meter(name)


# GuardStack custom metrics
class GuardStackMetrics:
    """Custom metrics for GuardStack."""
    
    def __init__(self):
        self.meter = get_meter("guardstack.metrics")
        
        # Evaluation metrics
        self.evaluations_total = self.meter.create_counter(
            "guardstack_evaluations_total",
            description="Total number of evaluations",
            unit="1",
        )
        
        self.evaluations_duration = self.meter.create_histogram(
            "guardstack_evaluation_duration_seconds",
            description="Evaluation duration in seconds",
            unit="s",
        )
        
        self.evaluation_scores = self.meter.create_histogram(
            "guardstack_evaluation_scores",
            description="Evaluation scores distribution",
            unit="1",
        )
        
        # Model metrics
        self.models_registered = self.meter.create_up_down_counter(
            "guardstack_models_registered",
            description="Number of registered models",
            unit="1",
        )
        
        self.model_invocations = self.meter.create_counter(
            "guardstack_model_invocations_total",
            description="Total model invocations",
            unit="1",
        )
        
        # Guardrail metrics
        self.guardrail_checks = self.meter.create_counter(
            "guardstack_guardrail_checks_total",
            description="Total guardrail checks",
            unit="1",
        )
        
        self.guardrail_blocks = self.meter.create_counter(
            "guardstack_guardrail_blocks_total",
            description="Total guardrail blocks",
            unit="1",
        )
        
        self.guardrail_latency = self.meter.create_histogram(
            "guardstack_guardrail_latency_ms",
            description="Guardrail check latency in milliseconds",
            unit="ms",
        )
        
        # Connector metrics
        self.connector_requests = self.meter.create_counter(
            "guardstack_connector_requests_total",
            description="Total connector requests",
            unit="1",
        )
        
        self.connector_errors = self.meter.create_counter(
            "guardstack_connector_errors_total",
            description="Total connector errors",
            unit="1",
        )
        
        self.connector_latency = self.meter.create_histogram(
            "guardstack_connector_latency_ms",
            description="Connector request latency in milliseconds",
            unit="ms",
        )
        
        # Finding metrics
        self.findings_detected = self.meter.create_counter(
            "guardstack_findings_detected_total",
            description="Total findings detected",
            unit="1",
        )
        
        self.findings_by_severity = self.meter.create_counter(
            "guardstack_findings_by_severity",
            description="Findings by severity level",
            unit="1",
        )
    
    def record_evaluation_complete(
        self,
        model_id: str,
        pillars: list[str],
        duration_seconds: float,
        overall_score: float,
    ):
        """Record completed evaluation."""
        attributes = {"model_id": model_id, "pillar_count": len(pillars)}
        
        self.evaluations_total.add(1, attributes)
        self.evaluations_duration.record(duration_seconds, attributes)
        self.evaluation_scores.record(overall_score, attributes)
    
    def record_model_invocation(
        self,
        model_id: str,
        connector_type: str,
        success: bool,
    ):
        """Record model invocation."""
        self.model_invocations.add(1, {
            "model_id": model_id,
            "connector_type": connector_type,
            "success": str(success),
        })
    
    def record_guardrail_check(
        self,
        guardrail_name: str,
        action: str,
        blocked: bool,
        latency_ms: float,
    ):
        """Record guardrail check."""
        attributes = {"guardrail": guardrail_name, "action": action}
        
        self.guardrail_checks.add(1, attributes)
        self.guardrail_latency.record(latency_ms, attributes)
        
        if blocked:
            self.guardrail_blocks.add(1, attributes)
    
    def record_connector_request(
        self,
        connector_type: str,
        operation: str,
        success: bool,
        latency_ms: float,
    ):
        """Record connector request."""
        attributes = {"connector_type": connector_type, "operation": operation}
        
        self.connector_requests.add(1, attributes)
        self.connector_latency.record(latency_ms, attributes)
        
        if not success:
            self.connector_errors.add(1, attributes)
    
    def record_finding(self, severity: str, pillar: str, model_id: str):
        """Record detected finding."""
        self.findings_detected.add(1, {
            "pillar": pillar,
            "model_id": model_id,
        })
        
        self.findings_by_severity.add(1, {
            "severity": severity,
            "pillar": pillar,
        })


# Global metrics instance
_metrics: GuardStackMetrics | None = None


def get_metrics() -> GuardStackMetrics:
    """Get global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = GuardStackMetrics()
    return _metrics
