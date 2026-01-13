"""
Evaluations API Router

Endpoints for managing and monitoring evaluation workflows.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter()


class EvaluationResponse(BaseModel):
    """Response model for evaluations."""
    id: UUID
    model_id: UUID
    workflow_name: str
    evaluation_type: str
    status: str
    progress: float
    overall_score: Optional[float]
    risk_status: Optional[str]
    findings_count: int
    critical_findings: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    triggered_by: Optional[str]


class PillarResultResponse(BaseModel):
    """Response model for pillar results."""
    pillar_name: str
    pillar_category: str
    score: float
    status: str
    findings: list[dict[str, Any]]
    metrics: dict[str, Any]
    execution_time_ms: int


class EvaluationDetailResponse(BaseModel):
    """Detailed evaluation response with pillar results."""
    evaluation: EvaluationResponse
    pillar_results: list[PillarResultResponse]
    config: dict[str, Any]


class EvaluationsListResponse(BaseModel):
    """Response for listing evaluations."""
    evaluations: list[EvaluationResponse]
    total: int
    page: int
    page_size: int


# In-memory storage for demo
_evaluations_db: dict[UUID, dict] = {}


@router.get("", response_model=EvaluationsListResponse)
async def list_evaluations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    model_id: Optional[UUID] = None,
    evaluation_type: Optional[str] = None,
    status: Optional[str] = None,
) -> EvaluationsListResponse:
    """
    List all evaluations.
    
    Supports filtering by model, evaluation type, and status.
    """
    evaluations = list(_evaluations_db.values())
    
    # Apply filters
    if model_id:
        evaluations = [e for e in evaluations if e["model_id"] == model_id]
    if evaluation_type:
        evaluations = [e for e in evaluations if e["evaluation_type"] == evaluation_type]
    if status:
        evaluations = [e for e in evaluations if e["status"] == status]
    
    # Sort by created_at descending
    evaluations.sort(key=lambda e: e["created_at"], reverse=True)
    
    total = len(evaluations)
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    evaluations = evaluations[start:end]
    
    return EvaluationsListResponse(
        evaluations=[EvaluationResponse(**e) for e in evaluations],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{evaluation_id}", response_model=EvaluationDetailResponse)
async def get_evaluation(evaluation_id: UUID) -> EvaluationDetailResponse:
    """
    Get detailed results for an evaluation.
    
    Includes all pillar results and configuration.
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = _evaluations_db[evaluation_id]
    
    # TODO: Fetch pillar results from database
    pillar_results = evaluation.get("pillar_results", [])
    
    return EvaluationDetailResponse(
        evaluation=EvaluationResponse(**evaluation),
        pillar_results=[PillarResultResponse(**p) for p in pillar_results],
        config=evaluation.get("config", {}),
    )


@router.get("/{evaluation_id}/status")
async def get_evaluation_status(evaluation_id: UUID) -> dict[str, Any]:
    """
    Get the current status of an evaluation.
    
    Returns workflow status from Argo.
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = _evaluations_db[evaluation_id]
    
    # TODO: Fetch workflow status from Argo
    # workflow_status = await argo_client.get_workflow_status(evaluation["workflow_name"])
    
    return {
        "evaluation_id": str(evaluation_id),
        "status": evaluation["status"],
        "progress": evaluation["progress"],
        "message": "Evaluation in progress",
        "current_step": "privacy_pillar",
        "completed_steps": ["toxicity_pillar"],
        "remaining_steps": ["fairness_pillar", "security_pillar"],
    }


@router.post("/{evaluation_id}/cancel")
async def cancel_evaluation(evaluation_id: UUID) -> dict[str, Any]:
    """
    Cancel a running evaluation.
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = _evaluations_db[evaluation_id]
    
    if evaluation["status"] not in ["pending", "running"]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot cancel evaluation in current status"
        )
    
    # TODO: Cancel Argo workflow
    # await argo_client.cancel_workflow(evaluation["workflow_name"])
    
    evaluation["status"] = "cancelled"
    
    return {
        "evaluation_id": str(evaluation_id),
        "status": "cancelled",
        "message": "Evaluation cancelled successfully",
    }


@router.get("/{evaluation_id}/report")
async def get_evaluation_report(
    evaluation_id: UUID,
    format: str = Query(default="pdf", pattern="^(pdf|json|html)$"),
) -> StreamingResponse:
    """
    Download the evaluation report.
    
    Available formats: pdf, json, html
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = _evaluations_db[evaluation_id]
    
    if evaluation["status"] != "succeeded":
        raise HTTPException(
            status_code=400,
            detail="Report only available for completed evaluations"
        )
    
    # TODO: Generate report from S3/MinIO artifacts
    # report_bytes = await storage.get_report(evaluation_id, format)
    
    # Placeholder response
    import json
    report_data = {
        "evaluation_id": str(evaluation_id),
        "model_id": str(evaluation["model_id"]),
        "evaluation_type": evaluation["evaluation_type"],
        "overall_score": evaluation.get("overall_score"),
        "risk_status": evaluation.get("risk_status"),
        "generated_at": evaluation.get("completed_at"),
    }
    
    if format == "json":
        return StreamingResponse(
            iter([json.dumps(report_data, indent=2)]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=report-{evaluation_id}.json"
            }
        )
    
    # TODO: Generate PDF/HTML reports
    raise HTTPException(status_code=501, detail=f"Format {format} not yet implemented")


@router.get("/{evaluation_id}/artifacts")
async def list_evaluation_artifacts(evaluation_id: UUID) -> dict[str, Any]:
    """
    List all artifacts generated by an evaluation.
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # TODO: List artifacts from S3/MinIO
    # artifacts = await storage.list_artifacts(evaluation_id)
    
    return {
        "evaluation_id": str(evaluation_id),
        "artifacts": [
            {
                "name": "privacy_pillar_results.json",
                "size_bytes": 12345,
                "created_at": "2024-01-15T10:30:00Z",
            },
            {
                "name": "toxicity_pillar_results.json",
                "size_bytes": 8765,
                "created_at": "2024-01-15T10:31:00Z",
            },
            {
                "name": "full_report.pdf",
                "size_bytes": 125000,
                "created_at": "2024-01-15T10:35:00Z",
            },
        ]
    }


@router.get("/{evaluation_id}/artifacts/{artifact_name}")
async def download_artifact(
    evaluation_id: UUID,
    artifact_name: str,
) -> StreamingResponse:
    """
    Download a specific artifact from an evaluation.
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # TODO: Download artifact from S3/MinIO
    # artifact_bytes = await storage.get_artifact(evaluation_id, artifact_name)
    
    raise HTTPException(status_code=501, detail="Artifact download not yet implemented")


@router.post("/{evaluation_id}/retry")
async def retry_evaluation(evaluation_id: UUID) -> dict[str, Any]:
    """
    Retry a failed evaluation.
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = _evaluations_db[evaluation_id]
    
    if evaluation["status"] != "failed":
        raise HTTPException(
            status_code=400,
            detail="Can only retry failed evaluations"
        )
    
    # TODO: Resubmit Argo workflow
    # new_workflow = await argo_client.retry_workflow(evaluation["workflow_name"])
    
    from datetime import datetime
    from uuid import uuid4
    
    new_evaluation_id = uuid4()
    
    return {
        "evaluation_id": str(new_evaluation_id),
        "original_evaluation_id": str(evaluation_id),
        "status": "pending",
        "message": "Evaluation retry submitted",
        "created_at": datetime.utcnow().isoformat(),
    }
