"""
Dashboard API Router

Endpoints for the executive dashboard and portfolio view.
"""

from typing import Any, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter()


class DashboardSummary(BaseModel):
    """Portfolio risk summary."""
    total_models: int
    pass_count: int
    warn_count: int
    fail_count: int
    average_score: float
    models_evaluated_last_24h: int
    models_evaluated_last_7d: int
    critical_findings: int


class ModelRiskSummary(BaseModel):
    """Risk summary for a single model."""
    id: str
    name: str
    model_type: str
    status: str
    overall_score: float
    pillar_scores: dict[str, float]
    last_evaluated: Optional[str]
    trend: str
    critical_findings: int


class TrendDataPoint(BaseModel):
    """Data point for trend charts."""
    date: str
    overall_score: float
    pass_count: int
    warn_count: int
    fail_count: int
    by_pillar: dict[str, float]


class PillarBreakdown(BaseModel):
    """Breakdown of scores by pillar."""
    pillar_name: str
    average_score: float
    model_count: int
    pass_count: int
    warn_count: int
    fail_count: int


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary() -> DashboardSummary:
    """
    Get portfolio risk summary.
    
    Returns aggregate counts for Pass/Warn/Fail status across
    all registered models.
    """
    # TODO: Query from database
    
    # Demo data
    return DashboardSummary(
        total_models=25,
        pass_count=15,
        warn_count=7,
        fail_count=3,
        average_score=72.5,
        models_evaluated_last_24h=5,
        models_evaluated_last_7d=18,
        critical_findings=12,
    )


@router.get("/models", response_model=list[ModelRiskSummary])
async def get_models_risk_summary(
    status: Optional[str] = Query(default=None, pattern="^(pass|warn|fail)$"),
    model_type: Optional[str] = Query(default=None, pattern="^(predictive|genai|agentic)$"),
    sort_by: str = Query(default="score", pattern="^(score|name|last_evaluated)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ModelRiskSummary]:
    """
    Get risk summary for all models.
    
    Returns a list of models with their current risk status
    and pillar scores for the portfolio view.
    """
    # TODO: Query from database
    
    # Demo data
    models = [
        ModelRiskSummary(
            id="model-1",
            name="GPT-4 Production",
            model_type="genai",
            status="pass",
            overall_score=85.0,
            pillar_scores={
                "privacy": 90.0,
                "toxicity": 88.0,
                "fairness": 82.0,
                "security": 80.0,
            },
            last_evaluated="2024-01-15T10:30:00Z",
            trend="improving",
            critical_findings=0,
        ),
        ModelRiskSummary(
            id="model-2",
            name="Fraud Detection ML",
            model_type="predictive",
            status="warn",
            overall_score=65.0,
            pillar_scores={
                "explain": 70.0,
                "actions": 60.0,
                "fairness": 55.0,
                "robustness": 75.0,
                "trace": 80.0,
                "testing": 65.0,
                "imitation": 60.0,
                "privacy": 55.0,
            },
            last_evaluated="2024-01-14T15:00:00Z",
            trend="stable",
            critical_findings=3,
        ),
        ModelRiskSummary(
            id="model-3",
            name="Customer Service Agent",
            model_type="agentic",
            status="fail",
            overall_score=35.0,
            pillar_scores={
                "tool_security": 30.0,
                "guardrails": 40.0,
                "autonomy_risk": 35.0,
            },
            last_evaluated="2024-01-13T08:00:00Z",
            trend="degrading",
            critical_findings=8,
        ),
    ]
    
    # Apply filters
    if status:
        models = [m for m in models if m.status == status]
    if model_type:
        models = [m for m in models if m.model_type == model_type]
    
    # Sort
    reverse = sort_order == "desc"
    if sort_by == "score":
        models.sort(key=lambda m: m.overall_score, reverse=reverse)
    elif sort_by == "name":
        models.sort(key=lambda m: m.name, reverse=reverse)
    
    return models[:limit]


@router.get("/trends", response_model=list[TrendDataPoint])
async def get_risk_trends(
    days: int = Query(default=30, ge=7, le=365),
    model_id: Optional[str] = None,
) -> list[TrendDataPoint]:
    """
    Get risk trends over time.
    
    Returns historical data for trend charts showing
    risk evolution.
    """
    # TODO: Query from database
    
    # Demo data - generate trend points
    from datetime import datetime, timedelta
    
    trends = []
    base_date = datetime.utcnow()
    
    for i in range(days, 0, -1):
        date = base_date - timedelta(days=i)
        trends.append(TrendDataPoint(
            date=date.strftime("%Y-%m-%d"),
            overall_score=70.0 + (i % 10) - 5,
            pass_count=15 + (i % 3),
            warn_count=7 + (i % 2),
            fail_count=3 + (i % 2),
            by_pillar={
                "privacy": 75.0 + (i % 8),
                "toxicity": 72.0 + (i % 6),
                "fairness": 68.0 + (i % 10),
                "security": 65.0 + (i % 12),
            },
        ))
    
    return trends


@router.get("/pillars", response_model=list[PillarBreakdown])
async def get_pillar_breakdown(
    evaluation_type: Optional[str] = Query(
        default=None, 
        pattern="^(predictive|genai|spm|agentic)$"
    ),
) -> list[PillarBreakdown]:
    """
    Get breakdown of scores by pillar across all models.
    
    Useful for identifying systemic weaknesses.
    """
    # TODO: Query from database
    
    # Demo data
    pillars = [
        PillarBreakdown(
            pillar_name="privacy",
            average_score=78.5,
            model_count=20,
            pass_count=14,
            warn_count=5,
            fail_count=1,
        ),
        PillarBreakdown(
            pillar_name="toxicity",
            average_score=82.0,
            model_count=15,
            pass_count=12,
            warn_count=2,
            fail_count=1,
        ),
        PillarBreakdown(
            pillar_name="fairness",
            average_score=65.0,
            model_count=25,
            pass_count=10,
            warn_count=10,
            fail_count=5,
        ),
        PillarBreakdown(
            pillar_name="security",
            average_score=70.0,
            model_count=15,
            pass_count=8,
            warn_count=5,
            fail_count=2,
        ),
    ]
    
    return pillars


@router.get("/alerts")
async def get_active_alerts(
    severity: Optional[str] = Query(default=None, pattern="^(critical|warning|info)$"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """
    Get active alerts from recent evaluations.
    """
    # TODO: Query from database
    
    return {
        "alerts": [
            {
                "id": "alert-1",
                "severity": "critical",
                "model_id": "model-3",
                "model_name": "Customer Service Agent",
                "pillar": "tool_security",
                "message": "Multiple tool injection vulnerabilities detected",
                "created_at": "2024-01-15T10:00:00Z",
                "acknowledged": False,
            },
            {
                "id": "alert-2",
                "severity": "warning",
                "model_id": "model-2",
                "model_name": "Fraud Detection ML",
                "pillar": "fairness",
                "message": "Demographic parity below threshold for age group",
                "created_at": "2024-01-14T15:30:00Z",
                "acknowledged": True,
            },
        ],
        "total_critical": 3,
        "total_warning": 8,
        "total_info": 15,
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    """
    Acknowledge an alert.
    """
    return {
        "alert_id": alert_id,
        "acknowledged": True,
        "acknowledged_at": "2024-01-15T11:00:00Z",
    }


@router.get("/comparison")
async def get_before_after_comparison(
    model_id: str,
    evaluation_ids: list[str] = Query(..., min_length=2, max_length=2),
) -> dict[str, Any]:
    """
    Get before/after comparison between two evaluations.
    
    Useful for measuring guardrail improvement.
    """
    # TODO: Query from database
    
    return {
        "model_id": model_id,
        "before": {
            "evaluation_id": evaluation_ids[0],
            "date": "2024-01-01T00:00:00Z",
            "overall_score": 55.0,
            "pillar_scores": {
                "privacy": 50.0,
                "toxicity": 60.0,
                "fairness": 45.0,
                "security": 65.0,
            },
        },
        "after": {
            "evaluation_id": evaluation_ids[1],
            "date": "2024-01-15T00:00:00Z",
            "overall_score": 78.0,
            "pillar_scores": {
                "privacy": 80.0,
                "toxicity": 82.0,
                "fairness": 70.0,
                "security": 80.0,
            },
        },
        "improvement": {
            "overall_score": 23.0,
            "pillar_improvements": {
                "privacy": 30.0,
                "toxicity": 22.0,
                "fairness": 25.0,
                "security": 15.0,
            },
        },
    }
