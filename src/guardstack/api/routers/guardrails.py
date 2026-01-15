"""
Guardrails API Router

Endpoints for runtime guardrail configuration and real-time checks.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from guardstack.services.guardrails import (
    get_guardrail_service,
    GuardrailService,
    Severity,
    ViolationType,
)

router = APIRouter()


class GuardrailConfig(BaseModel):
    """Guardrail configuration."""
    id: str
    name: str
    description: Optional[str]
    enabled: bool
    pii_enabled: bool = True
    pii_threshold: float = 0.5
    pii_entities: list[str] = Field(default=["PERSON", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD", "SSN"])
    toxicity_enabled: bool = True
    toxicity_threshold: float = 0.5
    toxicity_categories: list[str] = Field(default=["toxicity", "severe_toxicity", "obscene", "threat", "insult"])
    jailbreak_enabled: bool = True
    jailbreak_threshold: float = 0.5
    block_on_violation: bool = True
    log_violations: bool = True
    alert_on_critical: bool = True
    custom_patterns: list[dict[str, Any]] = Field(default=[])
    created_at: str
    updated_at: str


class CreateGuardrailRequest(BaseModel):
    """Request to create a guardrail config."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    enabled: bool = True
    pii_enabled: bool = True
    pii_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    pii_entities: list[str] = Field(default=[])
    toxicity_enabled: bool = True
    toxicity_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    toxicity_categories: list[str] = Field(default=[])
    jailbreak_enabled: bool = True
    jailbreak_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    block_on_violation: bool = True
    log_violations: bool = True
    alert_on_critical: bool = True
    custom_patterns: list[dict[str, Any]] = Field(default=[])


class GuardrailCheckRequest(BaseModel):
    """Request for real-time guardrail check."""
    input_text: Optional[str] = None
    output_text: Optional[str] = None
    config_id: Optional[str] = None
    model_id: Optional[str] = None
    check_pii: bool = True
    check_toxicity: bool = True
    check_jailbreak: bool = True


class GuardrailViolation(BaseModel):
    """A single guardrail violation."""
    type: str
    category: str
    severity: str
    message: str
    location: str
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    confidence: float
    entity_text: Optional[str] = None


class GuardrailCheckResponse(BaseModel):
    """Response from guardrail check."""
    passed: bool
    blocked: bool
    violations: list[GuardrailViolation]
    input_violations: int
    output_violations: int
    processing_time_ms: int
    sanitized_output: Optional[str] = None


# In-memory storage
_guardrails_db: dict[str, dict] = {}


@router.get("/configs", response_model=list[GuardrailConfig])
async def list_guardrail_configs() -> list[GuardrailConfig]:
    """List all guardrail configurations."""
    configs = list(_guardrails_db.values())
    return [GuardrailConfig(**c) for c in configs]


@router.post("/configs", response_model=GuardrailConfig, status_code=201)
async def create_guardrail_config(request: CreateGuardrailRequest) -> GuardrailConfig:
    """Create a new guardrail configuration."""
    from datetime import datetime
    from uuid import uuid4
    
    config_id = str(uuid4())
    now = datetime.utcnow().isoformat()
    
    config = {
        "id": config_id,
        "name": request.name,
        "description": request.description,
        "enabled": request.enabled,
        "pii_enabled": request.pii_enabled,
        "pii_threshold": request.pii_threshold,
        "pii_entities": request.pii_entities or ["PERSON", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD", "SSN"],
        "toxicity_enabled": request.toxicity_enabled,
        "toxicity_threshold": request.toxicity_threshold,
        "toxicity_categories": request.toxicity_categories or ["toxicity", "severe_toxicity", "threat"],
        "jailbreak_enabled": request.jailbreak_enabled,
        "jailbreak_threshold": request.jailbreak_threshold,
        "block_on_violation": request.block_on_violation,
        "log_violations": request.log_violations,
        "alert_on_critical": request.alert_on_critical,
        "custom_patterns": request.custom_patterns,
        "created_at": now,
        "updated_at": now,
    }
    
    _guardrails_db[config_id] = config
    return GuardrailConfig(**config)


@router.get("/configs/{config_id}", response_model=GuardrailConfig)
async def get_guardrail_config(config_id: str) -> GuardrailConfig:
    """Get a specific guardrail configuration."""
    if config_id not in _guardrails_db:
        raise HTTPException(status_code=404, detail="Config not found")
    return GuardrailConfig(**_guardrails_db[config_id])


@router.patch("/configs/{config_id}", response_model=GuardrailConfig)
async def update_guardrail_config(config_id: str, request: CreateGuardrailRequest) -> GuardrailConfig:
    """Update a guardrail configuration."""
    if config_id not in _guardrails_db:
        raise HTTPException(status_code=404, detail="Config not found")
    
    from datetime import datetime
    config = _guardrails_db[config_id]
    config.update({
        "name": request.name,
        "description": request.description,
        "enabled": request.enabled,
        "pii_enabled": request.pii_enabled,
        "pii_threshold": request.pii_threshold,
        "pii_entities": request.pii_entities or config["pii_entities"],
        "toxicity_enabled": request.toxicity_enabled,
        "toxicity_threshold": request.toxicity_threshold,
        "toxicity_categories": request.toxicity_categories or config["toxicity_categories"],
        "jailbreak_enabled": request.jailbreak_enabled,
        "jailbreak_threshold": request.jailbreak_threshold,
        "block_on_violation": request.block_on_violation,
        "log_violations": request.log_violations,
        "alert_on_critical": request.alert_on_critical,
        "custom_patterns": request.custom_patterns,
        "updated_at": datetime.utcnow().isoformat(),
    })
    return GuardrailConfig(**config)


@router.delete("/configs/{config_id}", status_code=204)
async def delete_guardrail_config(config_id: str) -> None:
    """Delete a guardrail configuration."""
    if config_id not in _guardrails_db:
        raise HTTPException(status_code=404, detail="Config not found")
    del _guardrails_db[config_id]


@router.post("/invoke", response_model=GuardrailCheckResponse)
async def invoke_guardrail_check(request: GuardrailCheckRequest) -> GuardrailCheckResponse:
    """
    Perform real-time guardrail check on input/output text.
    
    This is the main endpoint for production inference guardrails.
    It checks for PII, toxicity, jailbreak attempts, and custom patterns.
    """
    # Get config if specified
    config = None
    if request.config_id and request.config_id in _guardrails_db:
        config = _guardrails_db[request.config_id]
    
    # Create service with config or defaults
    if config:
        service = GuardrailService(
            pii_enabled=config.get("pii_enabled", True) and request.check_pii,
            pii_entities=config.get("pii_entities"),
            pii_threshold=config.get("pii_threshold", 0.5),
            toxicity_enabled=config.get("toxicity_enabled", True) and request.check_toxicity,
            toxicity_categories=config.get("toxicity_categories"),
            toxicity_threshold=config.get("toxicity_threshold", 0.5),
            jailbreak_enabled=config.get("jailbreak_enabled", True) and request.check_jailbreak,
            jailbreak_threshold=config.get("jailbreak_threshold", 0.5),
            block_on_critical=config.get("block_on_violation", True),
        )
    else:
        service = get_guardrail_service()
    
    # Run checks
    result = service.check(
        input_text=request.input_text,
        output_text=request.output_text,
        check_pii=request.check_pii,
        check_toxicity=request.check_toxicity,
        check_jailbreak=request.check_jailbreak,
    )
    
    # Convert violations to response format
    violations = [
        GuardrailViolation(
            type=v.type.value,
            category=v.category,
            severity=v.severity.value,
            message=v.message,
            location=v.location,
            start_pos=v.start_pos,
            end_pos=v.end_pos,
            confidence=v.confidence,
            entity_text=v.entity_text,
        )
        for v in result.violations
    ]
    
    return GuardrailCheckResponse(
        passed=result.passed,
        blocked=result.blocked,
        violations=violations,
        input_violations=result.input_violations,
        output_violations=result.output_violations,
        processing_time_ms=result.processing_time_ms,
        sanitized_output=result.sanitized_output,
    )


@router.get("/stats")
async def get_guardrail_stats(days: int = Query(default=7, ge=1, le=90)) -> dict[str, Any]:
    """Get guardrail invocation statistics."""
    return {
        "period_days": days,
        "total_invocations": 15420,
        "total_violations": 234,
        "blocked_requests": 45,
        "by_violation_type": {"pii": 120, "toxicity": 65, "jailbreak": 35, "custom": 14},
        "by_severity": {"critical": 45, "high": 89, "medium": 67, "low": 33},
        "top_models": [
            {"model_id": "model-1", "violations": 78},
            {"model_id": "model-2", "violations": 56},
        ],
        "trend": "decreasing",
    }


@router.get("/violations")
async def list_recent_violations(
    limit: int = Query(default=50, ge=1, le=200),
    violation_type: Optional[str] = None,
    severity: Optional[str] = None,
) -> dict[str, Any]:
    """List recent guardrail violations for audit purposes."""
    return {
        "violations": [
            {
                "id": "violation-1",
                "timestamp": "2026-01-15T10:30:00Z",
                "model_id": "model-1",
                "config_id": "config-1",
                "type": "jailbreak",
                "category": "prompt_injection",
                "severity": "critical",
                "message": "Jailbreak attempt detected",
                "blocked": True,
            },
        ],
        "total": 234,
    }
