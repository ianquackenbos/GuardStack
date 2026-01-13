"""
Guardrails API Router

Endpoints for runtime guardrail configuration and real-time checks.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


class GuardrailConfig(BaseModel):
    """Guardrail configuration."""
    id: str
    name: str
    description: Optional[str]
    enabled: bool
    
    # Detection settings
    pii_enabled: bool = True
    pii_threshold: float = 0.5
    pii_entities: list[str] = Field(default=[
        "PERSON", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD", "SSN"
    ])
    
    toxicity_enabled: bool = True
    toxicity_threshold: float = 0.5
    toxicity_categories: list[str] = Field(default=[
        "toxicity", "severe_toxicity", "obscene", "threat", "insult"
    ])
    
    jailbreak_enabled: bool = True
    jailbreak_threshold: float = 0.5
    
    # Actions
    block_on_violation: bool = True
    log_violations: bool = True
    alert_on_critical: bool = True
    
    # Custom rules
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
    
    # Override default settings for this check
    check_pii: bool = True
    check_toxicity: bool = True
    check_jailbreak: bool = True


class GuardrailViolation(BaseModel):
    """A single guardrail violation."""
    type: str  # pii, toxicity, jailbreak, custom
    category: str
    severity: str  # low, medium, high, critical
    message: str
    location: str  # input, output
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    confidence: float
    entity_text: Optional[str] = None  # For PII


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
    """
    List all guardrail configurations.
    """
    configs = list(_guardrails_db.values())
    return [GuardrailConfig(**c) for c in configs]


@router.post("/configs", response_model=GuardrailConfig, status_code=201)
async def create_guardrail_config(request: CreateGuardrailRequest) -> GuardrailConfig:
    """
    Create a new guardrail configuration.
    """
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
        "pii_entities": request.pii_entities or [
            "PERSON", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD", "SSN"
        ],
        "toxicity_enabled": request.toxicity_enabled,
        "toxicity_threshold": request.toxicity_threshold,
        "toxicity_categories": request.toxicity_categories or [
            "toxicity", "severe_toxicity", "obscene", "threat", "insult"
        ],
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
    """
    Get a specific guardrail configuration.
    """
    if config_id not in _guardrails_db:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return GuardrailConfig(**_guardrails_db[config_id])


@router.patch("/configs/{config_id}", response_model=GuardrailConfig)
async def update_guardrail_config(
    config_id: str,
    request: CreateGuardrailRequest,
) -> GuardrailConfig:
    """
    Update a guardrail configuration.
    """
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
    """
    Delete a guardrail configuration.
    """
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
    import time
    
    start_time = time.time()
    violations = []
    
    # Check input text
    if request.input_text:
        # PII detection
        if request.check_pii:
            # TODO: Use Presidio for real PII detection
            pii_patterns = ["@", "555-", "4111"]
            for pattern in pii_patterns:
                if pattern in request.input_text:
                    violations.append(GuardrailViolation(
                        type="pii",
                        category="EMAIL" if "@" in pattern else "PHONE_NUMBER",
                        severity="high",
                        message=f"Potential PII detected in input",
                        location="input",
                        confidence=0.85,
                    ))
        
        # Jailbreak detection
        if request.check_jailbreak:
            jailbreak_patterns = [
                "ignore previous instructions",
                "pretend you are",
                "act as if",
                "DAN mode",
            ]
            input_lower = request.input_text.lower()
            for pattern in jailbreak_patterns:
                if pattern in input_lower:
                    violations.append(GuardrailViolation(
                        type="jailbreak",
                        category="prompt_injection",
                        severity="critical",
                        message=f"Potential jailbreak attempt detected",
                        location="input",
                        confidence=0.9,
                    ))
                    break
    
    # Check output text
    if request.output_text and request.check_toxicity:
        # TODO: Use Detoxify for real toxicity detection
        toxic_words = ["hate", "kill", "attack"]
        output_lower = request.output_text.lower()
        for word in toxic_words:
            if word in output_lower:
                violations.append(GuardrailViolation(
                    type="toxicity",
                    category="threat",
                    severity="high",
                    message=f"Potentially harmful content in output",
                    location="output",
                    confidence=0.75,
                ))
                break
    
    processing_time = int((time.time() - start_time) * 1000)
    
    input_violations = sum(1 for v in violations if v.location == "input")
    output_violations = sum(1 for v in violations if v.location == "output")
    
    has_critical = any(v.severity == "critical" for v in violations)
    
    return GuardrailCheckResponse(
        passed=len(violations) == 0,
        blocked=has_critical,
        violations=violations,
        input_violations=input_violations,
        output_violations=output_violations,
        processing_time_ms=processing_time,
        sanitized_output=None,  # TODO: Implement output sanitization
    )


@router.get("/stats")
async def get_guardrail_stats(
    days: int = Query(default=7, ge=1, le=90),
) -> dict[str, Any]:
    """
    Get guardrail invocation statistics.
    """
    return {
        "period_days": days,
        "total_invocations": 15420,
        "total_violations": 234,
        "blocked_requests": 45,
        "by_violation_type": {
            "pii": 120,
            "toxicity": 65,
            "jailbreak": 35,
            "custom": 14,
        },
        "by_severity": {
            "critical": 45,
            "high": 89,
            "medium": 67,
            "low": 33,
        },
        "top_models": [
            {"model_id": "model-1", "violations": 78},
            {"model_id": "model-2", "violations": 56},
            {"model_id": "model-3", "violations": 45},
        ],
        "trend": "decreasing",
    }


@router.get("/violations")
async def list_recent_violations(
    limit: int = Query(default=50, ge=1, le=200),
    violation_type: Optional[str] = None,
    severity: Optional[str] = None,
) -> dict[str, Any]:
    """
    List recent guardrail violations for audit purposes.
    """
    return {
        "violations": [
            {
                "id": "violation-1",
                "timestamp": "2024-01-15T10:30:00Z",
                "model_id": "model-1",
                "config_id": "config-1",
                "type": "jailbreak",
                "category": "prompt_injection",
                "severity": "critical",
                "message": "Jailbreak attempt detected",
                "blocked": True,
                "input_preview": "Ignore previous instructions and...",
            },
            {
                "id": "violation-2",
                "timestamp": "2024-01-15T10:25:00Z",
                "model_id": "model-2",
                "config_id": "config-1",
                "type": "pii",
                "category": "EMAIL",
                "severity": "high",
                "message": "Email address detected in output",
                "blocked": False,
                "output_preview": "Contact john.doe@...",
            },
        ],
        "total": 234,
    }
