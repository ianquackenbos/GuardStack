"""
Models API Router

Endpoints for registering and managing AI models.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from guardstack.models.core import ModelType, RiskStatus
from guardstack.services.argo import (
    get_evaluation_workflow_service,
    EvaluationWorkflowService,
)

router = APIRouter()


class ModelResponse(BaseModel):
    """Response model for registered models."""
    id: UUID
    name: str
    description: Optional[str]
    model_type: str
    connector_type: str
    version: Optional[str]
    tags: list[str]
    current_status: str
    current_score: Optional[float]
    trend: str
    created_at: str
    last_evaluated: Optional[str]
    owner: Optional[str]
    team: Optional[str]


class CreateModelRequest(BaseModel):
    """Request to register a new model."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    model_type: str = Field(..., pattern="^(predictive|genai|agentic)$")
    connector_type: str = Field(..., min_length=1)
    connector_config: dict[str, Any] = Field(default={})
    version: Optional[str] = None
    tags: list[str] = Field(default=[])
    owner: Optional[str] = None
    team: Optional[str] = None


class UpdateModelRequest(BaseModel):
    """Request to update a model."""
    name: Optional[str] = None
    description: Optional[str] = None
    connector_config: Optional[dict[str, Any]] = None
    version: Optional[str] = None
    tags: Optional[list[str]] = None
    owner: Optional[str] = None
    team: Optional[str] = None


class ModelsListResponse(BaseModel):
    """Response for listing models."""
    models: list[ModelResponse]
    total: int
    page: int
    page_size: int


class StartEvaluationRequest(BaseModel):
    """Request to start an evaluation."""
    pillars: Optional[list[str]] = None
    config: Optional[dict[str, Any]] = None


# In-memory storage for demo (replace with database)
_models_db: dict[UUID, dict] = {}


@router.get("", response_model=ModelsListResponse)
async def list_models(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    model_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> ModelsListResponse:
    """
    List all registered models.
    
    Supports filtering by model type, status, and search query.
    """
    models = list(_models_db.values())
    
    # Apply filters
    if model_type:
        models = [m for m in models if m["model_type"] == model_type]
    if status:
        models = [m for m in models if m["current_status"] == status]
    if search:
        search_lower = search.lower()
        models = [
            m for m in models 
            if search_lower in m["name"].lower() 
            or (m.get("description") and search_lower in m["description"].lower())
        ]
    
    total = len(models)
    
    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    models = models[start:end]
    
    return ModelsListResponse(
        models=[ModelResponse(**m) for m in models],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ModelResponse, status_code=201)
async def create_model(request: CreateModelRequest) -> ModelResponse:
    """
    Register a new AI model.
    
    Creates a new model entry in the registry with the specified
    connector configuration.
    """
    model_id = uuid4()
    now = datetime.utcnow().isoformat()
    
    model = {
        "id": model_id,
        "name": request.name,
        "description": request.description,
        "model_type": request.model_type,
        "connector_type": request.connector_type,
        "connector_config": request.connector_config,
        "version": request.version,
        "tags": request.tags,
        "current_status": RiskStatus.WARN.value,
        "current_score": None,
        "trend": "stable",
        "created_at": now,
        "last_evaluated": None,
        "owner": request.owner,
        "team": request.team,
    }
    
    _models_db[model_id] = model
    
    return ModelResponse(**model)


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: UUID) -> ModelResponse:
    """
    Get details for a specific model.
    """
    if model_id not in _models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return ModelResponse(**_models_db[model_id])


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(model_id: UUID, request: UpdateModelRequest) -> ModelResponse:
    """
    Update a registered model.
    """
    if model_id not in _models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = _models_db[model_id]
    
    # Update fields if provided
    if request.name is not None:
        model["name"] = request.name
    if request.description is not None:
        model["description"] = request.description
    if request.connector_config is not None:
        model["connector_config"] = request.connector_config
    if request.version is not None:
        model["version"] = request.version
    if request.tags is not None:
        model["tags"] = request.tags
    if request.owner is not None:
        model["owner"] = request.owner
    if request.team is not None:
        model["team"] = request.team
    
    return ModelResponse(**model)


@router.delete("/{model_id}", status_code=204)
async def delete_model(model_id: UUID) -> None:
    """
    Unregister a model.
    """
    if model_id not in _models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    del _models_db[model_id]


@router.post("/{model_id}/evaluate")
async def start_evaluation(
    model_id: UUID,
    evaluation_type: str = Query(..., pattern="^(predictive|genai|spm|agentic)$"),
    request: Optional[StartEvaluationRequest] = None,
) -> dict[str, Any]:
    """
    Start an evaluation workflow for a model.
    
    Triggers an Argo Workflow to evaluate the model based on
    the specified evaluation type (predictive, genai, spm, agentic).
    
    The workflow runs as a Kubernetes-native DAG with parallel pillar evaluation.
    """
    if model_id not in _models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = _models_db[model_id]
    
    # Get evaluation service
    eval_service = get_evaluation_workflow_service()
    
    # Prepare config
    config = request.config if request else {}
    pillars = request.pillars if request else None
    
    # Add model connector info to config
    config["connector_type"] = model.get("connector_type")
    config["connector_config"] = model.get("connector_config", {})
    
    try:
        # Submit Argo Workflow
        workflow_status = await eval_service.submit_evaluation(
            model_id=str(model_id),
            evaluation_type=evaluation_type,
            config=config,
            pillars=pillars,
        )
        
        # Update model last_evaluated
        model["last_evaluated"] = datetime.utcnow().isoformat()
        
        return {
            "evaluation_id": workflow_status.workflow_name,
            "model_id": str(model_id),
            "model_name": model["name"],
            "evaluation_type": evaluation_type,
            "workflow_name": workflow_status.workflow_name,
            "workflow_namespace": workflow_status.namespace,
            "status": workflow_status.phase.lower(),
            "pillars": pillars or eval_service._get_default_pillars(evaluation_type),
            "created_at": datetime.utcnow().isoformat(),
            "message": "Evaluation workflow submitted to Argo",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit evaluation workflow: {str(e)}"
        )


@router.get("/{model_id}/evaluations")
async def list_model_evaluations(
    model_id: UUID,
    limit: int = Query(default=10, ge=1, le=100),
) -> dict[str, Any]:
    """
    List recent evaluations for a model.
    """
    if model_id not in _models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Get evaluation workflow service to query Argo
    eval_service = get_evaluation_workflow_service()
    
    try:
        evaluations = await eval_service.list_model_evaluations(
            model_id=str(model_id),
            limit=limit,
        )
        
        return {
            "model_id": str(model_id),
            "evaluations": evaluations,
            "total": len(evaluations),
        }
    except Exception as e:
        # Return empty list if Argo unavailable
        return {
            "model_id": str(model_id),
            "evaluations": [],
            "total": 0,
            "error": str(e),
        }
