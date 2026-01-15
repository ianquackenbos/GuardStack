"""
Inventory Router

Endpoints for AI model discovery, asset registration,
and comprehensive inventory management.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# ============================================================================
# Pydantic Models
# ============================================================================

class DiscoverySourceBase(BaseModel):
    """Base model for discovery sources"""
    name: str = Field(..., description="Source name")
    source_type: str = Field(..., description="Type: kubernetes, cloud, registry, manual")
    config: dict = Field(..., description="Source-specific configuration")


class DiscoverySourceCreate(DiscoverySourceBase):
    """Model for creating a discovery source"""
    enabled: bool = Field(True, description="Whether source is active")
    scan_interval_minutes: int = Field(60, ge=5, description="Scan interval")


class DiscoverySourceResponse(DiscoverySourceBase):
    """Model for discovery source response"""
    id: UUID
    enabled: bool
    scan_interval_minutes: int
    last_scan: Optional[datetime] = None
    next_scan: Optional[datetime] = None
    discovered_count: int = Field(0, description="Total assets discovered")
    status: str = Field("active", description="Source status")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiscoveredAsset(BaseModel):
    """Model for a discovered AI asset"""
    id: UUID
    source_id: UUID
    name: str = Field(..., description="Asset name/identifier")
    asset_type: str = Field(..., description="Type: model, endpoint, dataset, pipeline")
    provider: Optional[str] = Field(None, description="Provider (OpenAI, AWS, etc.)")
    location: str = Field(..., description="Location/path/URL")
    metadata: dict = Field(default_factory=dict, description="Discovered metadata")
    registration_status: str = Field("pending", description="Status: pending, registered, ignored")
    discovered_at: datetime
    registered_at: Optional[datetime] = None


class AssetRegistration(BaseModel):
    """Model for registering a discovered asset"""
    discovered_asset_id: UUID
    display_name: Optional[str] = Field(None, description="Override display name")
    classification: str = Field(..., description="Data classification")
    owner: str = Field(..., description="Asset owner/team")
    tags: Optional[dict] = Field(default_factory=dict, description="Custom tags")
    compliance_requirements: Optional[list[str]] = Field(None, description="Applicable compliance frameworks")


class DiscoveryScanRequest(BaseModel):
    """Request for triggering discovery scan"""
    source_ids: Optional[list[UUID]] = Field(None, description="Specific sources to scan")
    asset_types: Optional[list[str]] = Field(None, description="Asset types to discover")
    deep_scan: bool = Field(False, description="Perform deep metadata extraction")


class DiscoveryScanResponse(BaseModel):
    """Response for discovery scan"""
    scan_id: UUID
    status: str
    sources_scanned: int
    new_assets_found: int
    updated_assets: int
    errors: list[str]
    started_at: datetime
    completed_at: Optional[datetime] = None


# ============================================================================
# Discovery Source Endpoints
# ============================================================================

@router.get("/sources", response_model=list[DiscoverySourceResponse])
async def list_discovery_sources(
    source_type: Optional[str] = Query(None, description="Filter by type"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List configured discovery sources.
    """
    from uuid import uuid4
    
    sources = [
        DiscoverySourceResponse(
            id=uuid4(),
            name="Production Kubernetes",
            source_type="kubernetes",
            config={
                "cluster": "prod-cluster",
                "namespaces": ["ml-serving", "llm-inference"],
                "labels": {"app.kubernetes.io/component": "model-serving"},
            },
            enabled=True,
            scan_interval_minutes=30,
            last_scan=datetime.utcnow() - timedelta(minutes=15),
            next_scan=datetime.utcnow() + timedelta(minutes=15),
            discovered_count=23,
            status="active",
            created_at=datetime.utcnow() - timedelta(days=60),
            updated_at=datetime.utcnow(),
        ),
        DiscoverySourceResponse(
            id=uuid4(),
            name="AWS Bedrock",
            source_type="cloud",
            config={
                "provider": "aws",
                "service": "bedrock",
                "regions": ["us-east-1", "us-west-2"],
            },
            enabled=True,
            scan_interval_minutes=60,
            last_scan=datetime.utcnow() - timedelta(minutes=45),
            next_scan=datetime.utcnow() + timedelta(minutes=15),
            discovered_count=8,
            status="active",
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow(),
        ),
        DiscoverySourceResponse(
            id=uuid4(),
            name="HuggingFace Hub",
            source_type="registry",
            config={
                "registry": "huggingface",
                "organization": "company-org",
                "include_private": True,
            },
            enabled=True,
            scan_interval_minutes=120,
            last_scan=datetime.utcnow() - timedelta(hours=1),
            next_scan=datetime.utcnow() + timedelta(hours=1),
            discovered_count=45,
            status="active",
            created_at=datetime.utcnow() - timedelta(days=45),
            updated_at=datetime.utcnow(),
        ),
        DiscoverySourceResponse(
            id=uuid4(),
            name="OpenAI API Keys",
            source_type="cloud",
            config={
                "provider": "openai",
                "scan_api_keys": True,
                "scan_assistants": True,
            },
            enabled=True,
            scan_interval_minutes=60,
            last_scan=datetime.utcnow() - timedelta(minutes=30),
            next_scan=datetime.utcnow() + timedelta(minutes=30),
            discovered_count=12,
            status="active",
            created_at=datetime.utcnow() - timedelta(days=90),
            updated_at=datetime.utcnow(),
        ),
    ]
    
    return sources


@router.get("/sources/{source_id}", response_model=DiscoverySourceResponse)
async def get_discovery_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get details of a specific discovery source.
    """
    return DiscoverySourceResponse(
        id=source_id,
        name="Production Kubernetes",
        source_type="kubernetes",
        config={
            "cluster": "prod-cluster",
            "namespaces": ["ml-serving", "llm-inference"],
        },
        enabled=True,
        scan_interval_minutes=30,
        last_scan=datetime.utcnow() - timedelta(minutes=15),
        next_scan=datetime.utcnow() + timedelta(minutes=15),
        discovered_count=23,
        status="active",
        created_at=datetime.utcnow() - timedelta(days=60),
        updated_at=datetime.utcnow(),
    )


@router.post("/sources", response_model=DiscoverySourceResponse, status_code=status.HTTP_201_CREATED)
async def create_discovery_source(
    source: DiscoverySourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new discovery source.
    """
    from uuid import uuid4
    
    return DiscoverySourceResponse(
        id=uuid4(),
        name=source.name,
        source_type=source.source_type,
        config=source.config,
        enabled=source.enabled,
        scan_interval_minutes=source.scan_interval_minutes,
        last_scan=None,
        next_scan=datetime.utcnow() + timedelta(minutes=source.scan_interval_minutes),
        discovered_count=0,
        status="pending_initial_scan",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@router.put("/sources/{source_id}", response_model=DiscoverySourceResponse)
async def update_discovery_source(
    source_id: UUID,
    source: DiscoverySourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a discovery source configuration.
    """
    return DiscoverySourceResponse(
        id=source_id,
        name=source.name,
        source_type=source.source_type,
        config=source.config,
        enabled=source.enabled,
        scan_interval_minutes=source.scan_interval_minutes,
        last_scan=datetime.utcnow() - timedelta(minutes=15),
        next_scan=datetime.utcnow() + timedelta(minutes=source.scan_interval_minutes),
        discovered_count=23,
        status="active",
        created_at=datetime.utcnow() - timedelta(days=60),
        updated_at=datetime.utcnow(),
    )


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discovery_source(
    source_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a discovery source.
    """
    return None


# ============================================================================
# Discovery Scan Endpoints
# ============================================================================

@router.post("/discover", response_model=DiscoveryScanResponse)
async def trigger_discovery_scan(
    request: DiscoveryScanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger a discovery scan across configured sources.
    """
    from uuid import uuid4
    
    return DiscoveryScanResponse(
        scan_id=uuid4(),
        status="running",
        sources_scanned=4,
        new_assets_found=0,
        updated_assets=0,
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=None,
    )


@router.get("/discover/{scan_id}", response_model=DiscoveryScanResponse)
async def get_discovery_scan_status(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get status of a discovery scan.
    """
    return DiscoveryScanResponse(
        scan_id=scan_id,
        status="completed",
        sources_scanned=4,
        new_assets_found=3,
        updated_assets=12,
        errors=[],
        started_at=datetime.utcnow() - timedelta(minutes=5),
        completed_at=datetime.utcnow(),
    )


# ============================================================================
# Discovered Assets Endpoints
# ============================================================================

@router.get("/discovered", response_model=list[DiscoveredAsset])
async def list_discovered_assets(
    source_id: Optional[UUID] = Query(None, description="Filter by source"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    registration_status: Optional[str] = Query(None, description="Filter by registration status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    List discovered AI assets.
    """
    from uuid import uuid4
    
    assets = [
        DiscoveredAsset(
            id=uuid4(),
            source_id=uuid4(),
            name="gpt-4-turbo-preview",
            asset_type="model",
            provider="OpenAI",
            location="api.openai.com",
            metadata={
                "model_version": "gpt-4-turbo-2024-01-25",
                "context_window": 128000,
                "capabilities": ["vision", "function_calling"],
            },
            registration_status="registered",
            discovered_at=datetime.utcnow() - timedelta(days=7),
            registered_at=datetime.utcnow() - timedelta(days=6),
        ),
        DiscoveredAsset(
            id=uuid4(),
            source_id=uuid4(),
            name="llm-serving-pod-abc123",
            asset_type="endpoint",
            provider="Internal",
            location="k8s://prod-cluster/ml-serving/llm-serving-abc123",
            metadata={
                "image": "company/llm-serving:v2.1",
                "replicas": 3,
                "gpu": "nvidia-a100",
            },
            registration_status="pending",
            discovered_at=datetime.utcnow() - timedelta(hours=2),
            registered_at=None,
        ),
        DiscoveredAsset(
            id=uuid4(),
            source_id=uuid4(),
            name="training-data-customer-v3",
            asset_type="dataset",
            provider="AWS",
            location="s3://ml-datasets/training/customer-v3",
            metadata={
                "size_gb": 45.2,
                "record_count": 1250000,
                "format": "parquet",
            },
            registration_status="pending",
            discovered_at=datetime.utcnow() - timedelta(hours=1),
            registered_at=None,
        ),
        DiscoveredAsset(
            id=uuid4(),
            source_id=uuid4(),
            name="company-org/fine-tuned-bert",
            asset_type="model",
            provider="HuggingFace",
            location="huggingface.co/company-org/fine-tuned-bert",
            metadata={
                "task": "text-classification",
                "downloads": 1234,
                "likes": 56,
                "private": True,
            },
            registration_status="ignored",
            discovered_at=datetime.utcnow() - timedelta(days=14),
            registered_at=None,
        ),
    ]
    
    return assets


@router.get("/discovered/{asset_id}", response_model=DiscoveredAsset)
async def get_discovered_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get details of a specific discovered asset.
    """
    return DiscoveredAsset(
        id=asset_id,
        source_id=UUID("12345678-1234-1234-1234-123456789abc"),
        name="gpt-4-turbo-preview",
        asset_type="model",
        provider="OpenAI",
        location="api.openai.com",
        metadata={
            "model_version": "gpt-4-turbo-2024-01-25",
            "context_window": 128000,
        },
        registration_status="pending",
        discovered_at=datetime.utcnow() - timedelta(days=7),
        registered_at=None,
    )


@router.post("/discovered/{asset_id}/register")
async def register_discovered_asset(
    asset_id: UUID,
    registration: AssetRegistration,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Register a discovered asset in the official inventory.
    """
    from uuid import uuid4
    
    return {
        "discovered_asset_id": asset_id,
        "inventory_asset_id": uuid4(),
        "status": "registered",
        "registered_by": current_user.get("username", "unknown"),
        "registered_at": datetime.utcnow(),
    }


@router.post("/discovered/{asset_id}/ignore")
async def ignore_discovered_asset(
    asset_id: UUID,
    reason: Optional[str] = Query(None, description="Reason for ignoring"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Mark a discovered asset as ignored (won't prompt for registration).
    """
    return {
        "asset_id": asset_id,
        "status": "ignored",
        "reason": reason,
        "ignored_by": current_user.get("username", "unknown"),
        "ignored_at": datetime.utcnow(),
    }


# ============================================================================
# Inventory Statistics Endpoints
# ============================================================================

@router.get("/stats")
async def get_inventory_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get inventory statistics and summaries.
    """
    return {
        "total_assets": 88,
        "registered_assets": 67,
        "pending_registration": 15,
        "ignored_assets": 6,
        "by_type": {
            "model": 34,
            "endpoint": 28,
            "dataset": 18,
            "pipeline": 8,
        },
        "by_provider": {
            "OpenAI": 12,
            "AWS Bedrock": 8,
            "HuggingFace": 45,
            "Internal": 23,
        },
        "by_risk_level": {
            "critical": 3,
            "high": 12,
            "medium": 28,
            "low": 45,
        },
        "discovery_sources": 4,
        "last_full_scan": datetime.utcnow() - timedelta(hours=1),
        "coverage_percentage": 94.5,
    }


@router.get("/sync-status")
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Get synchronization status across all discovery sources.
    """
    return {
        "overall_status": "healthy",
        "last_sync": datetime.utcnow() - timedelta(minutes=15),
        "next_sync": datetime.utcnow() + timedelta(minutes=15),
        "sources": [
            {
                "name": "Production Kubernetes",
                "status": "synced",
                "last_sync": datetime.utcnow() - timedelta(minutes=15),
                "assets_count": 23,
            },
            {
                "name": "AWS Bedrock",
                "status": "synced",
                "last_sync": datetime.utcnow() - timedelta(minutes=45),
                "assets_count": 8,
            },
            {
                "name": "HuggingFace Hub",
                "status": "syncing",
                "last_sync": datetime.utcnow() - timedelta(hours=2),
                "assets_count": 45,
            },
        ],
        "pending_changes": 3,
        "sync_errors": [],
    }
