"""
Connectors API Router

Endpoints for managing model provider connections.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from guardstack.services.connectors import get_connector_service

router = APIRouter()


class ConnectorInfo(BaseModel):
    """Information about a connector type."""
    type: str
    name: str
    description: str
    category: str  # cloud, llm_provider, local, ml_platform, enterprise
    supported_model_types: list[str]
    required_config: list[str]
    optional_config: list[str]
    documentation_url: Optional[str]


class ConnectorTestRequest(BaseModel):
    """Request to test a connector configuration."""
    config: dict[str, Any]


class ConnectorTestResponse(BaseModel):
    """Response from connector test."""
    success: bool
    message: str
    latency_ms: Optional[int]
    available_models: list[str]
    error: Optional[str] = None


# Available connectors
CONNECTORS = {
    # LLM Providers
    "openai": ConnectorInfo(
        type="openai",
        name="OpenAI",
        description="Connect to OpenAI GPT models (GPT-4, GPT-3.5, etc.)",
        category="llm_provider",
        supported_model_types=["genai"],
        required_config=["api_key"],
        optional_config=["organization", "base_url"],
        documentation_url="https://platform.openai.com/docs",
    ),
    "anthropic": ConnectorInfo(
        type="anthropic",
        name="Anthropic",
        description="Connect to Anthropic Claude models",
        category="llm_provider",
        supported_model_types=["genai"],
        required_config=["api_key"],
        optional_config=["base_url"],
        documentation_url="https://docs.anthropic.com",
    ),
    "ollama": ConnectorInfo(
        type="ollama",
        name="Ollama",
        description="Connect to locally running Ollama instance",
        category="local",
        supported_model_types=["genai"],
        required_config=["endpoint"],
        optional_config=["timeout"],
        documentation_url="https://ollama.ai/docs",
    ),
    "huggingface": ConnectorInfo(
        type="huggingface",
        name="Hugging Face",
        description="Connect to Hugging Face Inference API or Hub models",
        category="ml_platform",
        supported_model_types=["genai", "predictive"],
        required_config=["api_key"],
        optional_config=["model_id", "endpoint"],
        documentation_url="https://huggingface.co/docs",
    ),
    "custom": ConnectorInfo(
        type="custom",
        name="Custom Endpoint",
        description="Connect to any REST API endpoint",
        category="custom",
        supported_model_types=["genai", "predictive", "agentic"],
        required_config=["endpoint"],
        optional_config=["headers", "auth_type", "api_key"],
        documentation_url=None,
    ),
}


@router.get("", response_model=list[ConnectorInfo])
async def list_connectors(
    category: Optional[str] = Query(default=None),
    model_type: Optional[str] = Query(default=None),
) -> list[ConnectorInfo]:
    """List available connector types."""
    connectors = list(CONNECTORS.values())
    if category:
        connectors = [c for c in connectors if c.category == category]
    if model_type:
        connectors = [c for c in connectors if model_type in c.supported_model_types]
    return connectors


@router.get("/{connector_type}", response_model=ConnectorInfo)
async def get_connector_info(connector_type: str) -> ConnectorInfo:
    """Get detailed information about a connector type."""
    if connector_type not in CONNECTORS:
        raise HTTPException(status_code=404, detail="Connector type not found")
    return CONNECTORS[connector_type]


@router.post("/{connector_type}/test", response_model=ConnectorTestResponse)
async def test_connector(
    connector_type: str,
    request: ConnectorTestRequest,
) -> ConnectorTestResponse:
    """Test a connector configuration."""
    if connector_type not in CONNECTORS:
        raise HTTPException(status_code=404, detail="Connector type not found")
    
    connector_info = CONNECTORS[connector_type]
    missing = [f for f in connector_info.required_config if f not in request.config]
    if missing:
        return ConnectorTestResponse(
            success=False,
            message=f"Missing required configuration: {', '.join(missing)}",
            latency_ms=None,
            available_models=[],
            error=f"Missing fields: {', '.join(missing)}",
        )
    
    connector_service = get_connector_service()
    result = await connector_service.test_connector(connector_type, request.config)
    
    return ConnectorTestResponse(
        success=result.success,
        message=result.message,
        latency_ms=result.latency_ms,
        available_models=result.available_models,
        error=result.error,
    )


@router.get("/{connector_type}/models")
async def list_available_models(
    connector_type: str,
    api_key: Optional[str] = Query(default=None),
    endpoint: Optional[str] = Query(default=None),
) -> dict[str, Any]:
    """List models available through a connector."""
    if connector_type not in CONNECTORS:
        raise HTTPException(status_code=404, detail="Connector type not found")
    
    config: dict[str, Any] = {}
    if api_key:
        config["api_key"] = api_key
    if endpoint:
        config["endpoint"] = endpoint
    
    connector_service = get_connector_service()
    models = await connector_service.list_models(connector_type, config)
    
    return {"connector_type": connector_type, "models": models}


@router.get("/health")
async def check_connectors_health() -> dict[str, Any]:
    """Check health of all configured connectors."""
    connector_service = get_connector_service()
    
    configured_connectors = [
        ("ollama", {"endpoint": "http://localhost:11434"}),
    ]
    
    health_statuses = await connector_service.check_all_health(configured_connectors)
    
    healthy_count = sum(1 for s in health_statuses if s.status == "healthy")
    degraded_count = sum(1 for s in health_statuses if s.status == "degraded")
    unhealthy_count = sum(1 for s in health_statuses if s.status == "unhealthy")
    
    return {
        "connectors": [
            {"type": s.type, "status": s.status, "latency_ms": s.latency_ms, "last_checked": s.last_checked, "message": s.message}
            for s in health_statuses
        ],
        "healthy_count": healthy_count,
        "degraded_count": degraded_count,
        "unhealthy_count": unhealthy_count,
    }
