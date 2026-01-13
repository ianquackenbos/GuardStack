"""
AI Asset Inventory

Track and manage AI assets for security scanning.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


class AssetType(Enum):
    """Types of AI assets."""
    LLM_ENDPOINT = "llm_endpoint"
    ML_MODEL = "ml_model"
    TRAINING_DATA = "training_data"
    VECTOR_DB = "vector_db"
    AGENT = "agent"
    PIPELINE = "pipeline"
    NOTEBOOK = "notebook"


class AssetStatus(Enum):
    """Asset operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    TESTING = "testing"


@dataclass
class AIAsset:
    """Represents an AI asset in the inventory."""
    
    asset_id: str
    name: str
    asset_type: str
    status: AssetStatus = AssetStatus.ACTIVE
    owner: Optional[str] = None
    team: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Connection details
    endpoint_url: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    
    # Classification
    data_classification: Optional[str] = None  # public, internal, confidential, restricted
    risk_level: Optional[str] = None  # low, medium, high, critical
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "asset_type": self.asset_type,
            "status": self.status.value,
            "owner": self.owner,
            "team": self.team,
            "description": self.description,
            "tags": self.tags,
            "config": self.config,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "endpoint_url": self.endpoint_url,
            "provider": self.provider,
            "model_name": self.model_name,
            "data_classification": self.data_classification,
            "risk_level": self.risk_level,
        }


class AIInventory:
    """
    Inventory of AI assets.
    
    Provides:
    - Asset registration
    - Discovery
    - Classification
    - Relationship tracking
    """
    
    def __init__(self) -> None:
        self._assets: dict[str, AIAsset] = {}
        self._relationships: dict[str, list[str]] = {}
    
    def register(
        self,
        name: str,
        asset_type: str | AssetType,
        **kwargs: Any,
    ) -> AIAsset:
        """Register a new AI asset."""
        asset_id = kwargs.pop("asset_id", str(uuid.uuid4()))
        
        if isinstance(asset_type, AssetType):
            asset_type = asset_type.value
        
        asset = AIAsset(
            asset_id=asset_id,
            name=name,
            asset_type=asset_type,
            **kwargs,
        )
        
        self._assets[asset_id] = asset
        return asset
    
    def get(self, asset_id: str) -> Optional[AIAsset]:
        """Get an asset by ID."""
        return self._assets.get(asset_id)
    
    def update(self, asset_id: str, **updates: Any) -> Optional[AIAsset]:
        """Update an existing asset."""
        asset = self._assets.get(asset_id)
        if not asset:
            return None
        
        for key, value in updates.items():
            if hasattr(asset, key):
                setattr(asset, key, value)
        
        asset.updated_at = datetime.utcnow().isoformat()
        return asset
    
    def delete(self, asset_id: str) -> bool:
        """Delete an asset from inventory."""
        if asset_id in self._assets:
            del self._assets[asset_id]
            # Clean up relationships
            if asset_id in self._relationships:
                del self._relationships[asset_id]
            for related_id in self._relationships:
                if asset_id in self._relationships[related_id]:
                    self._relationships[related_id].remove(asset_id)
            return True
        return False
    
    def list_assets(
        self,
        asset_type: Optional[str | AssetType] = None,
        status: Optional[AssetStatus] = None,
        tags: Optional[list[str]] = None,
        owner: Optional[str] = None,
        team: Optional[str] = None,
    ) -> list[AIAsset]:
        """List assets with optional filters."""
        assets = list(self._assets.values())
        
        if asset_type:
            if isinstance(asset_type, AssetType):
                asset_type = asset_type.value
            assets = [a for a in assets if a.asset_type == asset_type]
        
        if status:
            assets = [a for a in assets if a.status == status]
        
        if tags:
            assets = [a for a in assets if any(t in a.tags for t in tags)]
        
        if owner:
            assets = [a for a in assets if a.owner == owner]
        
        if team:
            assets = [a for a in assets if a.team == team]
        
        return assets
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
    ) -> bool:
        """Add a relationship between assets."""
        if source_id not in self._assets or target_id not in self._assets:
            return False
        
        if source_id not in self._relationships:
            self._relationships[source_id] = []
        
        if target_id not in self._relationships[source_id]:
            self._relationships[source_id].append(target_id)
        
        return True
    
    def get_related(self, asset_id: str) -> list[AIAsset]:
        """Get assets related to the given asset."""
        related_ids = self._relationships.get(asset_id, [])
        return [self._assets[rid] for rid in related_ids if rid in self._assets]
    
    def search(self, query: str) -> list[AIAsset]:
        """Search assets by name or description."""
        query_lower = query.lower()
        results = []
        
        for asset in self._assets.values():
            if query_lower in asset.name.lower():
                results.append(asset)
            elif asset.description and query_lower in asset.description.lower():
                results.append(asset)
            elif any(query_lower in tag.lower() for tag in asset.tags):
                results.append(asset)
        
        return results
    
    def get_statistics(self) -> dict[str, Any]:
        """Get inventory statistics."""
        assets = list(self._assets.values())
        
        # Count by type
        type_counts: dict[str, int] = {}
        for asset in assets:
            type_counts[asset.asset_type] = type_counts.get(asset.asset_type, 0) + 1
        
        # Count by status
        status_counts: dict[str, int] = {}
        for asset in assets:
            status = asset.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by risk level
        risk_counts: dict[str, int] = {}
        for asset in assets:
            risk = asset.risk_level or "unclassified"
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        return {
            "total_assets": len(assets),
            "by_type": type_counts,
            "by_status": status_counts,
            "by_risk_level": risk_counts,
            "total_relationships": sum(
                len(rels) for rels in self._relationships.values()
            ),
        }
    
    def export(self) -> list[dict[str, Any]]:
        """Export inventory to list of dicts."""
        return [asset.to_dict() for asset in self._assets.values()]
    
    def import_assets(self, data: list[dict[str, Any]]) -> int:
        """Import assets from list of dicts."""
        imported = 0
        
        for item in data:
            try:
                asset_type = item.pop("asset_type")
                name = item.pop("name")
                
                # Convert status string to enum
                if "status" in item and isinstance(item["status"], str):
                    item["status"] = AssetStatus(item["status"])
                
                self.register(name=name, asset_type=asset_type, **item)
                imported += 1
            except Exception:
                continue
        
        return imported


class AssetDiscovery:
    """
    Automatic discovery of AI assets.
    """
    
    def __init__(self, inventory: AIInventory) -> None:
        self.inventory = inventory
    
    async def discover_kubernetes(
        self,
        namespace: Optional[str] = None,
    ) -> list[AIAsset]:
        """Discover AI assets in Kubernetes cluster."""
        discovered = []
        
        # This would use kubernetes client to find:
        # - Deployments with AI-related labels
        # - Services exposing model endpoints
        # - ConfigMaps with model configurations
        
        # Placeholder implementation
        # In real implementation, would use kubernetes.client
        
        return discovered
    
    async def discover_cloud_endpoints(
        self,
        providers: Optional[list[str]] = None,
    ) -> list[AIAsset]:
        """Discover cloud AI service endpoints."""
        discovered = []
        
        # This would check for:
        # - OpenAI API usage
        # - Azure OpenAI endpoints
        # - AWS Bedrock endpoints
        # - Google Vertex AI endpoints
        
        return discovered
    
    async def discover_local_models(
        self,
        search_paths: Optional[list[str]] = None,
    ) -> list[AIAsset]:
        """Discover locally deployed models."""
        discovered = []
        
        # This would scan for:
        # - Ollama running instances
        # - Local model files (GGUF, ONNX, etc.)
        # - MLflow model registry
        
        return discovered
