"""
Workflow Templates

Argo Workflow templates for GuardStack evaluations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from uuid import UUID


class EvaluationType(str, Enum):
    """Types of evaluations."""
    PREDICTIVE = "predictive"
    GENAI = "genai"
    SPM = "spm"
    AGENTIC = "agentic"


@dataclass
class WorkflowParameter:
    """Workflow parameter definition."""
    name: str
    value: Any
    description: str = ""


@dataclass
class WorkflowTemplate:
    """Base workflow template."""
    name: str
    evaluation_type: EvaluationType
    parameters: list[WorkflowParameter] = field(default_factory=list)
    
    def to_argo_spec(self) -> dict[str, Any]:
        """Convert to Argo Workflow specification."""
        raise NotImplementedError


@dataclass
class PredictiveEvaluationTemplate(WorkflowTemplate):
    """
    Template for predictive ML model evaluations.
    
    Runs all 8 pillar evaluations in a DAG pattern.
    """
    
    def __init__(
        self,
        model_id: UUID,
        dataset_path: str,
        pillars: Optional[list[str]] = None,
    ):
        self.name = "predictive-evaluation"
        self.evaluation_type = EvaluationType.PREDICTIVE
        self.model_id = model_id
        self.dataset_path = dataset_path
        self.pillars = pillars or [
            "fairness",
            "explainability",
            "robustness",
            "transparency",
            "privacy",
            "accountability",
            "safety",
            "human_oversight",
        ]
        self.parameters = [
            WorkflowParameter("model_id", str(model_id), "Model UUID"),
            WorkflowParameter("dataset_path", dataset_path, "Path to evaluation dataset"),
            WorkflowParameter("pillars", ",".join(self.pillars), "Pillars to evaluate"),
        ]
    
    def to_argo_spec(self) -> dict[str, Any]:
        """Generate Argo Workflow spec for predictive evaluation."""
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "generateName": f"predictive-eval-{self.model_id}-",
                "labels": {
                    "guardstack.io/evaluation-type": "predictive",
                    "guardstack.io/model-id": str(self.model_id),
                },
            },
            "spec": {
                "entrypoint": "predictive-evaluation",
                "arguments": {
                    "parameters": [
                        {"name": p.name, "value": str(p.value)}
                        for p in self.parameters
                    ],
                },
                "templates": [
                    {
                        "name": "predictive-evaluation",
                        "dag": {
                            "tasks": [
                                *[
                                    {
                                        "name": f"evaluate-{pillar}",
                                        "template": "pillar-evaluation",
                                        "arguments": {
                                            "parameters": [
                                                {"name": "pillar", "value": pillar},
                                                {"name": "model_id", "value": "{{workflow.parameters.model_id}}"},
                                                {"name": "dataset_path", "value": "{{workflow.parameters.dataset_path}}"},
                                            ],
                                        },
                                    }
                                    for pillar in self.pillars
                                ],
                                {
                                    "name": "aggregate-results",
                                    "template": "aggregate",
                                    "dependencies": [f"evaluate-{p}" for p in self.pillars],
                                    "arguments": {
                                        "parameters": [
                                            {"name": "model_id", "value": "{{workflow.parameters.model_id}}"},
                                        ],
                                    },
                                },
                            ],
                        },
                    },
                    {
                        "name": "pillar-evaluation",
                        "inputs": {
                            "parameters": [
                                {"name": "pillar"},
                                {"name": "model_id"},
                                {"name": "dataset_path"},
                            ],
                        },
                        "container": {
                            "image": "guardstack/evaluator:latest",
                            "command": ["python", "-m", "guardstack.predictive.cli"],
                            "args": [
                                "--pillar", "{{inputs.parameters.pillar}}",
                                "--model-id", "{{inputs.parameters.model_id}}",
                                "--dataset", "{{inputs.parameters.dataset_path}}",
                            ],
                            "resources": {
                                "requests": {
                                    "memory": "2Gi",
                                    "cpu": "1",
                                },
                                "limits": {
                                    "memory": "8Gi",
                                    "cpu": "4",
                                },
                            },
                        },
                        "outputs": {
                            "artifacts": [
                                {
                                    "name": "pillar-result",
                                    "path": "/tmp/result.json",
                                    "s3": {
                                        "key": "evaluations/{{workflow.parameters.model_id}}/{{inputs.parameters.pillar}}.json",
                                    },
                                },
                            ],
                        },
                    },
                    {
                        "name": "aggregate",
                        "inputs": {
                            "parameters": [
                                {"name": "model_id"},
                            ],
                        },
                        "container": {
                            "image": "guardstack/evaluator:latest",
                            "command": ["python", "-m", "guardstack.scoring.cli"],
                            "args": [
                                "--model-id", "{{inputs.parameters.model_id}}",
                                "--aggregate",
                            ],
                        },
                    },
                ],
            },
        }


@dataclass
class GenAIEvaluationTemplate(WorkflowTemplate):
    """
    Template for GenAI model evaluations.
    
    Runs 4-pillar evaluations with Garak integration.
    """
    
    def __init__(
        self,
        model_id: UUID,
        connector_id: str,
        probes: Optional[list[str]] = None,
    ):
        self.name = "genai-evaluation"
        self.evaluation_type = EvaluationType.GENAI
        self.model_id = model_id
        self.connector_id = connector_id
        self.probes = probes or []
        self.parameters = [
            WorkflowParameter("model_id", str(model_id), "Model UUID"),
            WorkflowParameter("connector_id", connector_id, "Connector identifier"),
            WorkflowParameter("probes", ",".join(self.probes), "Garak probes to run"),
        ]
    
    def to_argo_spec(self) -> dict[str, Any]:
        """Generate Argo Workflow spec for GenAI evaluation."""
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "generateName": f"genai-eval-{self.model_id}-",
                "labels": {
                    "guardstack.io/evaluation-type": "genai",
                    "guardstack.io/model-id": str(self.model_id),
                },
            },
            "spec": {
                "entrypoint": "genai-evaluation",
                "arguments": {
                    "parameters": [
                        {"name": p.name, "value": str(p.value)}
                        for p in self.parameters
                    ],
                },
                "templates": [
                    {
                        "name": "genai-evaluation",
                        "dag": {
                            "tasks": [
                                {
                                    "name": "evaluate-content-safety",
                                    "template": "genai-pillar",
                                    "arguments": {
                                        "parameters": [
                                            {"name": "pillar", "value": "content_safety"},
                                        ],
                                    },
                                },
                                {
                                    "name": "evaluate-prompt-injection",
                                    "template": "genai-pillar",
                                    "arguments": {
                                        "parameters": [
                                            {"name": "pillar", "value": "prompt_injection"},
                                        ],
                                    },
                                },
                                {
                                    "name": "evaluate-hallucination",
                                    "template": "genai-pillar",
                                    "arguments": {
                                        "parameters": [
                                            {"name": "pillar", "value": "hallucination"},
                                        ],
                                    },
                                },
                                {
                                    "name": "evaluate-bias-toxicity",
                                    "template": "genai-pillar",
                                    "arguments": {
                                        "parameters": [
                                            {"name": "pillar", "value": "bias_toxicity"},
                                        ],
                                    },
                                },
                                {
                                    "name": "run-garak",
                                    "template": "garak-probes",
                                    "when": "{{workflow.parameters.probes}} != ''",
                                },
                                {
                                    "name": "aggregate-results",
                                    "template": "aggregate",
                                    "dependencies": [
                                        "evaluate-content-safety",
                                        "evaluate-prompt-injection",
                                        "evaluate-hallucination",
                                        "evaluate-bias-toxicity",
                                    ],
                                },
                            ],
                        },
                    },
                    {
                        "name": "genai-pillar",
                        "inputs": {
                            "parameters": [
                                {"name": "pillar"},
                            ],
                        },
                        "container": {
                            "image": "guardstack/genai-evaluator:latest",
                            "command": ["python", "-m", "guardstack.genai.cli"],
                            "args": [
                                "--pillar", "{{inputs.parameters.pillar}}",
                                "--model-id", "{{workflow.parameters.model_id}}",
                                "--connector", "{{workflow.parameters.connector_id}}",
                            ],
                            "resources": {
                                "requests": {
                                    "memory": "4Gi",
                                    "cpu": "2",
                                },
                                "limits": {
                                    "memory": "16Gi",
                                    "cpu": "8",
                                    "nvidia.com/gpu": "1",
                                },
                            },
                        },
                    },
                    {
                        "name": "garak-probes",
                        "container": {
                            "image": "guardstack/garak:latest",
                            "command": ["python", "-m", "garak"],
                            "args": [
                                "--model-type", "rest",
                                "--model-name", "{{workflow.parameters.connector_id}}",
                                "-p", "{{workflow.parameters.probes}}",
                                "--report", "json",
                            ],
                            "resources": {
                                "requests": {
                                    "memory": "8Gi",
                                    "cpu": "4",
                                },
                            },
                        },
                    },
                    {
                        "name": "aggregate",
                        "container": {
                            "image": "guardstack/evaluator:latest",
                            "command": ["python", "-m", "guardstack.scoring.cli"],
                            "args": [
                                "--model-id", "{{workflow.parameters.model_id}}",
                                "--type", "genai",
                                "--aggregate",
                            ],
                        },
                    },
                ],
            },
        }


@dataclass
class SPMScanTemplate(WorkflowTemplate):
    """
    Template for Security Posture Management scans.
    
    Scans model artifacts and infrastructure for security issues.
    """
    
    def __init__(
        self,
        target_path: str,
        scan_types: Optional[list[str]] = None,
    ):
        self.name = "spm-scan"
        self.evaluation_type = EvaluationType.SPM
        self.target_path = target_path
        self.scan_types = scan_types or [
            "model_artifacts",
            "dependencies",
            "configurations",
            "infrastructure",
        ]
        self.parameters = [
            WorkflowParameter("target_path", target_path, "Path to scan"),
            WorkflowParameter("scan_types", ",".join(self.scan_types), "Types of scans"),
        ]
    
    def to_argo_spec(self) -> dict[str, Any]:
        """Generate Argo Workflow spec for SPM scan."""
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "generateName": "spm-scan-",
                "labels": {
                    "guardstack.io/evaluation-type": "spm",
                },
            },
            "spec": {
                "entrypoint": "spm-scan",
                "arguments": {
                    "parameters": [
                        {"name": p.name, "value": str(p.value)}
                        for p in self.parameters
                    ],
                },
                "templates": [
                    {
                        "name": "spm-scan",
                        "dag": {
                            "tasks": [
                                *[
                                    {
                                        "name": f"scan-{scan_type.replace('_', '-')}",
                                        "template": "security-scan",
                                        "arguments": {
                                            "parameters": [
                                                {"name": "scan_type", "value": scan_type},
                                            ],
                                        },
                                    }
                                    for scan_type in self.scan_types
                                ],
                                {
                                    "name": "generate-report",
                                    "template": "report",
                                    "dependencies": [
                                        f"scan-{s.replace('_', '-')}"
                                        for s in self.scan_types
                                    ],
                                },
                            ],
                        },
                    },
                    {
                        "name": "security-scan",
                        "inputs": {
                            "parameters": [
                                {"name": "scan_type"},
                            ],
                        },
                        "container": {
                            "image": "guardstack/spm-scanner:latest",
                            "command": ["python", "-m", "guardstack.spm.cli"],
                            "args": [
                                "--scan-type", "{{inputs.parameters.scan_type}}",
                                "--target", "{{workflow.parameters.target_path}}",
                            ],
                        },
                    },
                    {
                        "name": "report",
                        "container": {
                            "image": "guardstack/spm-scanner:latest",
                            "command": ["python", "-m", "guardstack.spm.cli"],
                            "args": [
                                "--generate-report",
                                "--format", "json",
                            ],
                        },
                    },
                ],
            },
        }


@dataclass
class AgenticEvaluationTemplate(WorkflowTemplate):
    """
    Template for agentic AI evaluations.
    
    Evaluates agent behavior in sandboxed environments.
    """
    
    def __init__(
        self,
        agent_id: UUID,
        scenarios: list[str],
        sandbox_config: Optional[dict[str, Any]] = None,
    ):
        self.name = "agentic-evaluation"
        self.evaluation_type = EvaluationType.AGENTIC
        self.agent_id = agent_id
        self.scenarios = scenarios
        self.sandbox_config = sandbox_config or {}
        self.parameters = [
            WorkflowParameter("agent_id", str(agent_id), "Agent UUID"),
            WorkflowParameter("scenarios", ",".join(scenarios), "Test scenarios"),
        ]
    
    def to_argo_spec(self) -> dict[str, Any]:
        """Generate Argo Workflow spec for agentic evaluation."""
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "generateName": f"agentic-eval-{self.agent_id}-",
                "labels": {
                    "guardstack.io/evaluation-type": "agentic",
                    "guardstack.io/agent-id": str(self.agent_id),
                },
            },
            "spec": {
                "entrypoint": "agentic-evaluation",
                "arguments": {
                    "parameters": [
                        {"name": p.name, "value": str(p.value)}
                        for p in self.parameters
                    ],
                },
                "securityContext": {
                    "runAsNonRoot": True,
                    "runAsUser": 1000,
                },
                "templates": [
                    {
                        "name": "agentic-evaluation",
                        "dag": {
                            "tasks": [
                                {
                                    "name": "setup-sandbox",
                                    "template": "sandbox-setup",
                                },
                                *[
                                    {
                                        "name": f"scenario-{i}",
                                        "template": "run-scenario",
                                        "dependencies": ["setup-sandbox"],
                                        "arguments": {
                                            "parameters": [
                                                {"name": "scenario", "value": scenario},
                                            ],
                                        },
                                    }
                                    for i, scenario in enumerate(self.scenarios)
                                ],
                                {
                                    "name": "evaluate-behavior",
                                    "template": "behavior-analysis",
                                    "dependencies": [
                                        f"scenario-{i}"
                                        for i in range(len(self.scenarios))
                                    ],
                                },
                                {
                                    "name": "cleanup-sandbox",
                                    "template": "sandbox-cleanup",
                                    "dependencies": ["evaluate-behavior"],
                                },
                            ],
                        },
                    },
                    {
                        "name": "sandbox-setup",
                        "container": {
                            "image": "guardstack/agentic-sandbox:latest",
                            "command": ["python", "-m", "guardstack.agentic.sandbox"],
                            "args": ["--setup"],
                            "securityContext": {
                                "capabilities": {
                                    "drop": ["ALL"],
                                },
                                "readOnlyRootFilesystem": True,
                            },
                        },
                    },
                    {
                        "name": "run-scenario",
                        "inputs": {
                            "parameters": [
                                {"name": "scenario"},
                            ],
                        },
                        "container": {
                            "image": "guardstack/agentic-evaluator:latest",
                            "command": ["python", "-m", "guardstack.agentic.cli"],
                            "args": [
                                "--agent-id", "{{workflow.parameters.agent_id}}",
                                "--scenario", "{{inputs.parameters.scenario}}",
                            ],
                            "securityContext": {
                                "capabilities": {
                                    "drop": ["ALL"],
                                },
                            },
                        },
                    },
                    {
                        "name": "behavior-analysis",
                        "container": {
                            "image": "guardstack/agentic-evaluator:latest",
                            "command": ["python", "-m", "guardstack.agentic.cli"],
                            "args": [
                                "--agent-id", "{{workflow.parameters.agent_id}}",
                                "--analyze",
                            ],
                        },
                    },
                    {
                        "name": "sandbox-cleanup",
                        "container": {
                            "image": "guardstack/agentic-sandbox:latest",
                            "command": ["python", "-m", "guardstack.agentic.sandbox"],
                            "args": ["--cleanup"],
                        },
                    },
                ],
            },
        }


# Template factory
def create_workflow_template(
    evaluation_type: EvaluationType,
    **kwargs,
) -> WorkflowTemplate:
    """
    Factory function to create workflow templates.
    
    Args:
        evaluation_type: Type of evaluation
        **kwargs: Template-specific parameters
        
    Returns:
        WorkflowTemplate instance
    """
    templates = {
        EvaluationType.PREDICTIVE: PredictiveEvaluationTemplate,
        EvaluationType.GENAI: GenAIEvaluationTemplate,
        EvaluationType.SPM: SPMScanTemplate,
        EvaluationType.AGENTIC: AgenticEvaluationTemplate,
    }
    
    template_class = templates.get(evaluation_type)
    if not template_class:
        raise ValueError(f"Unknown evaluation type: {evaluation_type}")
    
    return template_class(**kwargs)
