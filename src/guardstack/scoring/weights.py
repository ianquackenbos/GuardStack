"""
Weight Manager for GuardStack.

Manages pillar weights for score aggregation, supporting
industry presets and custom weight configurations.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class WeightPreset(Enum):
    """Pre-defined weight configurations for different contexts."""
    
    BALANCED = "balanced"
    SAFETY_FOCUSED = "safety_focused"
    FAIRNESS_FOCUSED = "fairness_focused"
    PRIVACY_FOCUSED = "privacy_focused"
    PERFORMANCE_FOCUSED = "performance_focused"
    REGULATORY_EU_AI_ACT = "regulatory_eu_ai_act"
    REGULATORY_SOC2 = "regulatory_soc2"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    CONTENT_MODERATION = "content_moderation"


@dataclass
class PillarWeights:
    """Weight configuration for evaluation pillars."""
    
    name: str
    weights: Dict[str, float]
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Normalize weights to sum to 1.0."""
        self._normalize()
    
    def _normalize(self) -> None:
        """Normalize weights to sum to 1.0."""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def get_weight(self, pillar: str, default: float = 0.0) -> float:
        """Get weight for a pillar."""
        return self.weights.get(pillar, default)
    
    def set_weight(self, pillar: str, weight: float) -> None:
        """Set weight for a pillar and re-normalize."""
        self.weights[pillar] = weight
        self._normalize()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "weights": self.weights,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PillarWeights":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            weights=data["weights"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )


class WeightManager:
    """
    Manages pillar weights for score aggregation.
    
    Provides preset weights for common scenarios and supports
    custom weight configurations.
    """
    
    # Pre-defined weight configurations
    PRESETS: Dict[WeightPreset, PillarWeights] = {
        WeightPreset.BALANCED: PillarWeights(
            name="balanced",
            weights={
                "accuracy": 1.0,
                "robustness": 1.0,
                "fairness": 1.0,
                "privacy": 1.0,
                "security": 1.0,
                "explainability": 1.0,
                "toxicity": 1.0,
                "groundedness": 1.0,
            },
            description="Equal weight to all pillars",
        ),
        
        WeightPreset.SAFETY_FOCUSED: PillarWeights(
            name="safety_focused",
            weights={
                "accuracy": 0.5,
                "robustness": 1.5,
                "fairness": 1.0,
                "privacy": 1.0,
                "security": 2.0,
                "explainability": 0.5,
                "toxicity": 2.0,
                "groundedness": 1.0,
            },
            description="Prioritizes security, robustness, and content safety",
        ),
        
        WeightPreset.FAIRNESS_FOCUSED: PillarWeights(
            name="fairness_focused",
            weights={
                "accuracy": 0.8,
                "robustness": 0.8,
                "fairness": 3.0,
                "privacy": 1.0,
                "security": 0.8,
                "explainability": 1.5,
                "toxicity": 1.0,
                "groundedness": 0.8,
            },
            description="Prioritizes fairness and explainability",
        ),
        
        WeightPreset.PRIVACY_FOCUSED: PillarWeights(
            name="privacy_focused",
            weights={
                "accuracy": 0.5,
                "robustness": 0.8,
                "fairness": 1.0,
                "privacy": 3.0,
                "security": 1.5,
                "explainability": 0.8,
                "toxicity": 0.8,
                "groundedness": 0.8,
            },
            description="Prioritizes privacy and security",
        ),
        
        WeightPreset.PERFORMANCE_FOCUSED: PillarWeights(
            name="performance_focused",
            weights={
                "accuracy": 3.0,
                "robustness": 1.5,
                "fairness": 0.8,
                "privacy": 0.5,
                "security": 0.8,
                "explainability": 0.5,
                "toxicity": 0.5,
                "groundedness": 1.5,
            },
            description="Prioritizes accuracy and performance metrics",
        ),
        
        WeightPreset.REGULATORY_EU_AI_ACT: PillarWeights(
            name="regulatory_eu_ai_act",
            weights={
                "accuracy": 1.0,
                "robustness": 1.5,
                "fairness": 2.0,
                "privacy": 2.0,
                "security": 1.5,
                "explainability": 2.5,
                "toxicity": 1.5,
                "groundedness": 1.0,
                # EU AI Act specific
                "human_oversight": 2.0,
                "transparency": 2.5,
                "data_governance": 2.0,
            },
            description="Weights aligned with EU AI Act requirements",
            metadata={
                "regulation": "EU AI Act",
                "articles": ["Article 9", "Article 10", "Article 13", "Article 14", "Article 15"],
            },
        ),
        
        WeightPreset.REGULATORY_SOC2: PillarWeights(
            name="regulatory_soc2",
            weights={
                "accuracy": 0.8,
                "robustness": 1.0,
                "fairness": 0.8,
                "privacy": 2.5,
                "security": 3.0,
                "explainability": 1.0,
                "toxicity": 0.5,
                "groundedness": 0.5,
                # SOC2 specific
                "availability": 2.0,
                "confidentiality": 2.5,
                "processing_integrity": 2.0,
            },
            description="Weights aligned with SOC2 Trust Service Criteria",
            metadata={
                "framework": "SOC2",
                "criteria": ["Security", "Availability", "Processing Integrity", "Confidentiality", "Privacy"],
            },
        ),
        
        WeightPreset.HEALTHCARE: PillarWeights(
            name="healthcare",
            weights={
                "accuracy": 3.0,
                "robustness": 2.0,
                "fairness": 2.5,
                "privacy": 3.0,  # HIPAA
                "security": 2.0,
                "explainability": 2.5,
                "toxicity": 1.0,
                "groundedness": 2.5,
                # Healthcare specific
                "clinical_validity": 3.0,
                "patient_safety": 3.0,
            },
            description="Weights for healthcare AI applications (HIPAA compliant)",
            metadata={
                "industry": "healthcare",
                "compliance": ["HIPAA", "FDA 21 CFR Part 11"],
            },
        ),
        
        WeightPreset.FINANCE: PillarWeights(
            name="finance",
            weights={
                "accuracy": 2.5,
                "robustness": 2.0,
                "fairness": 3.0,  # Fair lending
                "privacy": 2.0,
                "security": 2.5,
                "explainability": 2.5,  # Model governance
                "toxicity": 0.5,
                "groundedness": 1.5,
                # Finance specific
                "model_governance": 2.5,
                "audit_trail": 2.0,
            },
            description="Weights for financial services AI (fair lending compliance)",
            metadata={
                "industry": "finance",
                "compliance": ["ECOA", "FCRA", "SR 11-7"],
            },
        ),
        
        WeightPreset.CONTENT_MODERATION: PillarWeights(
            name="content_moderation",
            weights={
                "accuracy": 1.5,
                "robustness": 1.5,
                "fairness": 2.0,
                "privacy": 1.0,
                "security": 1.0,
                "explainability": 1.5,
                "toxicity": 3.0,
                "groundedness": 0.5,
                # Content specific
                "hate_speech_detection": 3.0,
                "misinformation_detection": 2.5,
                "violence_detection": 2.5,
            },
            description="Weights for content moderation systems",
            metadata={
                "use_case": "content_moderation",
                "platforms": ["social_media", "forums", "user_generated_content"],
            },
        ),
    }
    
    def __init__(
        self,
        default_preset: WeightPreset = WeightPreset.BALANCED,
        custom_weights: Optional[Dict[str, PillarWeights]] = None,
    ):
        self.default_preset = default_preset
        self.custom_weights: Dict[str, PillarWeights] = custom_weights or {}
    
    def get_weights(
        self,
        preset: Optional[WeightPreset] = None,
        custom_name: Optional[str] = None,
    ) -> PillarWeights:
        """
        Get weights by preset or custom name.
        
        Args:
            preset: Pre-defined weight preset
            custom_name: Name of custom weight configuration
            
        Returns:
            PillarWeights configuration
        """
        if custom_name and custom_name in self.custom_weights:
            return self.custom_weights[custom_name]
        
        preset = preset or self.default_preset
        return self.PRESETS.get(preset, self.PRESETS[WeightPreset.BALANCED])
    
    def get_weight_dict(
        self,
        preset: Optional[WeightPreset] = None,
        custom_name: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Get weights as a simple dictionary.
        
        Args:
            preset: Pre-defined weight preset
            custom_name: Name of custom weight configuration
            
        Returns:
            Dictionary of pillar -> weight
        """
        return self.get_weights(preset, custom_name).weights
    
    def create_custom_weights(
        self,
        name: str,
        weights: Dict[str, float],
        description: str = "",
        base_preset: Optional[WeightPreset] = None,
    ) -> PillarWeights:
        """
        Create custom weight configuration.
        
        Args:
            name: Unique name for the configuration
            weights: Pillar weights (will be normalized)
            description: Description of the configuration
            base_preset: Optional preset to use as base
            
        Returns:
            Created PillarWeights
        """
        if base_preset:
            base = self.PRESETS[base_preset]
            merged_weights = {**base.weights, **weights}
        else:
            merged_weights = weights
        
        pillar_weights = PillarWeights(
            name=name,
            weights=merged_weights,
            description=description,
        )
        
        self.custom_weights[name] = pillar_weights
        return pillar_weights
    
    def update_custom_weights(
        self,
        name: str,
        updates: Dict[str, float],
    ) -> Optional[PillarWeights]:
        """
        Update existing custom weight configuration.
        
        Args:
            name: Name of custom configuration
            updates: Weight updates to apply
            
        Returns:
            Updated PillarWeights or None if not found
        """
        if name not in self.custom_weights:
            return None
        
        config = self.custom_weights[name]
        config.weights.update(updates)
        config._normalize()
        return config
    
    def delete_custom_weights(self, name: str) -> Optional[PillarWeights]:
        """Delete custom weight configuration."""
        return self.custom_weights.pop(name, None)
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """List all available presets."""
        return [
            {
                "preset": preset.value,
                "name": weights.name,
                "description": weights.description,
                "pillars": list(weights.weights.keys()),
            }
            for preset, weights in self.PRESETS.items()
        ]
    
    def list_custom(self) -> List[Dict[str, Any]]:
        """List all custom configurations."""
        return [
            {
                "name": name,
                "description": weights.description,
                "pillars": list(weights.weights.keys()),
                "created_at": weights.created_at.isoformat(),
            }
            for name, weights in self.custom_weights.items()
        ]
    
    def recommend_preset(
        self,
        industry: Optional[str] = None,
        regulation: Optional[str] = None,
        priorities: Optional[List[str]] = None,
    ) -> WeightPreset:
        """
        Recommend a weight preset based on context.
        
        Args:
            industry: Industry vertical
            regulation: Regulatory framework
            priorities: List of priority pillars
            
        Returns:
            Recommended WeightPreset
        """
        # Industry-based recommendations
        if industry:
            industry_map = {
                "healthcare": WeightPreset.HEALTHCARE,
                "medical": WeightPreset.HEALTHCARE,
                "finance": WeightPreset.FINANCE,
                "banking": WeightPreset.FINANCE,
                "insurance": WeightPreset.FINANCE,
                "social_media": WeightPreset.CONTENT_MODERATION,
                "content": WeightPreset.CONTENT_MODERATION,
            }
            if industry.lower() in industry_map:
                return industry_map[industry.lower()]
        
        # Regulation-based recommendations
        if regulation:
            regulation_map = {
                "eu_ai_act": WeightPreset.REGULATORY_EU_AI_ACT,
                "soc2": WeightPreset.REGULATORY_SOC2,
                "hipaa": WeightPreset.HEALTHCARE,
                "gdpr": WeightPreset.PRIVACY_FOCUSED,
                "ccpa": WeightPreset.PRIVACY_FOCUSED,
            }
            if regulation.lower() in regulation_map:
                return regulation_map[regulation.lower()]
        
        # Priority-based recommendations
        if priorities:
            priorities_lower = [p.lower() for p in priorities]
            if "fairness" in priorities_lower or "bias" in priorities_lower:
                return WeightPreset.FAIRNESS_FOCUSED
            if "privacy" in priorities_lower:
                return WeightPreset.PRIVACY_FOCUSED
            if "security" in priorities_lower or "safety" in priorities_lower:
                return WeightPreset.SAFETY_FOCUSED
            if "performance" in priorities_lower or "accuracy" in priorities_lower:
                return WeightPreset.PERFORMANCE_FOCUSED
        
        return WeightPreset.BALANCED
    
    def blend_presets(
        self,
        presets: List[WeightPreset],
        ratios: Optional[List[float]] = None,
        name: str = "blended",
    ) -> PillarWeights:
        """
        Blend multiple presets together.
        
        Args:
            presets: List of presets to blend
            ratios: Optional blend ratios (equal if not provided)
            name: Name for the blended configuration
            
        Returns:
            Blended PillarWeights
        """
        if not presets:
            return self.PRESETS[self.default_preset]
        
        if ratios is None:
            ratios = [1.0] * len(presets)
        
        # Normalize ratios
        total_ratio = sum(ratios)
        ratios = [r / total_ratio for r in ratios]
        
        # Collect all pillars
        all_pillars = set()
        for preset in presets:
            all_pillars.update(self.PRESETS[preset].weights.keys())
        
        # Blend weights
        blended = {}
        for pillar in all_pillars:
            blended[pillar] = sum(
                self.PRESETS[preset].weights.get(pillar, 0) * ratio
                for preset, ratio in zip(presets, ratios)
            )
        
        return PillarWeights(
            name=name,
            weights=blended,
            description=f"Blend of {', '.join(p.value for p in presets)}",
            metadata={
                "source_presets": [p.value for p in presets],
                "blend_ratios": ratios,
            },
        )
    
    def compare_weights(
        self,
        weight_configs: List[PillarWeights],
    ) -> Dict[str, Any]:
        """
        Compare multiple weight configurations.
        
        Args:
            weight_configs: List of weight configurations
            
        Returns:
            Comparison analysis
        """
        if not weight_configs:
            return {"error": "No configurations to compare"}
        
        # Collect all pillars
        all_pillars = set()
        for config in weight_configs:
            all_pillars.update(config.weights.keys())
        
        # Build comparison matrix
        comparison = {}
        for pillar in sorted(all_pillars):
            comparison[pillar] = {
                config.name: config.weights.get(pillar, 0)
                for config in weight_configs
            }
        
        # Find major differences
        differences = []
        for pillar, values in comparison.items():
            vals = list(values.values())
            if max(vals) - min(vals) > 0.1:  # Significant difference
                differences.append({
                    "pillar": pillar,
                    "range": [min(vals), max(vals)],
                    "values": values,
                })
        
        return {
            "configurations": [c.name for c in weight_configs],
            "pillar_comparison": comparison,
            "significant_differences": differences,
        }
    
    def export_all(self) -> Dict[str, Any]:
        """Export all configurations."""
        return {
            "default_preset": self.default_preset.value,
            "presets": {
                preset.value: weights.to_dict()
                for preset, weights in self.PRESETS.items()
            },
            "custom": {
                name: weights.to_dict()
                for name, weights in self.custom_weights.items()
            },
        }
    
    def import_custom(self, data: Dict[str, Any]) -> None:
        """Import custom configurations."""
        if "custom" in data:
            for name, config in data["custom"].items():
                self.custom_weights[name] = PillarWeights.from_dict(config)
        
        if "default_preset" in data:
            self.default_preset = WeightPreset(data["default_preset"])
