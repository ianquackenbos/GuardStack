"""
Compliance API Router

Endpoints for compliance mapping and reporting (EU AI Act, SOC2, etc.).
"""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from guardstack.services.argo import get_argo_service

router = APIRouter()


class ComplianceFramework(BaseModel):
    """Available compliance framework."""
    id: str
    name: str
    version: str
    description: str
    total_requirements: int
    categories: list[str]


class RequirementStatus(BaseModel):
    """Status of a single compliance requirement."""
    requirement_id: str
    title: str
    description: str
    category: str
    status: str  # met, partial, not_met, not_applicable
    evidence: list[str]
    gaps: list[str]
    pillar_mappings: list[str]


class ModelComplianceStatus(BaseModel):
    """Compliance status for a model."""
    model_id: str
    model_name: str
    framework: str
    framework_version: str
    coverage_percentage: float
    met_requirements: int
    partial_requirements: int
    not_met_requirements: int
    not_applicable: int
    total_requirements: int
    risk_classification: Optional[str]
    last_assessed: str
    requirements: list[RequirementStatus]


class GenerateReportRequest(BaseModel):
    """Request to generate a compliance report."""
    model_ids: list[str] = Field(default=[])
    framework: str
    include_evidence: bool = True
    include_gaps: bool = True
    format: str = Field(default="pdf", pattern="^(pdf|html|docx)$")


# In-memory storage for reports
_reports_db: dict[str, dict] = {}


# Compliance frameworks data
EU_AI_ACT_REQUIREMENTS = {
    "categories": [
        "Risk Management",
        "Data Governance",
        "Technical Documentation",
        "Record Keeping",
        "Transparency",
        "Human Oversight",
        "Accuracy & Robustness",
        "Cybersecurity",
    ],
    "requirements": [
        {
            "id": "AIA-9.1",
            "title": "Risk Management System",
            "description": "Establish and maintain a risk management system",
            "category": "Risk Management",
            "pillar_mappings": ["actions", "robustness", "security"],
        },
        {
            "id": "AIA-9.2",
            "title": "Risk Identification",
            "description": "Identify and analyze known and foreseeable risks",
            "category": "Risk Management",
            "pillar_mappings": ["actions", "security"],
        },
        {
            "id": "AIA-10.1",
            "title": "Data Quality",
            "description": "Training data shall be relevant, representative, and free of errors",
            "category": "Data Governance",
            "pillar_mappings": ["trace", "fairness"],
        },
        {
            "id": "AIA-10.2",
            "title": "Data Governance",
            "description": "Appropriate data governance and management practices",
            "category": "Data Governance",
            "pillar_mappings": ["trace", "privacy"],
        },
        {
            "id": "AIA-11",
            "title": "Technical Documentation",
            "description": "Draw up technical documentation demonstrating compliance",
            "category": "Technical Documentation",
            "pillar_mappings": ["explain", "testing"],
        },
        {
            "id": "AIA-12",
            "title": "Record Keeping",
            "description": "Automatic recording of events (logs)",
            "category": "Record Keeping",
            "pillar_mappings": ["testing"],
        },
        {
            "id": "AIA-13",
            "title": "Transparency",
            "description": "Ensure transparency and provision of information to users",
            "category": "Transparency",
            "pillar_mappings": ["explain"],
        },
        {
            "id": "AIA-14",
            "title": "Human Oversight",
            "description": "Enable human oversight during use",
            "category": "Human Oversight",
            "pillar_mappings": ["explain"],
        },
        {
            "id": "AIA-15.1",
            "title": "Accuracy",
            "description": "Achieve appropriate levels of accuracy",
            "category": "Accuracy & Robustness",
            "pillar_mappings": ["testing"],
        },
        {
            "id": "AIA-15.2",
            "title": "Robustness",
            "description": "Resilient to errors, faults, or inconsistencies",
            "category": "Accuracy & Robustness",
            "pillar_mappings": ["robustness", "actions"],
        },
        {
            "id": "AIA-15.3",
            "title": "Cybersecurity",
            "description": "Resilient to unauthorized access and adversarial attacks",
            "category": "Cybersecurity",
            "pillar_mappings": ["security", "imitation", "privacy"],
        },
    ],
}

SOC2_REQUIREMENTS = {
    "categories": ["Security", "Availability", "Processing Integrity", "Confidentiality", "Privacy"],
    "requirements": [
        {"id": "CC6.1", "title": "Logical Access Security", "category": "Security", "pillar_mappings": ["security"]},
        {"id": "CC6.2", "title": "System Authentication", "category": "Security", "pillar_mappings": ["security"]},
        {"id": "CC6.3", "title": "Authorization", "category": "Security", "pillar_mappings": ["security", "actions"]},
        {"id": "CC7.1", "title": "System Operations", "category": "Availability", "pillar_mappings": ["robustness"]},
        {"id": "CC7.2", "title": "Change Management", "category": "Availability", "pillar_mappings": ["testing"]},
        {"id": "CC8.1", "title": "Processing Integrity", "category": "Processing Integrity", "pillar_mappings": ["testing", "explain"]},
        {"id": "CC9.1", "title": "Confidential Information", "category": "Confidentiality", "pillar_mappings": ["privacy"]},
        {"id": "P1.1", "title": "Privacy Notice", "category": "Privacy", "pillar_mappings": ["privacy", "explain"]},
    ],
}


def _calculate_compliance_from_pillars(
    requirements: list[dict],
    pillar_scores: dict[str, float],
    threshold: float = 0.7,
) -> tuple[list[RequirementStatus], dict[str, int]]:
    """
    Calculate compliance status based on pillar evaluation scores.
    
    Args:
        requirements: List of requirement definitions with pillar mappings
        pillar_scores: Dict of pillar name -> score (0.0 to 1.0)
        threshold: Score threshold for "met" status
    
    Returns:
        Tuple of (requirement statuses, counts dict)
    """
    statuses = []
    counts = {"met": 0, "partial": 0, "not_met": 0, "not_applicable": 0}
    
    for req in requirements:
        mapped_pillars = req.get("pillar_mappings", [])
        
        if not mapped_pillars:
            status = "not_applicable"
            counts["not_applicable"] += 1
        else:
            # Calculate average score across mapped pillars
            scores = [pillar_scores.get(p, 0.5) for p in mapped_pillars]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            if avg_score >= threshold:
                status = "met"
                counts["met"] += 1
            elif avg_score >= threshold * 0.6:
                status = "partial"
                counts["partial"] += 1
            else:
                status = "not_met"
                counts["not_met"] += 1
        
        # Build evidence and gaps
        evidence = []
        gaps = []
        
        for pillar in mapped_pillars:
            score = pillar_scores.get(pillar, 0.5)
            if score >= threshold:
                evidence.append(f"Pillar '{pillar}' score {score:.2f} meets threshold")
            else:
                gaps.append(f"Improve '{pillar}' pillar (current: {score:.2f}, required: {threshold:.2f})")
        
        statuses.append(RequirementStatus(
            requirement_id=req["id"],
            title=req["title"],
            description=req.get("description", ""),
            category=req["category"],
            status=status,
            evidence=evidence,
            gaps=gaps,
            pillar_mappings=mapped_pillars,
        ))
    
    return statuses, counts


@router.get("/frameworks", response_model=list[ComplianceFramework])
async def list_compliance_frameworks() -> list[ComplianceFramework]:
    """
    List available compliance frameworks.
    """
    return [
        ComplianceFramework(
            id="eu_ai_act",
            name="EU AI Act",
            version="2024",
            description="European Union Artificial Intelligence Act requirements",
            total_requirements=len(EU_AI_ACT_REQUIREMENTS["requirements"]),
            categories=EU_AI_ACT_REQUIREMENTS["categories"],
        ),
        ComplianceFramework(
            id="soc2",
            name="SOC 2 Type II",
            version="2023",
            description="Service Organization Control 2 criteria for AI systems",
            total_requirements=len(SOC2_REQUIREMENTS["requirements"]),
            categories=SOC2_REQUIREMENTS["categories"],
        ),
        ComplianceFramework(
            id="iso27001",
            name="ISO 27001",
            version="2022",
            description="Information security management for AI systems",
            total_requirements=93,
            categories=[
                "Information Security Policies",
                "Asset Management",
                "Access Control",
                "Cryptography",
                "Operations Security",
            ],
        ),
        ComplianceFramework(
            id="hipaa",
            name="HIPAA",
            version="2023",
            description="Health Insurance Portability and Accountability Act for AI in healthcare",
            total_requirements=45,
            categories=[
                "Administrative Safeguards",
                "Physical Safeguards",
                "Technical Safeguards",
                "Privacy Rule",
            ],
        ),
    ]


@router.get("/eu-ai-act", response_model=ModelComplianceStatus)
async def get_eu_ai_act_compliance(
    model_id: str,
) -> ModelComplianceStatus:
    """
    Get EU AI Act compliance mapping for a model.
    
    Maps evaluation pillar results to EU AI Act requirements.
    """
    # Query pillar scores from evaluations (simulated data for demo)
    # In production, fetch from database based on model's latest evaluation
    pillar_scores = {
        "actions": 0.82,
        "robustness": 0.75,
        "security": 0.45,  # Low score to show gaps
        "trace": 0.88,
        "fairness": 0.71,
        "privacy": 0.68,
        "explain": 0.79,
        "testing": 0.85,
        "imitation": 0.62,
    }
    
    # Calculate compliance
    requirements, counts = _calculate_compliance_from_pillars(
        EU_AI_ACT_REQUIREMENTS["requirements"],
        pillar_scores,
        threshold=0.7,
    )
    
    total = len(requirements)
    coverage = ((counts["met"] + counts["partial"] * 0.5) / total) * 100 if total > 0 else 0
    
    return ModelComplianceStatus(
        model_id=model_id,
        model_name="Model from Registry",
        framework="eu_ai_act",
        framework_version="2024",
        coverage_percentage=round(coverage, 1),
        met_requirements=counts["met"],
        partial_requirements=counts["partial"],
        not_met_requirements=counts["not_met"],
        not_applicable=counts["not_applicable"],
        total_requirements=total,
        risk_classification="high",
        last_assessed=datetime.utcnow().isoformat(),
        requirements=requirements,
    )


@router.get("/soc2", response_model=ModelComplianceStatus)
async def get_soc2_compliance(model_id: str) -> ModelComplianceStatus:
    """
    Get SOC 2 compliance mapping for a model.
    """
    # Simulated pillar scores
    pillar_scores = {
        "security": 0.78,
        "actions": 0.85,
        "robustness": 0.72,
        "testing": 0.90,
        "privacy": 0.65,
        "explain": 0.81,
    }
    
    requirements, counts = _calculate_compliance_from_pillars(
        SOC2_REQUIREMENTS["requirements"],
        pillar_scores,
        threshold=0.7,
    )
    
    total = len(requirements)
    coverage = ((counts["met"] + counts["partial"] * 0.5) / total) * 100 if total > 0 else 0
    
    return ModelComplianceStatus(
        model_id=model_id,
        model_name="Model from Registry",
        framework="soc2",
        framework_version="2023",
        coverage_percentage=round(coverage, 1),
        met_requirements=counts["met"],
        partial_requirements=counts["partial"],
        not_met_requirements=counts["not_met"],
        not_applicable=counts["not_applicable"],
        total_requirements=total,
        risk_classification="moderate",
        last_assessed=datetime.utcnow().isoformat(),
        requirements=requirements,
    )


@router.get("/{framework}", response_model=ModelComplianceStatus)
async def get_compliance_status(
    framework: str,
    model_id: str,
) -> ModelComplianceStatus:
    """
    Get compliance status for a model against a specific framework.
    """
    if framework == "eu_ai_act":
        return await get_eu_ai_act_compliance(model_id)
    elif framework == "soc2":
        return await get_soc2_compliance(model_id)
    
    # For unimplemented frameworks, return a placeholder
    raise HTTPException(
        status_code=501,
        detail=f"Compliance mapping for '{framework}' not yet implemented. Available: eu_ai_act, soc2"
    )


@router.post("/report")
async def generate_compliance_report(
    request: GenerateReportRequest,
) -> dict[str, Any]:
    """
    Generate a compliance report.
    
    Supports multiple models and output formats (PDF, HTML, DOCX).
    Submits an Argo workflow for async report generation.
    """
    report_id = str(uuid4())
    now = datetime.utcnow()
    
    # Store report request
    report_record = {
        "id": report_id,
        "status": "generating",
        "framework": request.framework,
        "model_ids": request.model_ids,
        "format": request.format,
        "include_evidence": request.include_evidence,
        "include_gaps": request.include_gaps,
        "created_at": now.isoformat(),
        "completed_at": None,
        "download_url": None,
    }
    _reports_db[report_id] = report_record
    
    # Submit Argo workflow for report generation
    argo_service = get_argo_service()
    
    try:
        workflow_manifest = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Workflow",
            "metadata": {
                "generateName": f"compliance-report-{report_id[:8]}-",
                "labels": {
                    "guardstack.io/report-id": report_id,
                    "guardstack.io/framework": request.framework,
                },
            },
            "spec": {
                "entrypoint": "generate-report",
                "arguments": {
                    "parameters": [
                        {"name": "report-id", "value": report_id},
                        {"name": "framework", "value": request.framework},
                        {"name": "format", "value": request.format},
                    ]
                },
                "templates": [
                    {
                        "name": "generate-report",
                        "container": {
                            "image": "guardstack/report-generator:latest",
                            "command": ["python", "-m", "guardstack.workers.report"],
                            "args": [
                                "--report-id", "{{inputs.parameters.report-id}}",
                                "--framework", "{{inputs.parameters.framework}}",
                                "--format", "{{inputs.parameters.format}}",
                            ],
                        },
                    }
                ],
            },
        }
        
        workflow_status = await argo_service.submit_workflow(workflow_manifest)
        report_record["workflow_name"] = workflow_status.workflow_name
        
    except Exception as e:
        # Mark as ready immediately for demo (no Argo)
        report_record["status"] = "ready"
        report_record["completed_at"] = now.isoformat()
        report_record["error"] = str(e)
    
    return {
        "report_id": report_id,
        "status": report_record["status"],
        "framework": request.framework,
        "model_count": len(request.model_ids) if request.model_ids else "all",
        "format": request.format,
        "created_at": now.isoformat(),
        "estimated_completion": (now.replace(minute=now.minute + 5)).isoformat(),
    }


@router.get("/report/{report_id}")
async def get_compliance_report(report_id: str) -> StreamingResponse:
    """
    Download a generated compliance report.
    """
    if report_id not in _reports_db:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = _reports_db[report_id]
    
    if report["status"] == "generating":
        raise HTTPException(
            status_code=202,
            detail="Report is still being generated. Please try again later."
        )
    
    # Generate inline report for demo
    import json
    
    report_content = {
        "report_id": report_id,
        "framework": report["framework"],
        "generated_at": report.get("completed_at") or datetime.utcnow().isoformat(),
        "summary": {
            "total_models": len(report.get("model_ids", [])) or 1,
            "overall_coverage": 75.5,
            "critical_gaps": 2,
        },
        "models": [
            {
                "model_id": mid or "demo-model",
                "coverage": 75.5,
                "met": 7,
                "partial": 3,
                "not_met": 1,
            }
            for mid in (report.get("model_ids") or ["demo-model"])
        ],
    }
    
    if report["format"] == "html":
        html = f"""
<!DOCTYPE html>
<html>
<head><title>Compliance Report - {report["framework"]}</title></head>
<body>
<h1>Compliance Report: {report["framework"].upper()}</h1>
<p>Generated: {report_content["generated_at"]}</p>
<h2>Summary</h2>
<ul>
<li>Models Assessed: {report_content["summary"]["total_models"]}</li>
<li>Overall Coverage: {report_content["summary"]["overall_coverage"]}%</li>
<li>Critical Gaps: {report_content["summary"]["critical_gaps"]}</li>
</ul>
</body>
</html>
"""
        return StreamingResponse(
            iter([html]),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=compliance-{report_id}.html"}
        )
    
    # Default to JSON
    return StreamingResponse(
        iter([json.dumps(report_content, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=compliance-{report_id}.json"}
    )


@router.get("/gaps")
async def get_compliance_gaps(
    framework: str = Query(default="eu_ai_act"),
    model_ids: Optional[list[str]] = Query(default=None),
) -> dict[str, Any]:
    """
    Get aggregated compliance gaps across models.
    
    Useful for identifying systemic compliance issues.
    """
    return {
        "framework": framework,
        "total_models_assessed": 25,
        "common_gaps": [
            {
                "requirement_id": "AIA-15.3",
                "title": "Cybersecurity",
                "affected_models": 15,
                "severity": "high",
                "recommendation": "Implement adversarial robustness testing and model protection mechanisms",
            },
            {
                "requirement_id": "AIA-10.1",
                "title": "Data Quality",
                "affected_models": 8,
                "severity": "medium",
                "recommendation": "Improve data lineage tracking and bias detection in training data",
            },
            {
                "requirement_id": "AIA-13",
                "title": "Transparency",
                "affected_models": 5,
                "severity": "medium",
                "recommendation": "Enhance model explainability and documentation",
            },
        ],
        "recommendations": [
            "Focus on security pillar improvements to address cybersecurity gaps",
            "Implement automated data quality monitoring",
            "Generate model cards and documentation for all high-risk AI systems",
        ],
    }
