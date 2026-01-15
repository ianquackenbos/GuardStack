"""
Dashboard API Router

Endpoints for the executive dashboard and portfolio view.

Note: Currently returns demo data. In production, these endpoints
query PostgreSQL with pgvector for model and evaluation data.
"""

from datetime import datetime, timedelta
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


# Demo data storage (in production, this comes from PostgreSQL)
_demo_models = [
    {
        "id": "model-1",
        "name": "GPT-4 Production",
        "model_type": "genai",
        "status": "pass",
        "overall_score": 85.0,
        "pillar_scores": {
            "privacy": 90.0,
            "toxicity": 88.0,
            "fairness": 82.0,
            "security": 80.0,
        },
        "last_evaluated": "2026-01-15T10:30:00Z",
        "trend": "improving",
        "critical_findings": 0,
    },
    {
        "id": "model-2",
        "name": "Fraud Detection ML",
        "model_type": "predictive",
        "status": "warn",
        "overall_score": 65.0,
        "pillar_scores": {
            "explain": 70.0,
            "actions": 60.0,
            "fairness": 55.0,
            "robustness": 75.0,
            "trace": 80.0,
            "testing": 65.0,
            "imitation": 60.0,
            "privacy": 55.0,
        },
        "last_evaluated": "2026-01-14T15:00:00Z",
        "trend": "stable",
        "critical_findings": 3,
    },
    {
        "id": "model-3",
        "name": "Customer Service Agent",
        "model_type": "agentic",
        "status": "fail",
        "overall_score": 35.0,
        "pillar_scores": {
            "tool_security": 30.0,
            "guardrails": 40.0,
            "autonomy_risk": 35.0,
        },
        "last_evaluated": "2026-01-13T08:00:00Z",
        "trend": "degrading",
        "critical_findings": 8,
    },
    {
        "id": "model-4",
        "name": "Content Moderation",
        "model_type": "genai",
        "status": "pass",
        "overall_score": 92.0,
        "pillar_scores": {
            "privacy": 95.0,
            "toxicity": 94.0,
            "fairness": 88.0,
            "security": 91.0,
        },
        "last_evaluated": "2026-01-15T08:00:00Z",
        "trend": "stable",
        "critical_findings": 0,
    },
    {
        "id": "model-5",
        "name": "Recommendation Engine",
        "model_type": "predictive",
        "status": "pass",
        "overall_score": 78.0,
        "pillar_scores": {
            "explain": 80.0,
            "fairness": 75.0,
            "robustness": 82.0,
            "testing": 76.0,
        },
        "last_evaluated": "2026-01-14T12:00:00Z",
        "trend": "improving",
        "critical_findings": 1,
    },
]


def _calculate_summary() -> DashboardSummary:
    """Calculate portfolio summary from demo data."""
    pass_count = len([m for m in _demo_models if m["status"] == "pass"])
    warn_count = len([m for m in _demo_models if m["status"] == "warn"])
    fail_count = len([m for m in _demo_models if m["status"] == "fail"])
    avg_score = sum(m["overall_score"] for m in _demo_models) / len(_demo_models) if _demo_models else 0
    critical = sum(m["critical_findings"] for m in _demo_models)
    
    return DashboardSummary(
        total_models=len(_demo_models),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        average_score=round(avg_score, 1),
        models_evaluated_last_24h=3,
        models_evaluated_last_7d=len(_demo_models),
        critical_findings=critical,
    )


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary() -> DashboardSummary:
    """
    Get portfolio risk summary.
    
    Returns aggregate counts for Pass/Warn/Fail status across
    all registered models. In production, queries PostgreSQL
    for real-time aggregates.
    """
    return _calculate_summary()


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
    models = [ModelRiskSummary(**m) for m in _demo_models]
    
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
    elif sort_by == "last_evaluated":
        models.sort(key=lambda m: m.last_evaluated or "", reverse=reverse)
    
    return models[:limit]


@router.get("/trends", response_model=list[TrendDataPoint])
async def get_risk_trends(
    days: int = Query(default=30, ge=7, le=365),
    model_id: Optional[str] = None,
) -> list[TrendDataPoint]:
    """
    Get risk trends over time.
    
    Returns historical data for trend charts showing
    risk evolution. In production, queries time-series
    data from evaluations table.
    """
    trends = []
    base_date = datetime.utcnow()
    
    # Generate realistic trend data with some variance
    import math
    
    for i in range(days, 0, -1):
        date = base_date - timedelta(days=i)
        # Add some sinusoidal variation for realistic trends
        variance = math.sin(i / 7 * math.pi) * 5
        
        trends.append(TrendDataPoint(
            date=date.strftime("%Y-%m-%d"),
            overall_score=round(72.0 + variance, 1),
            pass_count=3 + (i % 2),
            warn_count=1 + ((i + 1) % 2),
            fail_count=1,
            by_pillar={
                "privacy": round(78.0 + variance * 0.8, 1),
                "toxicity": round(82.0 + variance * 0.6, 1),
                "fairness": round(65.0 + variance * 1.2, 1),
                "security": round(70.0 + variance, 1),
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
    Aggregates pillar scores from all evaluations.
    """
    # Aggregate pillar scores from demo models
    pillar_data: dict[str, list[float]] = {}
    
    for model in _demo_models:
        if evaluation_type and model["model_type"] != evaluation_type:
            continue
        for pillar, score in model["pillar_scores"].items():
            if pillar not in pillar_data:
                pillar_data[pillar] = []
            pillar_data[pillar].append(score)
    
    pillars = []
    for pillar_name, scores in pillar_data.items():
        avg = sum(scores) / len(scores) if scores else 0
        pass_count = len([s for s in scores if s >= 70])
        warn_count = len([s for s in scores if 50 <= s < 70])
        fail_count = len([s for s in scores if s < 50])
        
        pillars.append(PillarBreakdown(
            pillar_name=pillar_name,
            average_score=round(avg, 1),
            model_count=len(scores),
            pass_count=pass_count,
            warn_count=warn_count,
            fail_count=fail_count,
        ))
    
    # Sort by average score
    pillars.sort(key=lambda p: p.average_score, reverse=True)
    
    return pillars


@router.get("/alerts")
async def get_active_alerts(
    severity: Optional[str] = Query(default=None, pattern="^(critical|warning|info)$"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    """
    Get active alerts from recent evaluations.
    
    Alerts are generated when pillar scores fall below
    thresholds or critical findings are detected.
    """
    alerts = [
        {
            "id": "alert-1",
            "severity": "critical",
            "model_id": "model-3",
            "model_name": "Customer Service Agent",
            "pillar": "tool_security",
            "message": "Multiple tool injection vulnerabilities detected",
            "created_at": "2026-01-15T10:00:00Z",
            "acknowledged": False,
        },
        {
            "id": "alert-2",
            "severity": "warning",
            "model_id": "model-2",
            "model_name": "Fraud Detection ML",
            "pillar": "fairness",
            "message": "Demographic parity below threshold for age group",
            "created_at": "2026-01-14T15:30:00Z",
            "acknowledged": True,
        },
        {
            "id": "alert-3",
            "severity": "critical",
            "model_id": "model-3",
            "model_name": "Customer Service Agent",
            "pillar": "guardrails",
            "message": "Jailbreak attempts succeeded in 15% of test cases",
            "created_at": "2026-01-13T09:00:00Z",
            "acknowledged": False,
        },
        {
            "id": "alert-4",
            "severity": "info",
            "model_id": "model-5",
            "model_name": "Recommendation Engine",
            "pillar": "explain",
            "message": "Explainability score improved by 8% since last evaluation",
            "created_at": "2026-01-14T12:30:00Z",
            "acknowledged": True,
        },
    ]
    
    # Apply severity filter
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]
    
    # Calculate totals
    all_alerts = [
        {"severity": "critical"},
        {"severity": "critical"},
        {"severity": "critical"},
        {"severity": "warning"},
        {"severity": "warning"},
        {"severity": "warning"},
        {"severity": "warning"},
        {"severity": "warning"},
        {"severity": "info"},
        {"severity": "info"},
        {"severity": "info"},
    ]
    
    return {
        "alerts": alerts[:limit],
        "total_critical": len([a for a in all_alerts if a["severity"] == "critical"]),
        "total_warning": len([a for a in all_alerts if a["severity"] == "warning"]),
        "total_info": len([a for a in all_alerts if a["severity"] == "info"]),
    }


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    """
    Acknowledge an alert.
    
    Acknowledged alerts are still visible but marked as reviewed.
    """
    return {
        "alert_id": alert_id,
        "acknowledged": True,
        "acknowledged_at": datetime.utcnow().isoformat(),
    }


@router.get("/comparison")
async def get_before_after_comparison(
    model_id: str,
    evaluation_ids: list[str] = Query(..., min_length=2, max_length=2),
) -> dict[str, Any]:
    """
    Get before/after comparison between two evaluations.
    
    Useful for measuring guardrail improvement and demonstrating
    the impact of remediation efforts.
    """
    # Find model
    model = next((m for m in _demo_models if m["id"] == model_id), None)
    if not model:
        model = _demo_models[0]  # Fallback to first model for demo
    
    # Generate comparison data
    before_score = model["overall_score"] - 20
    before_pillars = {k: max(v - 25, 10) for k, v in model["pillar_scores"].items()}
    
    return {
        "model_id": model_id,
        "model_name": model["name"],
        "before": {
            "evaluation_id": evaluation_ids[0],
            "date": "2026-01-01T00:00:00Z",
            "overall_score": before_score,
            "pillar_scores": before_pillars,
            "status": "fail" if before_score < 50 else "warn",
        },
        "after": {
            "evaluation_id": evaluation_ids[1],
            "date": "2026-01-15T00:00:00Z",
            "overall_score": model["overall_score"],
            "pillar_scores": model["pillar_scores"],
            "status": model["status"],
        },
        "improvement": {
            "overall_score": round(model["overall_score"] - before_score, 1),
            "pillar_improvements": {
                k: round(model["pillar_scores"][k] - before_pillars[k], 1)
                for k in model["pillar_scores"]
            },
            "status_change": f"{'fail' if before_score < 50 else 'warn'} → {model['status']}",
        },
    }


@router.get("/export")
async def export_dashboard_data(
    format: str = Query(default="json", pattern="^(json|csv)$"),
) -> dict[str, Any]:
    """
    Export dashboard data for reporting.
    
    Returns portfolio summary and model data in the requested format.
    """
    summary = _calculate_summary()
    
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "format": format,
        "summary": summary.model_dump(),
        "models": _demo_models,
        "total_records": len(_demo_models),
    }
