"""
GuardStack Scoring Module.

Provides score aggregation, normalization, and threshold management
for AI safety evaluations across predictive, generative, and agentic models.
"""

from .aggregator import ScoreAggregator, AggregationStrategy
from .normalizer import ScoreNormalizer, NormalizationMethod
from .thresholds import ThresholdManager, ThresholdConfig, RiskLevel
from .weights import WeightManager, PillarWeights, WeightPreset

__all__ = [
    # Aggregator
    "ScoreAggregator",
    "AggregationStrategy",
    # Normalizer
    "ScoreNormalizer",
    "NormalizationMethod",
    # Thresholds
    "ThresholdManager",
    "ThresholdConfig",
    "RiskLevel",
    # Weights
    "WeightManager",
    "PillarWeights",
    "WeightPreset",
]
