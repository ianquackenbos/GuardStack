"""
Score Aggregator for GuardStack.

Aggregates pillar scores into composite safety scores using
configurable strategies (weighted average, min, max, etc.).
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np
from datetime import datetime


class AggregationStrategy(Enum):
    """Strategies for aggregating multiple scores."""
    
    WEIGHTED_AVERAGE = "weighted_average"
    ARITHMETIC_MEAN = "arithmetic_mean"
    GEOMETRIC_MEAN = "geometric_mean"
    HARMONIC_MEAN = "harmonic_mean"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    MEDIAN = "median"
    WEIGHTED_PRODUCT = "weighted_product"
    PERCENTILE_90 = "percentile_90"
    PERCENTILE_95 = "percentile_95"


@dataclass
class PillarScore:
    """Individual pillar evaluation score."""
    
    pillar_name: str
    score: float  # 0.0 to 1.0 (1.0 = best)
    confidence: float = 1.0  # 0.0 to 1.0
    weight: float = 1.0
    raw_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def weighted_score(self) -> float:
        """Calculate confidence-weighted score."""
        return self.score * self.confidence


@dataclass
class AggregatedScore:
    """Result of score aggregation."""
    
    overall_score: float
    strategy_used: AggregationStrategy
    pillar_scores: Dict[str, float]
    pillar_contributions: Dict[str, float]
    confidence: float
    risk_level: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScoreAggregator:
    """
    Aggregates individual pillar scores into composite safety scores.
    
    Supports multiple aggregation strategies and handles missing
    or low-confidence scores appropriately.
    """
    
    def __init__(
        self,
        default_strategy: AggregationStrategy = AggregationStrategy.WEIGHTED_AVERAGE,
        min_confidence_threshold: float = 0.5,
        missing_score_handling: str = "exclude",  # exclude, default, fail
        default_score: float = 0.5,
    ):
        self.default_strategy = default_strategy
        self.min_confidence_threshold = min_confidence_threshold
        self.missing_score_handling = missing_score_handling
        self.default_score = default_score
    
    def aggregate(
        self,
        pillar_scores: List[PillarScore],
        strategy: Optional[AggregationStrategy] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> AggregatedScore:
        """
        Aggregate multiple pillar scores into a single composite score.
        
        Args:
            pillar_scores: List of individual pillar scores
            strategy: Aggregation strategy (uses default if None)
            weights: Optional weight overrides per pillar
            
        Returns:
            AggregatedScore with overall score and breakdown
        """
        strategy = strategy or self.default_strategy
        
        # Filter low-confidence scores
        valid_scores = self._filter_scores(pillar_scores)
        
        if not valid_scores:
            return AggregatedScore(
                overall_score=self.default_score,
                strategy_used=strategy,
                pillar_scores={},
                pillar_contributions={},
                confidence=0.0,
                risk_level="unknown",
                metadata={"error": "No valid scores to aggregate"},
            )
        
        # Apply weight overrides
        if weights:
            for ps in valid_scores:
                if ps.pillar_name in weights:
                    ps.weight = weights[ps.pillar_name]
        
        # Calculate aggregate score
        overall_score = self._calculate_aggregate(valid_scores, strategy)
        
        # Calculate pillar contributions
        contributions = self._calculate_contributions(valid_scores, strategy)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(valid_scores)
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_score)
        
        return AggregatedScore(
            overall_score=overall_score,
            strategy_used=strategy,
            pillar_scores={ps.pillar_name: ps.score for ps in valid_scores},
            pillar_contributions=contributions,
            confidence=confidence,
            risk_level=risk_level,
            metadata={
                "num_pillars": len(valid_scores),
                "strategy": strategy.value,
            },
        )
    
    def _filter_scores(self, scores: List[PillarScore]) -> List[PillarScore]:
        """Filter out low-confidence or invalid scores."""
        valid = []
        for score in scores:
            if score.confidence >= self.min_confidence_threshold:
                valid.append(score)
            elif self.missing_score_handling == "default":
                # Use default score with original weight
                valid.append(PillarScore(
                    pillar_name=score.pillar_name,
                    score=self.default_score,
                    confidence=score.confidence,
                    weight=score.weight,
                ))
            elif self.missing_score_handling == "fail":
                raise ValueError(
                    f"Pillar {score.pillar_name} has confidence "
                    f"{score.confidence} below threshold {self.min_confidence_threshold}"
                )
            # else: exclude (skip)
        return valid
    
    def _calculate_aggregate(
        self,
        scores: List[PillarScore],
        strategy: AggregationStrategy,
    ) -> float:
        """Calculate aggregated score using specified strategy."""
        values = np.array([s.score for s in scores])
        weights = np.array([s.weight for s in scores])
        
        if strategy == AggregationStrategy.WEIGHTED_AVERAGE:
            if weights.sum() == 0:
                return float(np.mean(values))
            return float(np.average(values, weights=weights))
        
        elif strategy == AggregationStrategy.ARITHMETIC_MEAN:
            return float(np.mean(values))
        
        elif strategy == AggregationStrategy.GEOMETRIC_MEAN:
            # Handle zero values
            values = np.clip(values, 1e-10, 1.0)
            return float(np.exp(np.mean(np.log(values))))
        
        elif strategy == AggregationStrategy.HARMONIC_MEAN:
            # Handle zero values
            values = np.clip(values, 1e-10, 1.0)
            return float(len(values) / np.sum(1.0 / values))
        
        elif strategy == AggregationStrategy.MINIMUM:
            return float(np.min(values))
        
        elif strategy == AggregationStrategy.MAXIMUM:
            return float(np.max(values))
        
        elif strategy == AggregationStrategy.MEDIAN:
            return float(np.median(values))
        
        elif strategy == AggregationStrategy.WEIGHTED_PRODUCT:
            # Weighted geometric mean (product of values^weights)
            values = np.clip(values, 1e-10, 1.0)
            weights_norm = weights / weights.sum() if weights.sum() > 0 else weights
            return float(np.prod(values ** weights_norm))
        
        elif strategy == AggregationStrategy.PERCENTILE_90:
            return float(np.percentile(values, 10))  # Lower is worse
        
        elif strategy == AggregationStrategy.PERCENTILE_95:
            return float(np.percentile(values, 5))  # Lower is worse
        
        else:
            raise ValueError(f"Unknown aggregation strategy: {strategy}")
    
    def _calculate_contributions(
        self,
        scores: List[PillarScore],
        strategy: AggregationStrategy,
    ) -> Dict[str, float]:
        """Calculate each pillar's contribution to the final score."""
        contributions = {}
        total_weight = sum(s.weight for s in scores)
        
        if strategy in (
            AggregationStrategy.WEIGHTED_AVERAGE,
            AggregationStrategy.WEIGHTED_PRODUCT,
        ):
            for s in scores:
                # Contribution based on weight and score
                weight_fraction = s.weight / total_weight if total_weight > 0 else 1 / len(scores)
                contributions[s.pillar_name] = s.score * weight_fraction
        
        elif strategy == AggregationStrategy.MINIMUM:
            min_score = min(s.score for s in scores)
            for s in scores:
                contributions[s.pillar_name] = 1.0 if s.score == min_score else 0.0
        
        elif strategy == AggregationStrategy.MAXIMUM:
            max_score = max(s.score for s in scores)
            for s in scores:
                contributions[s.pillar_name] = 1.0 if s.score == max_score else 0.0
        
        else:
            # Equal contribution for mean-based strategies
            for s in scores:
                contributions[s.pillar_name] = s.score / len(scores)
        
        return contributions
    
    def _calculate_confidence(self, scores: List[PillarScore]) -> float:
        """Calculate overall confidence from individual confidences."""
        if not scores:
            return 0.0
        
        # Weighted average of confidences
        total_weight = sum(s.weight for s in scores)
        if total_weight == 0:
            return np.mean([s.confidence for s in scores])
        
        weighted_conf = sum(s.confidence * s.weight for s in scores)
        return weighted_conf / total_weight
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from aggregate score."""
        if score >= 0.9:
            return "low"
        elif score >= 0.7:
            return "medium"
        elif score >= 0.5:
            return "high"
        else:
            return "critical"
    
    def aggregate_by_category(
        self,
        pillar_scores: List[PillarScore],
        category_mapping: Dict[str, List[str]],
        strategy: AggregationStrategy = None,
    ) -> Dict[str, AggregatedScore]:
        """
        Aggregate scores by category (e.g., 'safety', 'fairness', 'privacy').
        
        Args:
            pillar_scores: All pillar scores
            category_mapping: Maps category names to pillar names
            strategy: Aggregation strategy
            
        Returns:
            Dictionary of category -> AggregatedScore
        """
        results = {}
        score_map = {ps.pillar_name: ps for ps in pillar_scores}
        
        for category, pillar_names in category_mapping.items():
            category_scores = [
                score_map[name]
                for name in pillar_names
                if name in score_map
            ]
            if category_scores:
                results[category] = self.aggregate(category_scores, strategy)
        
        return results
    
    def compare_aggregations(
        self,
        pillar_scores: List[PillarScore],
        strategies: List[AggregationStrategy] = None,
    ) -> Dict[str, AggregatedScore]:
        """
        Compare results across multiple aggregation strategies.
        
        Useful for sensitivity analysis and understanding
        how different strategies affect the final score.
        """
        if strategies is None:
            strategies = list(AggregationStrategy)
        
        return {
            strategy.value: self.aggregate(pillar_scores, strategy)
            for strategy in strategies
        }
    
    def trend_analysis(
        self,
        historical_scores: List[List[PillarScore]],
        strategy: AggregationStrategy = None,
    ) -> Dict[str, Any]:
        """
        Analyze score trends over multiple evaluations.
        
        Args:
            historical_scores: List of pillar score sets over time
            strategy: Aggregation strategy
            
        Returns:
            Trend analysis with direction, volatility, etc.
        """
        if len(historical_scores) < 2:
            return {"error": "Need at least 2 data points for trend analysis"}
        
        aggregates = [
            self.aggregate(scores, strategy)
            for scores in historical_scores
        ]
        
        overall_scores = [a.overall_score for a in aggregates]
        
        # Calculate trend metrics
        trend_direction = "improving" if overall_scores[-1] > overall_scores[0] else "declining"
        if abs(overall_scores[-1] - overall_scores[0]) < 0.05:
            trend_direction = "stable"
        
        volatility = float(np.std(overall_scores))
        avg_score = float(np.mean(overall_scores))
        
        # Calculate per-pillar trends
        pillar_trends = {}
        all_pillars = set()
        for agg in aggregates:
            all_pillars.update(agg.pillar_scores.keys())
        
        for pillar in all_pillars:
            pillar_values = [
                agg.pillar_scores.get(pillar, np.nan)
                for agg in aggregates
            ]
            pillar_values = [v for v in pillar_values if not np.isnan(v)]
            if len(pillar_values) >= 2:
                change = pillar_values[-1] - pillar_values[0]
                pillar_trends[pillar] = {
                    "change": float(change),
                    "direction": "improving" if change > 0.05 else ("declining" if change < -0.05 else "stable"),
                    "volatility": float(np.std(pillar_values)),
                }
        
        return {
            "trend_direction": trend_direction,
            "volatility": volatility,
            "average_score": avg_score,
            "latest_score": overall_scores[-1],
            "first_score": overall_scores[0],
            "num_evaluations": len(historical_scores),
            "pillar_trends": pillar_trends,
        }
