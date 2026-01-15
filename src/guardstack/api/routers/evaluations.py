"""
Evaluations API Router

Endpoints for managing and monitoring evaluation workflows.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from guardstack.services.argo import (
    get_argo_service,
    get_evaluation_workflow_service,
    ArgoWorkflowService,
    EvaluationWorkflowService,
)

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


def _status_to_progress(status: str) -> float:
    """Convert Argo workflow status to progress percentage."""
    status_map = {
        "Pending": 0.0,
        "Running": 0.5,
        "Succeeded": 1.0,
        "Failed": 1.0,
        "Error": 1.0,
        "Skipped": 1.0,
        "Omitted": 0.0,
    }
    return status_map.get(status, 0.0)


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
    
    # Fetch pillar results from Argo workflow artifacts if available
    pillar_results = evaluation.get("pillar_results", [])
    
    # Try to get additional data from Argo
    if evaluation.get("workflow_name"):
        eval_service = get_evaluation_workflow_service()
        try:
            report = await eval_service.get_evaluation_report(evaluation["workflow_name"])
            if report and "pillar_results" in report:
                pillar_results = report["pillar_results"]
        except Exception:
            pass  # Use cached data if Argo unavailable
    
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
    workflow_name = evaluation.get("workflow_name")
    
    # Fetch live workflow status from Argo
    argo_service = get_argo_service()
    
    try:
        workflow_status = await argo_service.get_workflow_status(workflow_name)
        
        # Update local cache
        evaluation["status"] = workflow_status.phase.lower()
        evaluation["progress"] = workflow_status.progress
        if workflow_status.started_at:
            evaluation["started_at"] = workflow_status.started_at.isoformat()
        if workflow_status.finished_at:
            evaluation["completed_at"] = workflow_status.finished_at.isoformat()
        
        # Parse step information
        completed_steps = []
        running_steps = []
        remaining_steps = []
        
        for node_name, node_status in workflow_status.nodes.items():
            if node_status.get("type") == "Pod":
                step_name = node_name.split(".")[-1] if "." in node_name else node_name
                phase = node_status.get("phase", "Pending")
                if phase == "Succeeded":
                    completed_steps.append(step_name)
                elif phase == "Running":
                    running_steps.append(step_name)
                else:
                    remaining_steps.append(step_name)
        
        return {
            "evaluation_id": str(evaluation_id),
            "workflow_name": workflow_name,
            "status": workflow_status.phase.lower(),
            "progress": workflow_status.progress,
            "message": workflow_status.message or "Evaluation in progress",
            "current_step": running_steps[0] if running_steps else None,
            "completed_steps": completed_steps,
            "remaining_steps": remaining_steps,
            "started_at": workflow_status.started_at.isoformat() if workflow_status.started_at else None,
            "finished_at": workflow_status.finished_at.isoformat() if workflow_status.finished_at else None,
        }
    except Exception as e:
        # Fallback to cached status
        return {
            "evaluation_id": str(evaluation_id),
            "workflow_name": workflow_name,
            "status": evaluation["status"],
            "progress": evaluation["progress"],
            "message": f"Unable to fetch live status: {str(e)}",
            "current_step": None,
            "completed_steps": [],
            "remaining_steps": [],
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
    
    # Cancel Argo workflow
    argo_service = get_argo_service()
    workflow_name = evaluation.get("workflow_name")
    
    try:
        success = await argo_service.cancel_workflow(workflow_name)
        if success:
            evaluation["status"] = "cancelled"
            return {
                "evaluation_id": str(evaluation_id),
                "workflow_name": workflow_name,
                "status": "cancelled",
                "message": "Evaluation cancelled successfully",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to cancel workflow"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling workflow: {str(e)}"
        )


@router.get("/{evaluation_id}/report")
async def get_evaluation_report(
    evaluation_id: UUID,
    format: str = Query(default="json", pattern="^(pdf|json|html)$"),
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
    
    # Fetch report from Argo artifacts
    eval_service = get_evaluation_workflow_service()
    workflow_name = evaluation.get("workflow_name")
    
    try:
        report_data = await eval_service.get_evaluation_report(workflow_name)
    except Exception:
        # Generate report from cached data
        report_data = {
            "evaluation_id": str(evaluation_id),
            "model_id": str(evaluation["model_id"]),
            "evaluation_type": evaluation["evaluation_type"],
            "overall_score": evaluation.get("overall_score"),
            "risk_status": evaluation.get("risk_status"),
            "findings_count": evaluation.get("findings_count", 0),
            "critical_findings": evaluation.get("critical_findings", 0),
            "pillar_results": evaluation.get("pillar_results", []),
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    import json
    
    if format == "json":
        return StreamingResponse(
            iter([json.dumps(report_data, indent=2, default=str)]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=report-{evaluation_id}.json"
            }
        )
    
    if format == "html":
        # Generate simple HTML report
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Evaluation Report - {evaluation_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .metric {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
        .score {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
        .risk-high {{ color: #f44336; }}
        .risk-medium {{ color: #ff9800; }}
        .risk-low {{ color: #4caf50; }}
    </style>
</head>
<body>
    <h1>GuardStack Evaluation Report</h1>
    <div class="metric">
        <strong>Evaluation ID:</strong> {evaluation_id}<br>
        <strong>Model ID:</strong> {evaluation.get("model_id")}<br>
        <strong>Type:</strong> {evaluation.get("evaluation_type")}<br>
        <strong>Status:</strong> {evaluation.get("status")}
    </div>
    <div class="metric">
        <strong>Overall Score:</strong> <span class="score">{evaluation.get("overall_score", "N/A")}</span><br>
        <strong>Risk Status:</strong> <span class="risk-{evaluation.get('risk_status', 'medium').lower()}">{evaluation.get("risk_status", "N/A")}</span>
    </div>
    <div class="metric">
        <strong>Findings:</strong> {evaluation.get("findings_count", 0)}<br>
        <strong>Critical:</strong> {evaluation.get("critical_findings", 0)}
    </div>
    <p><em>Generated at: {datetime.utcnow().isoformat()}</em></p>
</body>
</html>
"""
        return StreamingResponse(
            iter([html_content]),
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename=report-{evaluation_id}.html"
            }
        )
    
    # PDF generation requires additional libraries
    raise HTTPException(
        status_code=501, 
        detail="PDF format requires weasyprint or reportlab. Use json or html format."
    )


@router.get("/{evaluation_id}/artifacts")
async def list_evaluation_artifacts(evaluation_id: UUID) -> dict[str, Any]:
    """
    List all artifacts generated by an evaluation.
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = _evaluations_db[evaluation_id]
    workflow_name = evaluation.get("workflow_name")
    
    # List artifacts from Argo workflow
    argo_service = get_argo_service()
    
    try:
        artifacts = await argo_service.list_workflow_artifacts(workflow_name)
        return {
            "evaluation_id": str(evaluation_id),
            "workflow_name": workflow_name,
            "artifacts": artifacts,
        }
    except Exception as e:
        # Return placeholder if Argo unavailable
        return {
            "evaluation_id": str(evaluation_id),
            "workflow_name": workflow_name,
            "artifacts": [
                {
                    "name": "privacy_pillar_results.json",
                    "node": "evaluate-privacy",
                    "size_bytes": 12345,
                    "created_at": "2026-01-15T10:30:00Z",
                },
                {
                    "name": "toxicity_pillar_results.json",
                    "node": "evaluate-toxicity",
                    "size_bytes": 8765,
                    "created_at": "2026-01-15T10:31:00Z",
                },
                {
                    "name": "full_report.json",
                    "node": "generate-report",
                    "size_bytes": 125000,
                    "created_at": "2026-01-15T10:35:00Z",
                },
            ],
            "error": str(e),
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
    
    evaluation = _evaluations_db[evaluation_id]
    workflow_name = evaluation.get("workflow_name")
    
    # Download artifact from Argo
    argo_service = get_argo_service()
    
    try:
        artifact_data = await argo_service.get_workflow_artifact(
            workflow_name, 
            artifact_name
        )
        
        # Determine content type
        content_type = "application/octet-stream"
        if artifact_name.endswith(".json"):
            content_type = "application/json"
        elif artifact_name.endswith(".pdf"):
            content_type = "application/pdf"
        elif artifact_name.endswith(".html"):
            content_type = "text/html"
        
        return StreamingResponse(
            iter([artifact_data]),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={artifact_name}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact not found or unavailable: {str(e)}"
        )


@router.get("/{evaluation_id}/logs")
async def get_evaluation_logs(
    evaluation_id: UUID,
    step: Optional[str] = None,
    tail: int = Query(default=100, ge=1, le=10000),
) -> dict[str, Any]:
    """
    Get logs from an evaluation workflow.
    """
    if evaluation_id not in _evaluations_db:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    evaluation = _evaluations_db[evaluation_id]
    workflow_name = evaluation.get("workflow_name")
    
    # Get logs from Argo
    argo_service = get_argo_service()
    
    try:
        logs = await argo_service.get_workflow_logs(
            workflow_name,
            pod_name=step,
            container="main",
            tail_lines=tail,
        )
        
        return {
            "evaluation_id": str(evaluation_id),
            "workflow_name": workflow_name,
            "step": step,
            "logs": logs,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching logs: {str(e)}"
        )


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
    
    # Resubmit Argo workflow with same config
    eval_service = get_evaluation_workflow_service()
    
    try:
        workflow_status = await eval_service.submit_evaluation(
            model_id=str(evaluation["model_id"]),
            evaluation_type=evaluation["evaluation_type"],
            config=evaluation.get("config", {}),
            pillars=evaluation.get("config", {}).get("pillars"),
        )
        
        new_evaluation_id = uuid4()
        now = datetime.utcnow().isoformat()
        
        # Create new evaluation record
        new_evaluation = {
            "id": new_evaluation_id,
            "model_id": evaluation["model_id"],
            "workflow_name": workflow_status.workflow_name,
            "evaluation_type": evaluation["evaluation_type"],
            "status": workflow_status.phase.lower(),
            "progress": 0.0,
            "overall_score": None,
            "risk_status": None,
            "findings_count": 0,
            "critical_findings": 0,
            "created_at": now,
            "started_at": now,
            "completed_at": None,
            "triggered_by": f"retry:{evaluation_id}",
            "config": evaluation.get("config", {}),
            "pillar_results": [],
        }
        
        _evaluations_db[new_evaluation_id] = new_evaluation
        
        return {
            "evaluation_id": str(new_evaluation_id),
            "original_evaluation_id": str(evaluation_id),
            "workflow_name": workflow_status.workflow_name,
            "status": "pending",
            "message": "Evaluation retry submitted",
            "created_at": now,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrying evaluation: {str(e)}"
        )
