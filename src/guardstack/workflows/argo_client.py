"""
Argo Workflows Client

Client for submitting and monitoring Argo Workflows in Kubernetes.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

import httpx
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from guardstack.config import settings

logger = logging.getLogger(__name__)


class WorkflowPhase(str, Enum):
    """Argo Workflow execution phases."""
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    ERROR = "Error"
    SKIPPED = "Skipped"


@dataclass
class WorkflowStatus:
    """Status of an Argo Workflow."""
    name: str
    namespace: str
    phase: WorkflowPhase
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    progress: str = "0/0"
    message: str = ""
    nodes: dict[str, Any] = field(default_factory=dict)


@dataclass 
class WorkflowSubmission:
    """Result of workflow submission."""
    name: str
    namespace: str
    uid: str
    created_at: datetime


class ArgoWorkflowsClient:
    """
    Client for interacting with Argo Workflows.
    
    Supports both in-cluster and external configurations.
    """
    
    def __init__(
        self,
        namespace: str = "guardstack",
        in_cluster: bool = True,
        kubeconfig: Optional[str] = None,
        argo_server_url: Optional[str] = None,
    ):
        self.namespace = namespace
        self.argo_server_url = argo_server_url or settings.argo_server_url
        self._api_client: Optional[client.ApiClient] = None
        self._custom_api: Optional[client.CustomObjectsApi] = None
        
        # Load Kubernetes configuration
        try:
            if in_cluster:
                config.load_incluster_config()
            else:
                config.load_kube_config(config_file=kubeconfig)
            
            self._api_client = client.ApiClient()
            self._custom_api = client.CustomObjectsApi(self._api_client)
            logger.info("Kubernetes client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize K8s client: {e}")
            logger.info("Falling back to Argo Server API")
    
    async def submit_workflow(
        self,
        template_name: str,
        parameters: dict[str, Any],
        labels: Optional[dict[str, str]] = None,
        annotations: Optional[dict[str, str]] = None,
    ) -> WorkflowSubmission:
        """
        Submit a workflow from a WorkflowTemplate.
        
        Args:
            template_name: Name of the WorkflowTemplate to use
            parameters: Parameters to pass to the workflow
            labels: Additional labels for the workflow
            annotations: Additional annotations for the workflow
            
        Returns:
            WorkflowSubmission with workflow metadata
        """
        workflow_name = f"{template_name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        # Build workflow spec
        workflow_spec = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "name": workflow_name,
                "namespace": self.namespace,
                "labels": {
                    "app.kubernetes.io/name": "guardstack",
                    "app.kubernetes.io/component": "evaluation",
                    "guardstack.io/template": template_name,
                    **(labels or {}),
                },
                "annotations": annotations or {},
            },
            "spec": {
                "workflowTemplateRef": {
                    "name": template_name,
                },
                "arguments": {
                    "parameters": [
                        {"name": k, "value": str(v)}
                        for k, v in parameters.items()
                    ],
                },
            },
        }
        
        # Submit via Kubernetes API or Argo Server
        if self._custom_api:
            return await self._submit_via_k8s(workflow_spec)
        else:
            return await self._submit_via_argo_server(workflow_spec)
    
    async def _submit_via_k8s(
        self,
        workflow_spec: dict[str, Any]
    ) -> WorkflowSubmission:
        """Submit workflow via Kubernetes API."""
        try:
            result = self._custom_api.create_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="workflows",
                body=workflow_spec,
            )
            
            return WorkflowSubmission(
                name=result["metadata"]["name"],
                namespace=result["metadata"]["namespace"],
                uid=result["metadata"]["uid"],
                created_at=datetime.fromisoformat(
                    result["metadata"]["creationTimestamp"].replace("Z", "+00:00")
                ),
            )
        except ApiException as e:
            logger.error(f"Failed to submit workflow: {e}")
            raise
    
    async def _submit_via_argo_server(
        self,
        workflow_spec: dict[str, Any]
    ) -> WorkflowSubmission:
        """Submit workflow via Argo Server REST API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.argo_server_url}/api/v1/workflows/{self.namespace}",
                json=workflow_spec,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()
            
            return WorkflowSubmission(
                name=result["metadata"]["name"],
                namespace=result["metadata"]["namespace"],
                uid=result["metadata"]["uid"],
                created_at=datetime.fromisoformat(
                    result["metadata"]["creationTimestamp"].replace("Z", "+00:00")
                ),
            )
    
    async def get_workflow_status(
        self,
        workflow_name: str,
    ) -> WorkflowStatus:
        """
        Get current status of a workflow.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            WorkflowStatus with current state
        """
        if self._custom_api:
            return await self._get_status_via_k8s(workflow_name)
        else:
            return await self._get_status_via_argo_server(workflow_name)
    
    async def _get_status_via_k8s(
        self,
        workflow_name: str
    ) -> WorkflowStatus:
        """Get workflow status via Kubernetes API."""
        try:
            result = self._custom_api.get_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="workflows",
                name=workflow_name,
            )
            
            status = result.get("status", {})
            
            return WorkflowStatus(
                name=workflow_name,
                namespace=self.namespace,
                phase=WorkflowPhase(status.get("phase", "Pending")),
                started_at=datetime.fromisoformat(
                    status["startedAt"].replace("Z", "+00:00")
                ) if status.get("startedAt") else None,
                finished_at=datetime.fromisoformat(
                    status["finishedAt"].replace("Z", "+00:00")
                ) if status.get("finishedAt") else None,
                progress=status.get("progress", "0/0"),
                message=status.get("message", ""),
                nodes=status.get("nodes", {}),
            )
        except ApiException as e:
            logger.error(f"Failed to get workflow status: {e}")
            raise
    
    async def _get_status_via_argo_server(
        self,
        workflow_name: str
    ) -> WorkflowStatus:
        """Get workflow status via Argo Server REST API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.argo_server_url}/api/v1/workflows/{self.namespace}/{workflow_name}",
            )
            response.raise_for_status()
            result = response.json()
            
            status = result.get("status", {})
            
            return WorkflowStatus(
                name=workflow_name,
                namespace=self.namespace,
                phase=WorkflowPhase(status.get("phase", "Pending")),
                started_at=datetime.fromisoformat(
                    status["startedAt"].replace("Z", "+00:00")
                ) if status.get("startedAt") else None,
                finished_at=datetime.fromisoformat(
                    status["finishedAt"].replace("Z", "+00:00")
                ) if status.get("finishedAt") else None,
                progress=status.get("progress", "0/0"),
                message=status.get("message", ""),
                nodes=status.get("nodes", {}),
            )
    
    async def wait_for_completion(
        self,
        workflow_name: str,
        timeout_seconds: int = 3600,
        poll_interval: int = 5,
    ) -> WorkflowStatus:
        """
        Wait for a workflow to complete.
        
        Args:
            workflow_name: Name of the workflow
            timeout_seconds: Maximum time to wait
            poll_interval: Seconds between status checks
            
        Returns:
            Final WorkflowStatus
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status = await self.get_workflow_status(workflow_name)
            
            if status.phase in (
                WorkflowPhase.SUCCEEDED,
                WorkflowPhase.FAILED,
                WorkflowPhase.ERROR,
            ):
                return status
            
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                raise TimeoutError(
                    f"Workflow {workflow_name} did not complete within {timeout_seconds}s"
                )
            
            await asyncio.sleep(poll_interval)
    
    async def cancel_workflow(
        self,
        workflow_name: str,
    ) -> None:
        """
        Cancel a running workflow.
        
        Args:
            workflow_name: Name of the workflow to cancel
        """
        if self._custom_api:
            # Patch workflow to terminate
            patch = {
                "spec": {
                    "shutdown": "Terminate",
                }
            }
            self._custom_api.patch_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="workflows",
                name=workflow_name,
                body=patch,
            )
        else:
            async with httpx.AsyncClient() as client:
                await client.put(
                    f"{self.argo_server_url}/api/v1/workflows/{self.namespace}/{workflow_name}/terminate",
                )
        
        logger.info(f"Workflow {workflow_name} cancelled")
    
    async def delete_workflow(
        self,
        workflow_name: str,
    ) -> None:
        """
        Delete a workflow.
        
        Args:
            workflow_name: Name of the workflow to delete
        """
        if self._custom_api:
            self._custom_api.delete_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="workflows",
                name=workflow_name,
            )
        else:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{self.argo_server_url}/api/v1/workflows/{self.namespace}/{workflow_name}",
                )
        
        logger.info(f"Workflow {workflow_name} deleted")
    
    async def get_workflow_logs(
        self,
        workflow_name: str,
        node_id: Optional[str] = None,
        container: str = "main",
    ) -> str:
        """
        Get logs from a workflow or specific node.
        
        Args:
            workflow_name: Name of the workflow
            node_id: Specific node to get logs from (optional)
            container: Container name (default: main)
            
        Returns:
            Log content as string
        """
        if self.argo_server_url:
            async with httpx.AsyncClient() as client:
                params = {"container": container}
                if node_id:
                    params["podName"] = node_id
                
                response = await client.get(
                    f"{self.argo_server_url}/api/v1/workflows/{self.namespace}/{workflow_name}/log",
                    params=params,
                )
                response.raise_for_status()
                return response.text
        else:
            # Fall back to kubectl logs
            raise NotImplementedError(
                "Direct log retrieval requires Argo Server URL"
            )
    
    async def list_workflows(
        self,
        label_selector: Optional[str] = None,
        limit: int = 100,
    ) -> list[WorkflowStatus]:
        """
        List workflows in the namespace.
        
        Args:
            label_selector: Kubernetes label selector
            limit: Maximum number of workflows to return
            
        Returns:
            List of WorkflowStatus objects
        """
        workflows = []
        
        if self._custom_api:
            result = self._custom_api.list_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="workflows",
                label_selector=label_selector,
                limit=limit,
            )
            
            for item in result.get("items", []):
                status = item.get("status", {})
                workflows.append(WorkflowStatus(
                    name=item["metadata"]["name"],
                    namespace=self.namespace,
                    phase=WorkflowPhase(status.get("phase", "Pending")),
                    started_at=datetime.fromisoformat(
                        status["startedAt"].replace("Z", "+00:00")
                    ) if status.get("startedAt") else None,
                    finished_at=datetime.fromisoformat(
                        status["finishedAt"].replace("Z", "+00:00")
                    ) if status.get("finishedAt") else None,
                    progress=status.get("progress", "0/0"),
                ))
        
        return workflows


# Global client instance
_argo_client: Optional[ArgoWorkflowsClient] = None


def get_argo_client() -> ArgoWorkflowsClient:
    """Get or create the global Argo Workflows client."""
    global _argo_client
    if _argo_client is None:
        _argo_client = ArgoWorkflowsClient(
            namespace=settings.argo_namespace,
            in_cluster=settings.in_cluster,
            argo_server_url=settings.argo_server_url,
        )
    return _argo_client
