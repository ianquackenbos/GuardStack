"""
Predictive AI Evaluator

Orchestrates 8-pillar evaluation for traditional ML models.
"""

import asyncio
import logging
import time
from typing import Any, Optional

import numpy as np
from pydantic import BaseModel

from guardstack.models.core import RiskStatus
from guardstack.predictive.pillars import (
    BasePillar,
    PillarResult,
    ExplainPillar,
    ActionsPillar,
    FairnessPillar,
    RobustnessPillar,
    TracePillar,
    TestingPillar,
    ImitationPillar,
    PrivacyPillar,
)

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    """Complete evaluation result for a predictive model."""
    
    model_id: str
    overall_score: float
    overall_status: RiskStatus
    pillar_results: dict[str, PillarResult]
    execution_time_ms: int
    timestamp: str
    metadata: dict[str, Any] = {}


class ModelWrapper:
    """
    Wrapper for predictive models to provide unified interface.
    
    Supports sklearn, PyTorch, TensorFlow, and custom models.
    """
    
    def __init__(
        self,
        model: Any,
        model_type: str = "sklearn",
        feature_names: Optional[list[str]] = None,
        class_names: Optional[list[str]] = None,
    ) -> None:
        self.model = model
        self.model_type = model_type
        self.feature_names = feature_names
        self.class_names = class_names
        
        # Detect model type if not provided
        if model_type == "auto":
            self.model_type = self._detect_model_type()
    
    def _detect_model_type(self) -> str:
        """Detect model type from model object."""
        model_class = type(self.model).__name__
        model_module = type(self.model).__module__
        
        if "sklearn" in model_module:
            return "sklearn"
        elif "torch" in model_module:
            return "pytorch"
        elif "tensorflow" in model_module or "keras" in model_module:
            return "tensorflow"
        elif "xgboost" in model_module:
            return "xgboost"
        elif "lightgbm" in model_module:
            return "lightgbm"
        else:
            return "custom"
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Get predictions from model."""
        if self.model_type == "sklearn":
            return self.model.predict(X)
        elif self.model_type == "pytorch":
            import torch
            with torch.no_grad():
                tensor = torch.FloatTensor(X)
                return self.model(tensor).numpy()
        elif self.model_type == "tensorflow":
            return self.model.predict(X)
        else:
            return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get probability predictions from model."""
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        elif self.model_type == "pytorch":
            import torch
            with torch.no_grad():
                tensor = torch.FloatTensor(X)
                output = self.model(tensor)
                return torch.softmax(output, dim=1).numpy()
        elif self.model_type == "tensorflow":
            probs = self.model.predict(X)
            # Ensure probabilities sum to 1
            if probs.ndim == 1:
                return np.column_stack([1 - probs, probs])
            return probs
        else:
            # Fall back to predictions
            preds = self.predict(X)
            return np.column_stack([1 - preds, preds])


class PredictiveEvaluator:
    """
    Main evaluator for predictive AI models.
    
    Orchestrates the 8 evaluation pillars:
    - Explain: SHAP, LIME explanations
    - Actions: Counterfactual analysis, recommended actions
    - Fairness: Demographic parity, equalized odds
    - Robustness: Adversarial attacks, perturbation analysis
    - Trace: Model lineage and versioning
    - Testing: Behavioral testing, metamorphic tests
    - Imitation: Model extraction protection
    - Privacy: Membership inference, data leakage
    """
    
    def __init__(
        self,
        pillars: Optional[list[str]] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> None:
        self.config = config or {}
        
        # Available pillars
        all_pillars = {
            "explain": ExplainPillar,
            "actions": ActionsPillar,
            "fairness": FairnessPillar,
            "robustness": RobustnessPillar,
            "trace": TracePillar,
            "testing": TestingPillar,
            "imitation": ImitationPillar,
            "privacy": PrivacyPillar,
        }
        
        # Initialize requested pillars
        pillar_names = pillars or list(all_pillars.keys())
        self.pillars: dict[str, BasePillar] = {}
        
        for name in pillar_names:
            if name in all_pillars:
                pillar_config = self.config.get(name, {})
                self.pillars[name] = all_pillars[name](**pillar_config)
    
    async def evaluate(
        self,
        model: ModelWrapper,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
        model_id: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Run complete evaluation across all pillars.
        
        Args:
            model: Wrapped model to evaluate
            X: Feature matrix
            y: True labels
            sensitive_features: Dict of sensitive attribute arrays
            model_id: Optional model identifier
        
        Returns:
            Complete evaluation results
        """
        start_time = time.time()
        
        # Run all pillars
        pillar_results = await self._run_pillars(model, X, y, sensitive_features)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(pillar_results)
        overall_status = self._score_to_status(overall_score)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return EvaluationResult(
            model_id=model_id or "unknown",
            overall_score=overall_score,
            overall_status=overall_status,
            pillar_results=pillar_results,
            execution_time_ms=execution_time,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            metadata={
                "pillars_evaluated": list(pillar_results.keys()),
                "samples": len(X),
                "features": X.shape[1] if X.ndim > 1 else 1,
            },
        )
    
    async def _run_pillars(
        self,
        model: ModelWrapper,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]],
    ) -> dict[str, PillarResult]:
        """Run all pillars and collect results."""
        results = {}
        
        # Run pillars that can be parallelized
        independent_pillars = ["explain", "trace", "testing", "imitation"]
        dependent_pillars = ["fairness", "robustness", "actions", "privacy"]
        
        # Run independent pillars in parallel
        tasks = []
        pillar_names = []
        
        for name in independent_pillars:
            if name in self.pillars:
                tasks.append(
                    self.pillars[name].evaluate(model, X, y, sensitive_features)
                )
                pillar_names.append(name)
        
        if tasks:
            pillar_results = await asyncio.gather(*tasks, return_exceptions=True)
            for name, result in zip(pillar_names, pillar_results):
                if isinstance(result, Exception):
                    logger.error(f"Pillar {name} failed: {result}")
                    results[name] = self._create_error_result(name, str(result))
                else:
                    results[name] = result
        
        # Run dependent pillars sequentially
        for name in dependent_pillars:
            if name in self.pillars:
                try:
                    result = await self.pillars[name].evaluate(
                        model, X, y, sensitive_features
                    )
                    results[name] = result
                except Exception as e:
                    logger.error(f"Pillar {name} failed: {e}")
                    results[name] = self._create_error_result(name, str(e))
        
        return results
    
    def _calculate_overall_score(
        self,
        pillar_results: dict[str, PillarResult],
    ) -> float:
        """Calculate weighted overall score."""
        # Pillar weights (can be configured)
        weights = self.config.get("weights", {
            "explain": 1.0,
            "actions": 0.8,
            "fairness": 1.5,
            "robustness": 1.2,
            "trace": 0.5,
            "testing": 1.0,
            "imitation": 0.8,
            "privacy": 1.5,
        })
        
        total_weight = 0
        weighted_sum = 0
        
        for name, result in pillar_results.items():
            weight = weights.get(name, 1.0)
            weighted_sum += result.score * weight
            total_weight += weight
        
        if total_weight > 0:
            return weighted_sum / total_weight
        return 0.0
    
    def _score_to_status(self, score: float) -> RiskStatus:
        """Convert score to risk status."""
        thresholds = self.config.get("thresholds", {
            "pass": 80,
            "warn": 60,
        })
        
        if score >= thresholds["pass"]:
            return RiskStatus.PASS
        elif score >= thresholds["warn"]:
            return RiskStatus.WARN
        else:
            return RiskStatus.FAIL
    
    def _create_error_result(
        self,
        pillar_name: str,
        error_message: str,
    ) -> PillarResult:
        """Create error result for failed pillar."""
        return PillarResult(
            pillar_name=pillar_name,
            score=0.0,
            status=RiskStatus.FAIL,
            findings=[{
                "finding_type": "evaluation_error",
                "severity": "critical",
                "message": f"Pillar evaluation failed: {error_message}",
            }],
            metrics={},
            details={"error": error_message},
            execution_time_ms=0,
            samples_tested=0,
        )


async def evaluate_model(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: Optional[list[str]] = None,
    sensitive_features: Optional[dict[str, np.ndarray]] = None,
    pillars: Optional[list[str]] = None,
) -> EvaluationResult:
    """
    Convenience function to evaluate a model.
    
    Args:
        model: Model to evaluate (sklearn, pytorch, tensorflow)
        X: Feature matrix
        y: True labels
        feature_names: Optional feature names
        sensitive_features: Dict of sensitive attribute arrays
        pillars: List of pillars to run (default: all)
    
    Returns:
        Complete evaluation results
    """
    wrapper = ModelWrapper(model, model_type="auto", feature_names=feature_names)
    evaluator = PredictiveEvaluator(pillars=pillars)
    return await evaluator.evaluate(wrapper, X, y, sensitive_features)
