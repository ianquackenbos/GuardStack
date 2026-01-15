"""
Argo Workflow Service

Service for managing Argo Workflows for model evaluations.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import httpx

from guardstack.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStatus:
    """Status of an Argo workflow."""
    name: str
    namespace: str
    phase: str  # Pending, Running, Succeeded, Failed, Error
    progress: str  # e.g., "2/5"
    started_at: Optional[str]
    finished_at: Optional[str]
    message: Optional[str] = None
    nodes: Optional[dict[str, Any]] = None


@dataclass
class WorkflowSubmitResult:
    """Result of workflow submission."""
    success: bool
    workflow_name: Optional[str]
    namespace: Optional[str]
    error: Optional[str] = None


class ArgoWorkflowService:
    """
    Service for interacting with Argo Workflows.
    
    Provides:
    - Workflow submission
    - Status tracking
    - Cancellation
    - Log retrieval
    """
    
    def __init__(
        self,
        server_url: Optional[str] = None,
        namespace: str = "argo",
        token: Optional[str] = None,
    ):
        self.server_url = server_url or getattr(settings, 'argo_server', 'http://argo-server.argo:2746')
        self.namespace = namespace
        self.token = token or getattr(settings, 'argo_token', None)
    
    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for Argo API requests."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def submit_workflow(
        self,
        template_name: str,
        parameters: dict[str, Any],
        labels: Optional[dict[str, str]] = None,
        workflow_name: Optional[str] = None,
    ) -> WorkflowSubmitResult:
        """
        Submit a workflow from a template.
        
        Args:
            template_name: Name of the WorkflowTemplate
            parameters: Workflow parameters
            labels: Optional labels
            workflow_name: Optional custom name (generated if not provided)
        
        Returns:
            WorkflowSubmitResult with workflow name or error
        """
        if workflow_name is None:
            workflow_name = f"{template_name}-{uuid4().hex[:8]}"
        
        workflow_spec = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "name": workflow_name,
                "namespace": self.namespace,
                "labels": labels or {},
            },
            "spec": {
                "workflowTemplateRef": {
                    "name": template_name,
                },
                "arguments": {
                    "parameters": [
                        {"name": k, "value": str(v) if not isinstance(v, str) else v}
                        for k, v in parameters.items()
                    ],
                },
            },
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.server_url}/api/v1/workflows/{self.namespace}",
                    headers=self._get_headers(),
                    json={"workflow": workflow_spec},
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return WorkflowSubmitResult(
                        success=True,
                        workflow_name=data.get("metadata", {}).get("name", workflow_name),
                        namespace=self.namespace,
                    )
                else:
                    logger.error(f"Workflow submission failed: {response.status_code} - {response.text}")
                    return WorkflowSubmitResult(
                        success=False,
                        workflow_name=None,
                        namespace=None,
                        error=f"API error: {response.status_code}",
                    )
        except Exception as e:
            logger.error(f"Workflow submission error: {e}")
            return WorkflowSubmitResult(
                success=False,
                workflow_name=None,
                namespace=None,
                error=str(e),
            )
    
    async def get_workflow_status(self, workflow_name: str) -> Optional[WorkflowStatus]:
        """
        Get the status of a workflow.
        
        Args:
            workflow_name: Name of the workflow
        
        Returns:
            WorkflowStatus or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.server_url}/api/v1/workflows/{self.namespace}/{workflow_name}",
                    headers=self._get_headers(),
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", {})
                    
                    # Calculate progress from nodes
                    nodes = status.get("nodes", {})
                    completed = sum(1 for n in nodes.values() if n.get("phase") == "Succeeded")
                    total = len(nodes) or 1
                    
                    return WorkflowStatus(
                        name=data.get("metadata", {}).get("name", workflow_name),
                        namespace=self.namespace,
                        phase=status.get("phase", "Unknown"),
                        progress=f"{completed}/{total}",
                        started_at=status.get("startedAt"),
                        finished_at=status.get("finishedAt"),
                        message=status.get("message"),
                        nodes=nodes,
                    )
                elif response.status_code == 404:
                    return None
                else:
                    logger.error(f"Failed to get workflow status: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return None
    
    async def cancel_workflow(self, workflow_name: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_name: Name of the workflow
        
        Returns:
            True if successfully cancelled
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.server_url}/api/v1/workflows/{self.namespace}/{workflow_name}/stop",
                    headers=self._get_headers(),
                )
                
                if response.status_code in [200, 202]:
                    logger.info(f"Cancelled workflow: {workflow_name}")
                    return True
                else:
                    logger.error(f"Failed to cancel workflow: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error cancelling workflow: {e}")
            return False
    
    async def retry_workflow(self, workflow_name: str) -> WorkflowSubmitResult:
        """
        Retry a failed workflow.
        
        Args:
            workflow_name: Name of the failed workflow
        
        Returns:
            WorkflowSubmitResult for the new workflow
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.server_url}/api/v1/workflows/{self.namespace}/{workflow_name}/retry",
                    headers=self._get_headers(),
                )
                
                if response.status_code in [200, 202]:
                    data = response.json()
                    return WorkflowSubmitResult(
                        success=True,
                        workflow_name=data.get("metadata", {}).get("name", workflow_name),
                        namespace=self.namespace,
                    )
                else:
                    return WorkflowSubmitResult(
                        success=False,
                        workflow_name=None,
                        namespace=None,
                        error=f"API error: {response.status_code}",
                    )
        except Exception as e:
            return WorkflowSubmitResult(
                success=False,
                workflow_name=None,
                namespace=None,
                error=str(e),
            )
    
    async def get_workflow_logs(
        self,
        workflow_name: str,
        pod_name: Optional[str] = None,
        container: str = "main",
    ) -> Optional[str]:
        """
        Get logs from a workflow.
        
        Args:
            workflow_name: Name of the workflow
            pod_name: Specific pod (optional)
            container: Container name
        
        Returns:
            Log content as string
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                params = {"logOptions.container": container}
                if pod_name:
                    params["podName"] = pod_name
                
                response = await client.get(
                    f"{self.server_url}/api/v1/workflows/{self.namespace}/{workflow_name}/log",
                    headers=self._get_headers(),
                    params=params,
                )
                
                if response.status_code == 200:
                    return response.text
                else:
                    logger.error(f"Failed to get logs: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting workflow logs: {e}")
            return None
    
    async def list_workflows(
        self,
        labels: Optional[dict[str, str]] = None,
        phases: Optional[list[str]] = None,
        limit: int = 100,
    ) -> list[WorkflowStatus]:
        """
        List workflows.
        
        Args:
            labels: Filter by labels
            phases: Filter by phase (Running, Succeeded, etc.)
            limit: Maximum number of workflows
        
        Returns:
            List of WorkflowStatus
        """
        try:
            params = {"listOptions.limit": str(limit)}
            if labels:
                selector = ",".join(f"{k}={v}" for k, v in labels.items())
                params["listOptions.labelSelector"] = selector
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.server_url}/api/v1/workflows/{self.namespace}",
                    headers=self._get_headers(),
                    params=params,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    workflows = []
                    
                    for item in data.get("items", []):
                        status = item.get("status", {})
                        phase = status.get("phase", "Unknown")
                        
                        # Filter by phase if specified
                        if phases and phase not in phases:
                            continue
                        
                        nodes = status.get("nodes", {})
                        completed = sum(1 for n in nodes.values() if n.get("phase") == "Succeeded")
                        total = len(nodes) or 1
                        
                        workflows.append(WorkflowStatus(
                            name=item.get("metadata", {}).get("name"),
                            namespace=self.namespace,
                            phase=phase,
                            progress=f"{completed}/{total}",
                            started_at=status.get("startedAt"),
                            finished_at=status.get("finishedAt"),
                            message=status.get("message"),
                        ))
                    
                    return workflows
                else:
                    logger.error(f"Failed to list workflows: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return []
    
    async def delete_workflow(self, workflow_name: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_name: Name of the workflow
        
        Returns:
            True if successfully deleted
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.server_url}/api/v1/workflows/{self.namespace}/{workflow_name}",
                    headers=self._get_headers(),
                )
                
                if response.status_code in [200, 204]:
                    logger.info(f"Deleted workflow: {workflow_name}")
                    return True
                else:
                    logger.error(f"Failed to delete workflow: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error deleting workflow: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Argo server is healthy."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.server_url}/api/v1/info",
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False


# Evaluation workflow templates
EVALUATION_TEMPLATES = {
    "genai": "guardstack-genai-evaluation",
    "predictive": "guardstack-predictive-evaluation",
    "spm": "guardstack-spm-evaluation",
    "agentic": "guardstack-agentic-evaluation",
}


class EvaluationWorkflowService:
    """Service for managing evaluation workflows."""
    
    def __init__(self, argo_service: Optional[ArgoWorkflowService] = None):
        self.argo = argo_service or ArgoWorkflowService()
    
    async def submit_evaluation(
        self,
        model_id: str,
        evaluation_type: str,
        config: Optional[dict[str, Any]] = None,
    ) -> WorkflowSubmitResult:
        """
        Submit an evaluation workflow.
        
        Args:
            model_id: ID of the model to evaluate
            evaluation_type: Type of evaluation (genai, predictive, spm, agentic)
            config: Optional evaluation configuration
        
        Returns:
            WorkflowSubmitResult
        """
        template_name = EVALUATION_TEMPLATES.get(evaluation_type)
        if not template_name:
            return WorkflowSubmitResult(
                success=False,
                workflow_name=None,
                namespace=None,
                error=f"Unknown evaluation type: {evaluation_type}",
            )
        
        parameters = {
            "model_id": model_id,
            "evaluation_type": evaluation_type,
            **(config or {}),
        }
        
        labels = {
            "guardstack/model-id": model_id,
            "guardstack/evaluation-type": evaluation_type,
        }
        
        return await self.argo.submit_workflow(
            template_name=template_name,
            parameters=parameters,
            labels=labels,
        )
    
    async def get_evaluation_status(
        self,
        workflow_name: str,
    ) -> Optional[dict[str, Any]]:
        """Get evaluation status with progress details."""
        status = await self.argo.get_workflow_status(workflow_name)
        
        if not status:
            return None
        
        # Parse progress
        progress_parts = status.progress.split("/")
        completed = int(progress_parts[0]) if progress_parts[0].isdigit() else 0
        total = int(progress_parts[1]) if len(progress_parts) > 1 and progress_parts[1].isdigit() else 1
        
        # Map phase to evaluation status
        status_map = {
            "Pending": "pending",
            "Running": "running",
            "Succeeded": "succeeded",
            "Failed": "failed",
            "Error": "error",
        }
        
        return {
            "workflow_name": status.name,
            "status": status_map.get(status.phase, "unknown"),
            "progress": (completed / total * 100) if total > 0 else 0,
            "phase": status.phase,
            "started_at": status.started_at,
            "finished_at": status.finished_at,
            "message": status.message,
            "completed_steps": completed,
            "total_steps": total,
        }


# Global service instances
_argo_service: Optional[ArgoWorkflowService] = None
_evaluation_workflow_service: Optional[EvaluationWorkflowService] = None


def get_argo_service() -> ArgoWorkflowService:
    """Get the global Argo service."""
    global _argo_service
    if _argo_service is None:
        _argo_service = ArgoWorkflowService()
    return _argo_service


def get_evaluation_workflow_service() -> EvaluationWorkflowService:
    """Get the global evaluation workflow service."""
    global _evaluation_workflow_service
    if _evaluation_workflow_service is None:
        _evaluation_workflow_service = EvaluationWorkflowService()
    return _evaluation_workflow_service
