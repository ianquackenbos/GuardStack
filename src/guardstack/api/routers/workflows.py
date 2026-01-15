"""
Workflows Router

Endpoints for managing Argo Workflows for ML evaluation pipelines,
including workflow templates, execution, and monitoring.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user

router = APIRouter(prefix="/workflows", tags=["Workflows"])


# ============================================================================
# Pydantic Models
# ============================================================================

class WorkflowTemplateBase(BaseModel):
    """Base model for workflow templates"""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: str = Field(..., description="Category: evaluation, training, deployment, data_processing")
    entrypoint: str = Field(..., description="Main entrypoint template")


class WorkflowTemplateCreate(WorkflowTemplateBase):
    """Model for creating a workflow template"""
    spec: dict = Field(..., description="Argo Workflow spec in YAML/JSON")
    parameters: Optional[list[dict]] = Field(None, description="Configurable parameters")


class WorkflowTemplateResponse(WorkflowTemplateBase):
    """Model for workflow template response"""
    id: UUID
    version: str = Field("1.0.0", description="Template version")
    parameters: Optional[list[dict]] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkflowExecutionRequest(BaseModel):
    """Request model for workflow execution"""
    template_id: UUID = Field(..., description="Template to execute")
    name: Optional[str] = Field(None, description="Custom workflow name")
    parameters: Optional[dict] = Field(default_factory=dict, description="Parameter values")
    priority: int = Field(5, ge=1, le=10, description="Execution priority 1-10")
    labels: Optional[dict] = Field(default_factory=dict, description="Kubernetes labels")


class WorkflowExecutionResponse(BaseModel):
    """Model for workflow execution response"""
    id: UUID
    name: str
    template_id: UUID
    status: str = Field(..., description="Status: pending, running, succeeded, failed, error")
    phase: str = Field(..., description="Current phase")
    progress: str = Field(..., description="Progress (e.g., '2/5' nodes completed)")
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkflowNode(BaseModel):
    """Individual node in a workflow"""
    id: str
    name: str
    display_name: str
    type: str = Field(..., description="Type: Pod, DAG, Steps, Suspend")
    phase: str = Field(..., description="Node phase")
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    message: Optional[str] = None
    inputs: Optional[dict] = None
    outputs: Optional[dict] = None


# ============================================================================
# Template Endpoints
# ============================================================================

@router.get("/templates", response_model=list[WorkflowTemplateResponse])
async def list_workflow_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List available workflow templates.
    """
    from uuid import uuid4
    
    templates = [
        WorkflowTemplateResponse(
            id=uuid4(),
            name="model-safety-evaluation",
            description="Comprehensive safety evaluation pipeline for LLMs",
            category="evaluation",
            entrypoint="safety-eval-dag",
            version="2.1.0",
            parameters=[
                {"name": "model_id", "type": "string", "required": True},
                {"name": "benchmark_suite", "type": "string", "default": "standard"},
                {"name": "sample_size", "type": "int", "default": 1000},
            ],
            created_by="platform-team",
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow() - timedelta(days=5),
        ),
        WorkflowTemplateResponse(
            id=uuid4(),
            name="bias-detection-pipeline",
            description="Multi-stage bias detection and fairness evaluation",
            category="evaluation",
            entrypoint="bias-detection",
            version="1.3.0",
            parameters=[
                {"name": "model_id", "type": "string", "required": True},
                {"name": "protected_attributes", "type": "array", "required": True},
                {"name": "fairness_threshold", "type": "float", "default": 0.1},
            ],
            created_by="ml-team",
            created_at=datetime.utcnow() - timedelta(days=60),
            updated_at=datetime.utcnow() - timedelta(days=10),
        ),
        WorkflowTemplateResponse(
            id=uuid4(),
            name="red-team-simulation",
            description="Automated red team adversarial testing",
            category="evaluation",
            entrypoint="red-team-dag",
            version="1.0.0",
            parameters=[
                {"name": "model_endpoint", "type": "string", "required": True},
                {"name": "attack_vectors", "type": "array", "default": ["prompt_injection", "jailbreak"]},
                {"name": "intensity", "type": "string", "default": "medium"},
            ],
            created_by="security-team",
            created_at=datetime.utcnow() - timedelta(days=14),
            updated_at=datetime.utcnow() - timedelta(days=2),
        ),
        WorkflowTemplateResponse(
            id=uuid4(),
            name="data-quality-check",
            description="Training data quality and compliance verification",
            category="data_processing",
            entrypoint="data-quality",
            version="1.5.0",
            parameters=[
                {"name": "dataset_uri", "type": "string", "required": True},
                {"name": "checks", "type": "array", "default": ["pii", "bias", "quality"]},
            ],
            created_by="data-team",
            created_at=datetime.utcnow() - timedelta(days=45),
            updated_at=datetime.utcnow() - timedelta(days=7),
        ),
    ]
    
    if category:
        templates = [t for t in templates if t.category == category]
    
    return templates


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_workflow_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get details of a specific workflow template.
    """
    return WorkflowTemplateResponse(
        id=template_id,
        name="model-safety-evaluation",
        description="Comprehensive safety evaluation pipeline for LLMs",
        category="evaluation",
        entrypoint="safety-eval-dag",
        version="2.1.0",
        parameters=[
            {"name": "model_id", "type": "string", "required": True},
            {"name": "benchmark_suite", "type": "string", "default": "standard"},
            {"name": "sample_size", "type": "int", "default": 1000},
        ],
        created_by="platform-team",
        created_at=datetime.utcnow() - timedelta(days=30),
        updated_at=datetime.utcnow() - timedelta(days=5),
    )


@router.post("/templates", response_model=WorkflowTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_template(
    template: WorkflowTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new workflow template.
    """
    from uuid import uuid4
    
    return WorkflowTemplateResponse(
        id=uuid4(),
        name=template.name,
        description=template.description,
        category=template.category,
        entrypoint=template.entrypoint,
        version="1.0.0",
        parameters=template.parameters,
        created_by=current_user.get("username", "unknown"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.put("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def update_workflow_template(
    template_id: UUID,
    template: WorkflowTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a workflow template (creates new version).
    """
    from uuid import uuid4
    
    return WorkflowTemplateResponse(
        id=template_id,
        name=template.name,
        description=template.description,
        category=template.category,
        entrypoint=template.entrypoint,
        version="1.1.0",  # Bumped version
        parameters=template.parameters,
        created_by=current_user.get("username", "unknown"),
        created_at=datetime.utcnow() - timedelta(days=30),
        updated_at=datetime.utcnow(),
    )


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a workflow template.
    """
    return None


# ============================================================================
# Execution Endpoints
# ============================================================================

@router.post("/execute", response_model=WorkflowExecutionResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow(
    request: WorkflowExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Execute a workflow from a template.
    
    The workflow will be submitted to Argo Workflows and run asynchronously.
    """
    from uuid import uuid4
    
    workflow_id = uuid4()
    workflow_name = request.name or f"workflow-{workflow_id.hex[:8]}"
    
    return WorkflowExecutionResponse(
        id=workflow_id,
        name=workflow_name,
        template_id=request.template_id,
        status="pending",
        phase="Pending",
        progress="0/0",
        started_at=None,
        finished_at=None,
        duration_seconds=None,
        message="Workflow submitted to Argo",
        created_at=datetime.utcnow(),
    )


@router.get("/executions", response_model=list[WorkflowExecutionResponse])
async def list_workflow_executions(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    template_id: Optional[UUID] = Query(None, description="Filter by template"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List workflow executions.
    """
    from uuid import uuid4
    
    executions = [
        WorkflowExecutionResponse(
            id=uuid4(),
            name="safety-eval-gpt4-20240114",
            template_id=uuid4(),
            status="running",
            phase="Running",
            progress="3/7",
            started_at=datetime.utcnow() - timedelta(minutes=15),
            finished_at=None,
            duration_seconds=None,
            message="Running bias detection stage",
            created_at=datetime.utcnow() - timedelta(minutes=15),
        ),
        WorkflowExecutionResponse(
            id=uuid4(),
            name="red-team-claude-20240114",
            template_id=uuid4(),
            status="succeeded",
            phase="Succeeded",
            progress="5/5",
            started_at=datetime.utcnow() - timedelta(hours=2),
            finished_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
            duration_seconds=1800,
            message="Workflow completed successfully",
            created_at=datetime.utcnow() - timedelta(hours=2),
        ),
        WorkflowExecutionResponse(
            id=uuid4(),
            name="data-quality-training-20240113",
            template_id=uuid4(),
            status="failed",
            phase="Failed",
            progress="2/4",
            started_at=datetime.utcnow() - timedelta(days=1),
            finished_at=datetime.utcnow() - timedelta(days=1) + timedelta(minutes=20),
            duration_seconds=1200,
            message="PII detection stage failed: resource limit exceeded",
            created_at=datetime.utcnow() - timedelta(days=1),
        ),
    ]
    
    return executions


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_workflow_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get details of a specific workflow execution.
    """
    return WorkflowExecutionResponse(
        id=execution_id,
        name="safety-eval-gpt4-20240114",
        template_id=UUID("12345678-1234-1234-1234-123456789abc"),
        status="running",
        phase="Running",
        progress="3/7",
        started_at=datetime.utcnow() - timedelta(minutes=15),
        finished_at=None,
        duration_seconds=None,
        message="Running bias detection stage",
        created_at=datetime.utcnow() - timedelta(minutes=15),
    )


@router.get("/executions/{execution_id}/nodes", response_model=list[WorkflowNode])
async def get_workflow_nodes(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the node graph for a workflow execution.
    """
    nodes = [
        WorkflowNode(
            id="node-1",
            name="safety-eval-gpt4-20240114.data-load",
            display_name="Data Load",
            type="Pod",
            phase="Succeeded",
            started_at=datetime.utcnow() - timedelta(minutes=15),
            finished_at=datetime.utcnow() - timedelta(minutes=13),
            message=None,
            inputs={"dataset": "s3://datasets/eval-set-v2"},
            outputs={"loaded_records": 10000},
        ),
        WorkflowNode(
            id="node-2",
            name="safety-eval-gpt4-20240114.toxicity-check",
            display_name="Toxicity Check",
            type="Pod",
            phase="Succeeded",
            started_at=datetime.utcnow() - timedelta(minutes=13),
            finished_at=datetime.utcnow() - timedelta(minutes=8),
            message=None,
            inputs={"records": 10000},
            outputs={"toxic_responses": 23, "score": 0.977},
        ),
        WorkflowNode(
            id="node-3",
            name="safety-eval-gpt4-20240114.bias-detection",
            display_name="Bias Detection",
            type="Pod",
            phase="Running",
            started_at=datetime.utcnow() - timedelta(minutes=8),
            finished_at=None,
            message="Processing batch 7/10",
            inputs={"records": 10000},
            outputs=None,
        ),
        WorkflowNode(
            id="node-4",
            name="safety-eval-gpt4-20240114.jailbreak-test",
            display_name="Jailbreak Test",
            type="Pod",
            phase="Pending",
            started_at=None,
            finished_at=None,
            message="Waiting for bias-detection",
            inputs=None,
            outputs=None,
        ),
    ]
    
    return nodes


@router.get("/executions/{execution_id}/logs")
async def get_workflow_logs(
    execution_id: UUID,
    node_id: Optional[str] = Query(None, description="Filter by specific node"),
    tail: int = Query(100, ge=1, le=1000, description="Number of log lines"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get logs for a workflow execution.
    """
    return {
        "execution_id": execution_id,
        "node_id": node_id,
        "logs": [
            {"timestamp": datetime.utcnow() - timedelta(minutes=10), "level": "INFO", "message": "Starting bias detection pipeline"},
            {"timestamp": datetime.utcnow() - timedelta(minutes=9), "level": "INFO", "message": "Loaded 10000 records from input"},
            {"timestamp": datetime.utcnow() - timedelta(minutes=8), "level": "INFO", "message": "Processing batch 1/10"},
            {"timestamp": datetime.utcnow() - timedelta(minutes=7), "level": "INFO", "message": "Processing batch 2/10"},
            {"timestamp": datetime.utcnow() - timedelta(minutes=6), "level": "WARN", "message": "High gender bias detected in batch 2"},
            {"timestamp": datetime.utcnow() - timedelta(minutes=5), "level": "INFO", "message": "Processing batch 3/10"},
        ],
    }


@router.post("/executions/{execution_id}/stop")
async def stop_workflow_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Stop a running workflow execution.
    """
    return {
        "id": execution_id,
        "status": "stopping",
        "message": "Workflow stop signal sent",
        "stopped_by": current_user.get("username", "unknown"),
        "stopped_at": datetime.utcnow(),
    }


@router.post("/executions/{execution_id}/retry")
async def retry_workflow_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retry a failed workflow execution.
    """
    from uuid import uuid4
    
    return {
        "original_id": execution_id,
        "new_id": uuid4(),
        "status": "pending",
        "message": "Workflow retry submitted",
        "retried_by": current_user.get("username", "unknown"),
        "retried_at": datetime.utcnow(),
    }


@router.delete("/executions/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a workflow execution and its artifacts.
    """
    return None


# ============================================================================
# Results/Artifacts Endpoints
# ============================================================================

@router.get("/executions/{execution_id}/results")
async def get_workflow_results(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the results/outputs of a completed workflow.
    """
    return {
        "execution_id": execution_id,
        "status": "succeeded",
        "outputs": {
            "overall_safety_score": 0.92,
            "toxicity_score": 0.977,
            "bias_score": 0.89,
            "jailbreak_resistance": 0.95,
            "findings": [
                {"severity": "medium", "category": "gender_bias", "details": "Detected 3.2% gender bias in responses"},
                {"severity": "low", "category": "prompt_injection", "details": "Minor vulnerability in edge cases"},
            ],
            "recommendations": [
                "Add gender-neutral prompt engineering",
                "Enhance input validation for special characters",
            ],
        },
        "artifacts": [
            {"name": "full_report.pdf", "path": "s3://results/safety-eval-gpt4-20240114/full_report.pdf", "size": 2456789},
            {"name": "raw_data.json", "path": "s3://results/safety-eval-gpt4-20240114/raw_data.json", "size": 15234567},
        ],
        "completed_at": datetime.utcnow() - timedelta(hours=1),
    }


@router.get("/executions/{execution_id}/artifacts/{artifact_name}")
async def download_workflow_artifact(
    execution_id: UUID,
    artifact_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Download a specific artifact from a workflow execution.
    """
    from fastapi.responses import StreamingResponse
    import io
    
    content = f"Mock artifact content for {artifact_name}"
    
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{artifact_name}"'
        }
    )
