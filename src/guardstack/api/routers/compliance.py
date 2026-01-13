"""
Compliance API Router

Endpoints for compliance mapping and reporting (EU AI Act, SOC2, etc.).
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

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
            total_requirements=11,
            categories=EU_AI_ACT_REQUIREMENTS["categories"],
        ),
        ComplianceFramework(
            id="soc2",
            name="SOC 2 Type II",
            version="2023",
            description="Service Organization Control 2 criteria for AI systems",
            total_requirements=64,
            categories=[
                "Security",
                "Availability",
                "Processing Integrity",
                "Confidentiality",
                "Privacy",
            ],
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
    # TODO: Query model and its latest evaluation from database
    # Calculate compliance based on pillar scores
    
    # Demo data
    requirements = []
    met = 0
    partial = 0
    not_met = 0
    
    for req in EU_AI_ACT_REQUIREMENTS["requirements"]:
        # Simulate status based on pillar mappings
        status = "met" if len(req["pillar_mappings"]) > 1 else "partial"
        if req["id"] == "AIA-15.3":
            status = "not_met"
        
        if status == "met":
            met += 1
        elif status == "partial":
            partial += 1
        else:
            not_met += 1
        
        requirements.append(RequirementStatus(
            requirement_id=req["id"],
            title=req["title"],
            description=req["description"],
            category=req["category"],
            status=status,
            evidence=[f"Pillar '{p}' score above threshold" for p in req["pillar_mappings"]] if status == "met" else [],
            gaps=[f"Improve {p} pillar score" for p in req["pillar_mappings"]] if status != "met" else [],
            pillar_mappings=req["pillar_mappings"],
        ))
    
    total = len(requirements)
    coverage = ((met + partial * 0.5) / total) * 100
    
    return ModelComplianceStatus(
        model_id=model_id,
        model_name="Demo Model",
        framework="eu_ai_act",
        framework_version="2024",
        coverage_percentage=coverage,
        met_requirements=met,
        partial_requirements=partial,
        not_met_requirements=not_met,
        not_applicable=0,
        total_requirements=total,
        risk_classification="high",
        last_assessed="2024-01-15T10:00:00Z",
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
    
    # TODO: Implement other frameworks
    raise HTTPException(
        status_code=501,
        detail=f"Compliance mapping for {framework} not yet implemented"
    )


@router.post("/report")
async def generate_compliance_report(
    request: GenerateReportRequest,
) -> dict[str, Any]:
    """
    Generate a compliance report.
    
    Supports multiple models and output formats (PDF, HTML, DOCX).
    """
    from datetime import datetime
    from uuid import uuid4
    
    report_id = uuid4()
    
    # TODO: Generate report asynchronously via Argo workflow
    
    return {
        "report_id": str(report_id),
        "status": "generating",
        "framework": request.framework,
        "model_count": len(request.model_ids) if request.model_ids else "all",
        "format": request.format,
        "created_at": datetime.utcnow().isoformat(),
        "estimated_completion": "2024-01-15T10:05:00Z",
    }


@router.get("/report/{report_id}")
async def get_compliance_report(report_id: str) -> StreamingResponse:
    """
    Download a generated compliance report.
    """
    # TODO: Fetch report from S3/MinIO
    
    raise HTTPException(
        status_code=404,
        detail="Report not found or still generating"
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
