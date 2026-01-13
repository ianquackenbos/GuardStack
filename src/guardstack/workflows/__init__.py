"""
GuardStack Workflows Module

Argo Workflows integration for DAG-based evaluations.
"""

from guardstack.workflows.argo_client import (
    ArgoWorkflowsClient,
    WorkflowPhase,
    WorkflowStatus,
    WorkflowSubmission,
    get_argo_client,
)
from guardstack.workflows.templates import (
    AgenticEvaluationTemplate,
    EvaluationType,
    GenAIEvaluationTemplate,
    PredictiveEvaluationTemplate,
    SPMScanTemplate,
    WorkflowParameter,
    WorkflowTemplate,
    create_workflow_template,
)

__all__ = [
    # Client
    "ArgoWorkflowsClient",
    "WorkflowPhase",
    "WorkflowStatus",
    "WorkflowSubmission",
    "get_argo_client",
    # Templates
    "EvaluationType",
    "WorkflowParameter",
    "WorkflowTemplate",
    "PredictiveEvaluationTemplate",
    "GenAIEvaluationTemplate",
    "SPMScanTemplate",
    "AgenticEvaluationTemplate",
    "create_workflow_template",
]
