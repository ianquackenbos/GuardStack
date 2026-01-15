"""
AI Security Posture Management (AI-SPM) Router

Endpoints for managing AI security posture across the organization,
including asset inventory, vulnerability findings, and risk assessment.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user

router = APIRouter(prefix="/spm", tags=["AI-SPM"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AssetBase(BaseModel):
    """Base model for AI assets"""
    name: str = Field(..., description="Asset name")
    asset_type: str = Field(..., description="Type: model, dataset, pipeline, agent")
    provider: Optional[str] = Field(None, description="Provider name (OpenAI, HuggingFace, etc.)")
    location: Optional[str] = Field(None, description="Deployment location")
    classification: Optional[str] = Field(None, description="Data classification level")
    owner: Optional[str] = Field(None, description="Asset owner")
    tags: Optional[dict] = Field(default_factory=dict, description="Custom tags")


class AssetCreate(AssetBase):
    """Model for creating an asset"""
    pass


class AssetResponse(AssetBase):
    """Model for asset response"""
    id: UUID
    risk_score: float = Field(0.0, description="Calculated risk score 0-100")
    status: str = Field("active", description="Asset status")
    last_scanned: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FindingBase(BaseModel):
    """Base model for security findings"""
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Detailed description")
    severity: str = Field(..., description="Severity: critical, high, medium, low, info")
    category: str = Field(..., description="Category: vulnerability, misconfiguration, compliance, exposure")
    asset_id: Optional[UUID] = Field(None, description="Associated asset ID")


class FindingCreate(FindingBase):
    """Model for creating a finding"""
    remediation: Optional[str] = Field(None, description="Remediation guidance")
    evidence: Optional[dict] = Field(default_factory=dict, description="Supporting evidence")


class FindingResponse(FindingBase):
    """Model for finding response"""
    id: UUID
    status: str = Field("open", description="Finding status: open, in_progress, resolved, ignored")
    remediation: Optional[str] = None
    evidence: Optional[dict] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostureScore(BaseModel):
    """Security posture score breakdown"""
    overall_score: float = Field(..., description="Overall posture score 0-100")
    model_security: float = Field(..., description="Model security score")
    data_protection: float = Field(..., description="Data protection score")
    access_control: float = Field(..., description="Access control score")
    compliance: float = Field(..., description="Compliance score")
    monitoring: float = Field(..., description="Monitoring coverage score")


class PostureResponse(BaseModel):
    """Full security posture response"""
    score: PostureScore
    total_assets: int
    assets_by_risk: dict = Field(..., description="Asset count by risk level")
    open_findings: int
    critical_findings: int
    trend: str = Field(..., description="Score trend: improving, stable, declining")
    last_scan: Optional[datetime] = None


class ScanRequest(BaseModel):
    """Request model for initiating a scan"""
    scan_type: str = Field("full", description="Scan type: full, quick, targeted")
    asset_ids: Optional[list[UUID]] = Field(None, description="Specific assets to scan")
    categories: Optional[list[str]] = Field(None, description="Categories to check")


class ScanResponse(BaseModel):
    """Response for scan initiation"""
    scan_id: UUID
    status: str = Field("queued", description="Scan status")
    estimated_duration: int = Field(..., description="Estimated duration in seconds")
    queued_at: datetime


# ============================================================================
# Asset Inventory Endpoints
# ============================================================================

@router.get("/inventory", response_model=list[AssetResponse])
async def list_assets(
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: critical, high, medium, low"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    status: Optional[str] = Query("active", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List all AI assets in the inventory.
    
    Returns paginated list of models, datasets, pipelines, and agents
    with their current risk scores and status.
    """
    # Mock response for now - would query from database
    from uuid import uuid4
    
    assets = [
        AssetResponse(
            id=uuid4(),
            name="GPT-4-Production",
            asset_type="model",
            provider="OpenAI",
            location="us-east-1",
            classification="confidential",
            owner="ml-team",
            tags={"environment": "production", "cost_center": "ml-ops"},
            risk_score=23.5,
            status="active",
            last_scanned=datetime.utcnow() - timedelta(hours=2),
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow(),
        ),
        AssetResponse(
            id=uuid4(),
            name="Customer-Dataset-v2",
            asset_type="dataset",
            provider="Internal",
            location="s3://data-lake",
            classification="pii",
            owner="data-team",
            tags={"contains_pii": "true"},
            risk_score=67.2,
            status="active",
            last_scanned=datetime.utcnow() - timedelta(hours=6),
            created_at=datetime.utcnow() - timedelta(days=90),
            updated_at=datetime.utcnow(),
        ),
        AssetResponse(
            id=uuid4(),
            name="RAG-Pipeline-Prod",
            asset_type="pipeline",
            provider="LangChain",
            location="k8s-cluster-prod",
            classification="internal",
            owner="platform-team",
            tags={"has_vector_store": "true"},
            risk_score=45.8,
            status="active",
            last_scanned=datetime.utcnow() - timedelta(hours=1),
            created_at=datetime.utcnow() - timedelta(days=14),
            updated_at=datetime.utcnow(),
        ),
    ]
    
    return assets


@router.get("/inventory/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed information about a specific AI asset.
    """
    # Mock response
    return AssetResponse(
        id=asset_id,
        name="GPT-4-Production",
        asset_type="model",
        provider="OpenAI",
        location="us-east-1",
        classification="confidential",
        owner="ml-team",
        tags={"environment": "production"},
        risk_score=23.5,
        status="active",
        last_scanned=datetime.utcnow() - timedelta(hours=2),
        created_at=datetime.utcnow() - timedelta(days=30),
        updated_at=datetime.utcnow(),
    )


@router.post("/inventory", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Register a new AI asset in the inventory.
    """
    from uuid import uuid4
    
    return AssetResponse(
        id=uuid4(),
        **asset.model_dump(),
        risk_score=0.0,
        status="pending_scan",
        last_scanned=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.delete("/inventory/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Remove an AI asset from the inventory.
    """
    return None


# ============================================================================
# Security Findings Endpoints
# ============================================================================

@router.get("/findings", response_model=list[FindingResponse])
async def list_findings(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    asset_id: Optional[UUID] = Query(None, description="Filter by asset"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List security findings across all AI assets.
    """
    from uuid import uuid4
    
    findings = [
        FindingResponse(
            id=uuid4(),
            title="Model API Key Exposed in Logs",
            description="API key for production model found in application logs accessible to unauthorized users.",
            severity="critical",
            category="exposure",
            asset_id=uuid4(),
            status="open",
            remediation="Rotate API key immediately and configure log scrubbing for sensitive values.",
            evidence={"log_file": "/var/log/app/api.log", "line": 1234},
            detected_at=datetime.utcnow() - timedelta(hours=4),
            resolved_at=None,
            created_at=datetime.utcnow() - timedelta(hours=4),
            updated_at=datetime.utcnow(),
        ),
        FindingResponse(
            id=uuid4(),
            title="Missing Input Validation on RAG Pipeline",
            description="RAG pipeline accepts user input without proper sanitization, potential prompt injection risk.",
            severity="high",
            category="vulnerability",
            asset_id=uuid4(),
            status="in_progress",
            remediation="Implement input validation and sanitization before processing user queries.",
            evidence={"endpoint": "/api/chat", "test_payload": "ignore previous..."},
            detected_at=datetime.utcnow() - timedelta(days=2),
            resolved_at=None,
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow(),
        ),
        FindingResponse(
            id=uuid4(),
            title="Dataset Missing Encryption at Rest",
            description="Customer dataset stored without encryption, violating data protection policies.",
            severity="high",
            category="misconfiguration",
            asset_id=uuid4(),
            status="open",
            remediation="Enable S3 server-side encryption with customer-managed keys.",
            evidence={"bucket": "s3://data-lake/customers", "encryption": "none"},
            detected_at=datetime.utcnow() - timedelta(days=1),
            resolved_at=None,
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow(),
        ),
    ]
    
    return findings


@router.get("/findings/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed information about a specific security finding.
    """
    return FindingResponse(
        id=finding_id,
        title="Model API Key Exposed in Logs",
        description="API key for production model found in application logs.",
        severity="critical",
        category="exposure",
        asset_id=None,
        status="open",
        remediation="Rotate API key and configure log scrubbing.",
        evidence={},
        detected_at=datetime.utcnow() - timedelta(hours=4),
        resolved_at=None,
        created_at=datetime.utcnow() - timedelta(hours=4),
        updated_at=datetime.utcnow(),
    )


@router.patch("/findings/{finding_id}/status")
async def update_finding_status(
    finding_id: UUID,
    new_status: str = Query(..., description="New status: open, in_progress, resolved, ignored"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update the status of a security finding.
    """
    valid_statuses = ["open", "in_progress", "resolved", "ignored"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    return {"id": finding_id, "status": new_status, "updated_at": datetime.utcnow()}


# ============================================================================
# Security Posture Endpoints
# ============================================================================

@router.get("/posture", response_model=PostureResponse)
async def get_security_posture(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the current AI security posture score and breakdown.
    
    Returns overall score and individual domain scores for:
    - Model security (access, versioning, vulnerabilities)
    - Data protection (encryption, classification, lineage)
    - Access control (authentication, authorization, audit)
    - Compliance (regulatory requirements, policies)
    - Monitoring (logging, alerting, response)
    """
    return PostureResponse(
        score=PostureScore(
            overall_score=72.5,
            model_security=78.0,
            data_protection=65.0,
            access_control=82.0,
            compliance=70.0,
            monitoring=67.5,
        ),
        total_assets=47,
        assets_by_risk={
            "critical": 2,
            "high": 8,
            "medium": 15,
            "low": 22,
        },
        open_findings=23,
        critical_findings=3,
        trend="improving",
        last_scan=datetime.utcnow() - timedelta(hours=1),
    )


@router.get("/posture/history")
async def get_posture_history(
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get historical security posture scores for trend analysis.
    """
    # Generate mock historical data
    history = []
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - i - 1)
        # Simulate gradual improvement
        base_score = 65.0 + (i * 0.25)
        history.append({
            "date": date.isoformat(),
            "overall_score": min(base_score + (i % 3), 100),
            "open_findings": max(30 - (i // 3), 20),
        })
    
    return {"history": history, "period_days": days}


# ============================================================================
# Scanning Endpoints
# ============================================================================

@router.post("/scan", response_model=ScanResponse)
async def initiate_scan(
    request: ScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Initiate a security scan across AI assets.
    
    Scan types:
    - full: Complete scan of all assets and categories
    - quick: Fast scan of critical issues only
    - targeted: Scan specific assets or categories
    """
    from uuid import uuid4
    
    # Estimate duration based on scan type
    duration_map = {
        "full": 3600,
        "quick": 300,
        "targeted": 600,
    }
    
    return ScanResponse(
        scan_id=uuid4(),
        status="queued",
        estimated_duration=duration_map.get(request.scan_type, 600),
        queued_at=datetime.utcnow(),
    )


@router.get("/scan/{scan_id}/status")
async def get_scan_status(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the current status of a running scan.
    """
    return {
        "scan_id": scan_id,
        "status": "running",
        "progress": 67,
        "assets_scanned": 32,
        "total_assets": 47,
        "findings_detected": 5,
        "started_at": datetime.utcnow() - timedelta(minutes=20),
        "estimated_completion": datetime.utcnow() + timedelta(minutes=10),
    }


@router.delete("/scan/{scan_id}")
async def cancel_scan(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Cancel a running scan.
    """
    return {"scan_id": scan_id, "status": "cancelled", "cancelled_at": datetime.utcnow()}
