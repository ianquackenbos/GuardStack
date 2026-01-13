"""
GuardStack Evaluation Configuration Models

Pydantic models for evaluation request/response schemas.
"""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationConfig(BaseModel):
    """Base configuration for all evaluation types."""
    
    # Sampling
    sample_size: int = Field(default=1000, ge=1, le=100000)
    random_seed: Optional[int] = None
    
    # Parallelism
    parallel_workers: int = Field(default=4, ge=1, le=32)
    
    # Timeouts
    timeout_seconds: int = Field(default=3600, ge=60)
    
    # Output
    save_artifacts: bool = True
    generate_report: bool = True


class PredictiveEvalConfig(EvaluationConfig):
    """
    Configuration for Predictive AI (8-pillar) evaluation.
    
    Controls which pillars to run and their specific settings.
    """
    
    # Pillar selection (all enabled by default)
    pillars: list[str] = Field(
        default=[
            "explain",
            "actions", 
            "fairness",
            "robustness",
            "trace",
            "testing",
            "imitation",
            "privacy",
        ]
    )
    
    # Explain pillar settings
    explain_method: str = Field(default="shap", pattern="^(shap|lime|captum)$")
    explain_samples: int = Field(default=100, ge=10)
    
    # Actions pillar settings (adversarial)
    adversarial_attacks: list[str] = Field(
        default=["fgsm", "pgd", "deepfool", "c&w"]
    )
    adversarial_epsilon: float = Field(default=0.1, ge=0.0, le=1.0)
    
    # Fairness pillar settings
    sensitive_attributes: list[str] = Field(default=[])
    fairness_metrics: list[str] = Field(
        default=["demographic_parity", "equalized_odds", "calibration"]
    )
    
    # Robustness pillar settings
    noise_types: list[str] = Field(
        default=["gaussian", "uniform", "salt_pepper"]
    )
    noise_levels: list[float] = Field(default=[0.01, 0.05, 0.1])
    
    # Trace pillar settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Testing pillar settings
    performance_metrics: list[str] = Field(
        default=["accuracy", "precision", "recall", "f1", "auc"]
    )
    
    # Imitation pillar settings
    extraction_queries: int = Field(default=1000, ge=100)
    
    # Privacy pillar settings (MIA)
    mia_shadow_models: int = Field(default=10, ge=1)


class GenAIEvalConfig(EvaluationConfig):
    """
    Configuration for Gen AI (4-pillar) evaluation.
    
    Controls LLM safety testing parameters.
    """
    
    # Pillar selection
    pillars: list[str] = Field(
        default=["privacy", "toxicity", "fairness", "security"]
    )
    
    # Test prompts
    custom_prompts: list[str] = Field(default=[])
    use_standard_prompts: bool = True
    
    # Privacy pillar settings (PII)
    pii_entities: list[str] = Field(
        default=[
            "PERSON", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD",
            "SSN", "IP_ADDRESS", "LOCATION", "DATE_TIME",
        ]
    )
    pii_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Toxicity pillar settings
    toxicity_categories: list[str] = Field(
        default=[
            "toxicity", "severe_toxicity", "obscene",
            "threat", "insult", "identity_attack",
        ]
    )
    toxicity_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Fairness pillar settings
    demographic_groups: list[str] = Field(
        default=["gender", "race", "age", "religion"]
    )
    bias_prompts_per_group: int = Field(default=100, ge=10)
    
    # Security pillar settings (Red teaming)
    garak_probes: list[str] = Field(
        default=[
            "dan",
            "encoding",
            "gcg",
            "glitch",
            "goodside",
            "knownbadsignatures",
            "leakreplay",
            "lmrc",
            "malwaregen",
            "misleading",
            "packagehallucination",
            "promptinject",
            "realtoxicityprompts",
            "snowball",
            "xss",
        ]
    )
    max_attack_attempts: int = Field(default=100, ge=10)
    jailbreak_templates: list[str] = Field(default=[])


class SPMConfig(EvaluationConfig):
    """
    Configuration for AI Security Posture Management scans.
    
    Controls which security scans to run across model portfolio.
    """
    
    # Scan selection
    scans: list[str] = Field(
        default=[
            "privacy_leakage",
            "red_team",
            "ip_theft",
            "adversarial",
            "protection",
            "features",
            "fairness",
            "rogue",
            "toxicity",
            "metrics",
        ]
    )
    
    # Scope
    scan_all_models: bool = True
    model_ids: list[UUID] = Field(default=[])
    
    # Red teaming at scale
    red_team_depth: str = Field(default="standard", pattern="^(quick|standard|deep)$")
    
    # Alerting
    alert_on_critical: bool = True
    alert_threshold: float = Field(default=30.0, ge=0.0, le=100.0)


class AgenticConfig(EvaluationConfig):
    """
    Configuration for Agentic AI security testing.
    
    Controls agent and MCP tool calling security tests.
    """
    
    # Tool security testing
    test_tool_injection: bool = True
    test_parameter_fuzzing: bool = True
    test_privilege_escalation: bool = True
    test_data_exfiltration: bool = True
    
    # MCP monitoring
    mcp_servers: list[str] = Field(default=[])
    monitor_duration_seconds: int = Field(default=300, ge=60)
    
    # Guardrail validation
    validate_guardrails: bool = True
    guardrail_bypass_attempts: int = Field(default=100, ge=10)
    
    # Autonomy risk
    max_tool_chain_depth: int = Field(default=10, ge=1)
    blocked_tools: list[str] = Field(default=[])


# Request/Response schemas

class CreateModelRequest(BaseModel):
    """Request to register a new model."""
    name: str
    description: Optional[str] = None
    model_type: str  # predictive, genai, agentic
    connector_type: str
    connector_config: dict[str, Any] = Field(default={})
    version: Optional[str] = None
    tags: list[str] = Field(default=[])
    owner: Optional[str] = None
    team: Optional[str] = None


class StartEvaluationRequest(BaseModel):
    """Request to start an evaluation."""
    evaluation_type: str  # predictive, genai, spm, agentic
    config: dict[str, Any] = Field(default={})


class DashboardSummary(BaseModel):
    """Dashboard summary response."""
    total_models: int
    pass_count: int
    warn_count: int
    fail_count: int
    average_score: float
    last_updated: str


class ModelRiskSummary(BaseModel):
    """Risk summary for a single model."""
    id: UUID
    name: str
    model_type: str
    status: str
    overall_score: float
    pillar_scores: dict[str, float]
    last_evaluated: Optional[str]
    trend: str


class TrendDataPoint(BaseModel):
    """Single data point for trend charts."""
    date: str
    overall_score: float
    by_pillar: dict[str, float]


class ComplianceStatus(BaseModel):
    """Compliance status for a framework."""
    framework: str
    coverage_percentage: float
    met_requirements: int
    total_requirements: int
    risk_classification: Optional[str] = None
    gaps: list[str] = Field(default=[])
