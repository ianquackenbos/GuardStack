"""
Fairness Pillar

Bias detection and fairness metrics for predictive models.
"""

import logging
import time
from typing import Any, Optional

import numpy as np

from guardstack.predictive.pillars.base import BasePillar, PillarResult
from guardstack.models.core import RiskStatus

logger = logging.getLogger(__name__)


class FairnessPillar(BasePillar):
    """
    Fairness pillar for predictive models.
    
    Evaluates:
    - Demographic parity
    - Equalized odds
    - Equal opportunity
    - Disparate impact
    - Calibration across groups
    """
    
    pillar_name = "fairness"
    pillar_category = "predictive"
    
    def __init__(
        self,
        disparate_impact_threshold: float = 0.8,
        demographic_parity_threshold: float = 0.1,
        equalized_odds_threshold: float = 0.1,
    ) -> None:
        self.disparate_impact_threshold = disparate_impact_threshold
        self.demographic_parity_threshold = demographic_parity_threshold
        self.equalized_odds_threshold = equalized_odds_threshold
    
    async def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate model fairness across protected groups.
        
        Requires sensitive_features dict mapping attribute names to arrays.
        """
        start_time = time.time()
        
        findings = []
        metrics = {
            "attributes_analyzed": [],
            "fairness_metrics": {},
            "overall_fairness_score": 0.0,
        }
        
        if not sensitive_features:
            findings.append(self._create_finding(
                finding_type="no_sensitive_features",
                severity="medium",
                message="No sensitive features provided for fairness analysis",
            ))
            score = 50.0  # Neutral score when no analysis possible
        else:
            predictions = model.predict(X)
            
            # Calculate fairness metrics for each sensitive attribute
            for attr_name, attr_values in sensitive_features.items():
                metrics["attributes_analyzed"].append(attr_name)
                
                attr_metrics = await self._analyze_attribute(
                    predictions, y, attr_values, attr_name
                )
                
                metrics["fairness_metrics"][attr_name] = attr_metrics
                findings.extend(attr_metrics.get("findings", []))
            
            # Calculate overall fairness score
            score = self._calculate_overall_score(metrics["fairness_metrics"])
            metrics["overall_fairness_score"] = score
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PillarResult(
            pillar_name=self.pillar_name,
            score=score,
            status=self._score_to_status(score),
            findings=findings,
            metrics=metrics,
            details={
                "thresholds": {
                    "disparate_impact": self.disparate_impact_threshold,
                    "demographic_parity": self.demographic_parity_threshold,
                    "equalized_odds": self.equalized_odds_threshold,
                },
            },
            execution_time_ms=execution_time,
            samples_tested=len(X),
        )
    
    async def _analyze_attribute(
        self,
        predictions: np.ndarray,
        y_true: np.ndarray,
        sensitive_attr: np.ndarray,
        attr_name: str,
    ) -> dict[str, Any]:
        """Analyze fairness for a single sensitive attribute."""
        results = {
            "demographic_parity": None,
            "disparate_impact": None,
            "equalized_odds": None,
            "equal_opportunity": None,
            "findings": [],
        }
        
        unique_groups = np.unique(sensitive_attr)
        
        if len(unique_groups) < 2:
            results["findings"].append(self._create_finding(
                finding_type="single_group",
                severity="low",
                message=f"Attribute '{attr_name}' has only one group",
                attribute=attr_name,
            ))
            return results
        
        # Calculate metrics for each group
        group_metrics = {}
        
        for group in unique_groups:
            mask = sensitive_attr == group
            group_preds = predictions[mask]
            group_true = y_true[mask]
            
            # Positive rate
            pos_rate = np.mean(group_preds == 1) if len(group_preds) > 0 else 0
            
            # True positive rate (recall)
            pos_mask = group_true == 1
            if pos_mask.any():
                tpr = np.mean(group_preds[pos_mask] == 1)
            else:
                tpr = 0
            
            # False positive rate
            neg_mask = group_true == 0
            if neg_mask.any():
                fpr = np.mean(group_preds[neg_mask] == 1)
            else:
                fpr = 0
            
            group_metrics[str(group)] = {
                "count": int(mask.sum()),
                "positive_rate": float(pos_rate),
                "tpr": float(tpr),
                "fpr": float(fpr),
            }
        
        results["group_metrics"] = group_metrics
        
        # Calculate aggregate metrics
        positive_rates = [m["positive_rate"] for m in group_metrics.values()]
        tprs = [m["tpr"] for m in group_metrics.values()]
        fprs = [m["fpr"] for m in group_metrics.values()]
        
        # Demographic parity (difference in positive rates)
        dp_diff = max(positive_rates) - min(positive_rates) if positive_rates else 0
        results["demographic_parity"] = 1 - dp_diff
        
        if dp_diff > self.demographic_parity_threshold:
            results["findings"].append(self._create_finding(
                finding_type="demographic_parity_violation",
                severity="high",
                message=f"Demographic parity violation for '{attr_name}'",
                attribute=attr_name,
                difference=float(dp_diff),
                threshold=self.demographic_parity_threshold,
            ))
        
        # Disparate impact (ratio of positive rates)
        if max(positive_rates) > 0:
            di_ratio = min(positive_rates) / max(positive_rates)
        else:
            di_ratio = 1.0
        results["disparate_impact"] = di_ratio
        
        if di_ratio < self.disparate_impact_threshold:
            results["findings"].append(self._create_finding(
                finding_type="disparate_impact",
                severity="critical",
                message=f"Disparate impact detected for '{attr_name}'",
                attribute=attr_name,
                ratio=float(di_ratio),
                threshold=self.disparate_impact_threshold,
            ))
        
        # Equalized odds (difference in TPR and FPR)
        tpr_diff = max(tprs) - min(tprs) if tprs else 0
        fpr_diff = max(fprs) - min(fprs) if fprs else 0
        eo_diff = max(tpr_diff, fpr_diff)
        results["equalized_odds"] = 1 - eo_diff
        
        if eo_diff > self.equalized_odds_threshold:
            results["findings"].append(self._create_finding(
                finding_type="equalized_odds_violation",
                severity="high",
                message=f"Equalized odds violation for '{attr_name}'",
                attribute=attr_name,
                tpr_difference=float(tpr_diff),
                fpr_difference=float(fpr_diff),
                threshold=self.equalized_odds_threshold,
            ))
        
        # Equal opportunity (difference in TPR only)
        results["equal_opportunity"] = 1 - tpr_diff
        
        return results
    
    def _calculate_overall_score(
        self,
        fairness_metrics: dict[str, dict[str, Any]],
    ) -> float:
        """Calculate overall fairness score from attribute metrics."""
        if not fairness_metrics:
            return 50.0
        
        scores = []
        
        for attr_metrics in fairness_metrics.values():
            attr_score = 0
            count = 0
            
            for metric in ["demographic_parity", "disparate_impact", 
                          "equalized_odds", "equal_opportunity"]:
                value = attr_metrics.get(metric)
                if value is not None:
                    attr_score += value * 100
                    count += 1
            
            if count > 0:
                scores.append(attr_score / count)
        
        return np.mean(scores) if scores else 50.0


class FairnessMetricsCalculator:
    """
    Utility class for calculating fairness metrics.
    
    Can be used independently of the pillar for ad-hoc analysis.
    """
    
    @staticmethod
    def demographic_parity_difference(
        predictions: np.ndarray,
        sensitive_attr: np.ndarray,
    ) -> float:
        """Calculate demographic parity difference."""
        groups = np.unique(sensitive_attr)
        positive_rates = []
        
        for group in groups:
            mask = sensitive_attr == group
            rate = np.mean(predictions[mask] == 1)
            positive_rates.append(rate)
        
        return max(positive_rates) - min(positive_rates)
    
    @staticmethod
    def disparate_impact_ratio(
        predictions: np.ndarray,
        sensitive_attr: np.ndarray,
    ) -> float:
        """Calculate disparate impact ratio."""
        groups = np.unique(sensitive_attr)
        positive_rates = []
        
        for group in groups:
            mask = sensitive_attr == group
            rate = np.mean(predictions[mask] == 1)
            positive_rates.append(rate)
        
        if max(positive_rates) == 0:
            return 1.0
        
        return min(positive_rates) / max(positive_rates)
    
    @staticmethod
    def equalized_odds_difference(
        predictions: np.ndarray,
        y_true: np.ndarray,
        sensitive_attr: np.ndarray,
    ) -> dict[str, float]:
        """Calculate equalized odds differences."""
        groups = np.unique(sensitive_attr)
        tprs = []
        fprs = []
        
        for group in groups:
            mask = sensitive_attr == group
            group_preds = predictions[mask]
            group_true = y_true[mask]
            
            # TPR
            pos_mask = group_true == 1
            if pos_mask.any():
                tpr = np.mean(group_preds[pos_mask] == 1)
                tprs.append(tpr)
            
            # FPR
            neg_mask = group_true == 0
            if neg_mask.any():
                fpr = np.mean(group_preds[neg_mask] == 1)
                fprs.append(fpr)
        
        return {
            "tpr_difference": max(tprs) - min(tprs) if tprs else 0,
            "fpr_difference": max(fprs) - min(fprs) if fprs else 0,
        }
