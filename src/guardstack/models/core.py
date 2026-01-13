"""
GuardStack Core Data Models

SQLModel definitions for the core database entities.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import Field
from sqlmodel import JSON, Column, SQLModel


class ModelType(str, Enum):
    """Type of AI model being evaluated."""
    PREDICTIVE = "predictive"
    GENAI = "genai"
    AGENTIC = "agentic"


class RiskStatus(str, Enum):
    """Risk status indicator (traffic light)."""
    PASS = "pass"      # Green - ready for production
    WARN = "warn"      # Yellow - needs review
    FAIL = "fail"      # Red - critical issues


class TrendDirection(str, Enum):
    """Trend direction for risk over time."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


class EvaluationStatus(str, Enum):
    """Status of an evaluation workflow."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RegisteredModel(SQLModel, table=True):
    """
    A registered AI model in the GuardStack platform.
    
    Stores model metadata, connector configuration, and current risk status.
    """
    __tablename__ = "registered_models"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    model_type: ModelType
    
    # Connector configuration
    connector_type: str  # openai, anthropic, ollama, etc.
    connector_config: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    
    # Metadata
    version: Optional[str] = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Current status (updated after each evaluation)
    current_status: RiskStatus = RiskStatus.WARN
    current_score: Optional[float] = None
    trend: TrendDirection = TrendDirection.STABLE
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_evaluated: Optional[datetime] = None
    
    # Owner/Team
    owner: Optional[str] = None
    team: Optional[str] = None


class Evaluation(SQLModel, table=True):
    """
    An evaluation run against a registered model.
    
    Tracks the Argo workflow execution and stores results.
    """
    __tablename__ = "evaluations"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_id: UUID = Field(foreign_key="registered_models.id", index=True)
    
    # Argo workflow reference
    workflow_name: str
    workflow_namespace: str = "guardstack"
    
    # Evaluation type and config
    evaluation_type: str  # predictive, genai, spm, agentic
    config: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Status
    status: EvaluationStatus = EvaluationStatus.PENDING
    progress: float = 0.0  # 0-100 percentage
    
    # Results (populated on completion)
    results: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    overall_score: Optional[float] = None
    risk_status: Optional[RiskStatus] = None
    
    # Findings summary
    findings_count: int = 0
    critical_findings: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Triggered by
    triggered_by: Optional[str] = None  # user or "scheduled"


class PillarResult(SQLModel, table=True):
    """
    Results for a single pillar in an evaluation.
    
    Each evaluation has multiple pillar results (8 for predictive, 4 for genai).
    """
    __tablename__ = "pillar_results"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    evaluation_id: UUID = Field(foreign_key="evaluations.id", index=True)
    
    # Pillar identification
    pillar_name: str  # explain, actions, fairness, etc.
    pillar_category: str  # predictive, genai, spm, agentic
    
    # Scoring
    score: float  # 0-100
    status: RiskStatus
    weight: float = 1.0  # For weighted aggregation
    
    # Detailed results
    findings: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    
    # Execution info
    execution_time_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceMapping(SQLModel, table=True):
    """
    Compliance framework mapping for a model.
    
    Maps evaluation results to compliance requirements (EU AI Act, SOC2, etc.).
    """
    __tablename__ = "compliance_mappings"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    model_id: UUID = Field(foreign_key="registered_models.id", index=True)
    
    # Compliance framework
    framework: str  # eu_ai_act, soc2, hipaa, iso27001
    framework_version: str = "1.0"
    
    # Requirements mapping
    requirements: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )  # requirement_id -> {status, evidence, gaps}
    
    # Coverage metrics
    total_requirements: int = 0
    met_requirements: int = 0
    partial_requirements: int = 0
    coverage_percentage: float = 0.0
    
    # Risk classification (for EU AI Act)
    risk_classification: Optional[str] = None  # unacceptable, high, limited, minimal
    
    # Timestamps
    last_assessed: datetime = Field(default_factory=datetime.utcnow)
    next_review: Optional[datetime] = None


class AuditLog(SQLModel, table=True):
    """
    Audit log for tracking all platform actions.
    
    Provides complete audit trail for compliance and security.
    """
    __tablename__ = "audit_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Actor
    user_id: str
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    
    # Action
    action: str  # create, update, delete, evaluate, export
    resource_type: str  # model, evaluation, compliance, guardrail
    resource_id: Optional[UUID] = None
    
    # Details
    details: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    
    # Outcome
    success: bool = True
    error_message: Optional[str] = None


class GuardrailConfig(SQLModel, table=True):
    """
    Runtime guardrail configuration.
    
    Defines guardrail rules for real-time inference protection.
    """
    __tablename__ = "guardrail_configs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    
    # Status
    enabled: bool = True
    
    # Configuration
    config: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    
    # NeMo Guardrails specific
    colang_content: Optional[str] = None
    yaml_config: Optional[str] = None
    
    # Thresholds
    pii_enabled: bool = True
    pii_threshold: float = 0.5
    toxicity_enabled: bool = True
    toxicity_threshold: float = 0.5
    jailbreak_enabled: bool = True
    jailbreak_threshold: float = 0.5
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    """
    User account for the GuardStack platform.
    
    Stores user credentials and authorization information.
    """
    __tablename__ = "users"
    
    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    name: Optional[str] = None
    
    # Authentication
    hashed_password: Optional[str] = None
    
    # Authorization
    is_active: bool = True
    is_admin: bool = False
    permissions: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Profile
    organization: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
