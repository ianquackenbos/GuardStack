"""GuardStack API Routers."""

from guardstack.api.routers.models import router as models_router
from guardstack.api.routers.evaluations import router as evaluations_router
from guardstack.api.routers.dashboard import router as dashboard_router
from guardstack.api.routers.compliance import router as compliance_router
from guardstack.api.routers.guardrails import router as guardrails_router
from guardstack.api.routers.connectors import router as connectors_router
from guardstack.api.routers.websocket import router as websocket_router

# Re-export router modules
from guardstack.api.routers import (
    models,
    evaluations,
    dashboard,
    compliance,
    guardrails,
    connectors,
    websocket,
)

__all__ = [
    "models",
    "evaluations",
    "dashboard",
    "compliance",
    "guardrails",
    "connectors",
    "websocket",
    "models_router",
    "evaluations_router",
    "dashboard_router",
    "compliance_router",
    "guardrails_router",
    "connectors_router",
    "websocket_router",
]
