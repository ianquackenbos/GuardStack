"""
Actions Pillar

Counterfactual explanations and actionable recommendations.
"""

import logging
import time
from typing import Any, Optional

import numpy as np

from guardstack.predictive.pillars.base import BasePillar, PillarResult
from guardstack.models.core import RiskStatus

logger = logging.getLogger(__name__)


class ActionsPillar(BasePillar):
    """
    Actions pillar for predictive models.
    
    Generates:
    - Counterfactual explanations
    - Actionable recommendations
    - What-if analysis
    """
    
    pillar_name = "actions"
    pillar_category = "predictive"
    
    def __init__(
        self,
        max_counterfactuals: int = 5,
        max_samples: int = 50,
        feature_ranges: Optional[dict[str, tuple[float, float]]] = None,
        immutable_features: Optional[list[int]] = None,
    ) -> None:
        self.max_counterfactuals = max_counterfactuals
        self.max_samples = max_samples
        self.feature_ranges = feature_ranges or {}
        self.immutable_features = immutable_features or []
    
    async def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate actionability of model predictions.
        
        Metrics:
        - Counterfactual generation success rate
        - Average number of features changed
        - Plausibility of counterfactuals
        """
        start_time = time.time()
        
        findings = []
        metrics = {
            "counterfactuals_generated": 0,
            "avg_features_changed": 0.0,
            "avg_distance": 0.0,
            "coverage": 0.0,
            "plausibility_score": 0.0,
        }
        
        # Sample negative predictions (where counterfactuals are useful)
        predictions = model.predict(X)
        negative_mask = predictions == 0  # Assuming binary classification
        
        if not negative_mask.any():
            # No negative predictions to generate counterfactuals for
            findings.append(self._create_finding(
                finding_type="no_negative_predictions",
                severity="low",
                message="No negative predictions found for counterfactual analysis",
            ))
            score = 100.0  # Default good score
        else:
            X_negative = X[negative_mask][:self.max_samples]
            
            # Generate counterfactuals
            cf_results = await self._generate_counterfactuals(
                model, X_negative, X
            )
            
            metrics.update(cf_results["metrics"])
            findings.extend(cf_results.get("findings", []))
            
            score = self._calculate_score(metrics)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PillarResult(
            pillar_name=self.pillar_name,
            score=score,
            status=self._score_to_status(score),
            findings=findings,
            metrics=metrics,
            details={
                "max_counterfactuals": self.max_counterfactuals,
                "immutable_features": self.immutable_features,
            },
            execution_time_ms=execution_time,
            samples_tested=self.max_samples,
        )
    
    async def _generate_counterfactuals(
        self,
        model: Any,
        X_negative: np.ndarray,
        X_all: np.ndarray,
    ) -> dict[str, Any]:
        """Generate counterfactual explanations."""
        results = {
            "metrics": {
                "counterfactuals_generated": 0,
                "avg_features_changed": 0.0,
                "avg_distance": 0.0,
                "coverage": 0.0,
                "plausibility_score": 0.0,
            },
            "findings": [],
            "counterfactuals": [],
        }
        
        # Calculate feature bounds from data
        feature_mins = X_all.min(axis=0)
        feature_maxs = X_all.max(axis=0)
        
        counterfactuals = []
        features_changed_list = []
        distances = []
        
        for i, x in enumerate(X_negative):
            cf = await self._find_counterfactual(
                model, x, feature_mins, feature_maxs
            )
            
            if cf is not None:
                counterfactuals.append(cf)
                
                # Calculate features changed
                changed = np.sum(np.abs(cf - x) > 1e-6)
                features_changed_list.append(changed)
                
                # Calculate normalized distance
                ranges = feature_maxs - feature_mins
                ranges[ranges == 0] = 1
                normalized_diff = np.abs(cf - x) / ranges
                distances.append(np.mean(normalized_diff))
                
                results["counterfactuals"].append({
                    "original": x.tolist(),
                    "counterfactual": cf.tolist(),
                    "features_changed": int(changed),
                })
        
        if counterfactuals:
            results["metrics"]["counterfactuals_generated"] = len(counterfactuals)
            results["metrics"]["coverage"] = len(counterfactuals) / len(X_negative)
            results["metrics"]["avg_features_changed"] = np.mean(features_changed_list)
            results["metrics"]["avg_distance"] = np.mean(distances)
            
            # Calculate plausibility (proximity to training data)
            plausibility = self._calculate_plausibility(
                np.array(counterfactuals), X_all
            )
            results["metrics"]["plausibility_score"] = plausibility
            
            # Add findings
            if results["metrics"]["avg_features_changed"] > X_negative.shape[1] * 0.5:
                results["findings"].append(self._create_finding(
                    finding_type="many_changes_required",
                    severity="medium",
                    message="Counterfactuals require changing many features",
                    avg_features=float(results["metrics"]["avg_features_changed"]),
                ))
            
            if plausibility < 0.5:
                results["findings"].append(self._create_finding(
                    finding_type="low_plausibility",
                    severity="high",
                    message="Generated counterfactuals may not be realistic",
                    plausibility_score=plausibility,
                ))
        else:
            results["findings"].append(self._create_finding(
                finding_type="no_counterfactuals",
                severity="high",
                message="Unable to generate any counterfactuals",
            ))
        
        return results
    
    async def _find_counterfactual(
        self,
        model: Any,
        x: np.ndarray,
        feature_mins: np.ndarray,
        feature_maxs: np.ndarray,
        max_iterations: int = 100,
    ) -> Optional[np.ndarray]:
        """Find a counterfactual for a single instance."""
        cf = x.copy()
        n_features = len(x)
        
        for _ in range(max_iterations):
            # Check current prediction
            pred = model.predict(cf.reshape(1, -1))[0]
            if pred == 1:
                return cf
            
            # Try modifying a random feature
            feature_idx = np.random.randint(n_features)
            
            # Skip immutable features
            if feature_idx in self.immutable_features:
                continue
            
            # Calculate step size
            feature_range = feature_maxs[feature_idx] - feature_mins[feature_idx]
            step = feature_range * 0.1
            
            # Try positive and negative directions
            for direction in [1, -1]:
                cf_new = cf.copy()
                cf_new[feature_idx] += direction * step
                
                # Clip to valid range
                cf_new[feature_idx] = np.clip(
                    cf_new[feature_idx],
                    feature_mins[feature_idx],
                    feature_maxs[feature_idx],
                )
                
                new_pred = model.predict(cf_new.reshape(1, -1))[0]
                if new_pred == 1:
                    return cf_new
                
                # Check if we're moving in the right direction
                if hasattr(model, "predict_proba"):
                    old_prob = model.predict_proba(cf.reshape(1, -1))[0][1]
                    new_prob = model.predict_proba(cf_new.reshape(1, -1))[0][1]
                    if new_prob > old_prob:
                        cf = cf_new
        
        return None
    
    def _calculate_plausibility(
        self,
        counterfactuals: np.ndarray,
        X_train: np.ndarray,
    ) -> float:
        """Calculate plausibility score based on proximity to training data."""
        if len(counterfactuals) == 0:
            return 0.0
        
        plausibilities = []
        
        for cf in counterfactuals:
            # Calculate distance to nearest training point
            distances = np.linalg.norm(X_train - cf, axis=1)
            min_distance = distances.min()
            
            # Calculate average distance between training points
            avg_train_distance = np.mean([
                np.linalg.norm(X_train - X_train[i], axis=1).mean()
                for i in range(min(50, len(X_train)))
            ])
            
            # Plausibility is high if CF is close to training data
            plausibility = np.exp(-min_distance / (avg_train_distance + 1e-6))
            plausibilities.append(plausibility)
        
        return float(np.mean(plausibilities))
    
    def _calculate_score(self, metrics: dict[str, Any]) -> float:
        """Calculate overall actions score."""
        score = 0.0
        
        # Coverage score (40%)
        coverage = metrics.get("coverage", 0)
        score += coverage * 40
        
        # Plausibility score (40%)
        plausibility = metrics.get("plausibility_score", 0)
        score += plausibility * 40
        
        # Sparsity score (20%) - fewer features changed is better
        n_features = metrics.get("avg_features_changed", 0)
        if n_features > 0:
            # Assuming average of 10 features, normalize
            sparsity = max(0, 1 - n_features / 10)
            score += sparsity * 20
        else:
            score += 20
        
        return min(100, score)
