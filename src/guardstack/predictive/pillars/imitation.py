"""
Imitation Pillar

Model extraction protection and intellectual property security.
"""

import logging
import time
from typing import Any, Optional

import numpy as np

from guardstack.predictive.pillars.base import BasePillar, PillarResult
from guardstack.models.core import RiskStatus

logger = logging.getLogger(__name__)


class ImitationPillar(BasePillar):
    """
    Imitation pillar for predictive models.
    
    Evaluates vulnerability to:
    - Model extraction attacks
    - Model stealing
    - Decision boundary reconstruction
    """
    
    pillar_name = "imitation"
    pillar_category = "predictive"
    
    def __init__(
        self,
        query_budget: int = 1000,
        extraction_threshold: float = 0.85,
    ) -> None:
        self.query_budget = query_budget
        self.extraction_threshold = extraction_threshold
    
    async def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate model's resistance to extraction attacks.
        
        Metrics:
        - Query complexity required for extraction
        - Fidelity of extracted model
        - Boundary reconstruction accuracy
        """
        start_time = time.time()
        
        findings = []
        metrics = {
            "extraction_fidelity": 0.0,
            "query_complexity": 0,
            "boundary_leakage": 0.0,
            "watermark_detected": False,
        }
        
        # Simulate model extraction attack
        extraction_results = await self._simulate_extraction(model, X, y)
        metrics.update(extraction_results["metrics"])
        findings.extend(extraction_results.get("findings", []))
        
        # Test decision boundary leakage
        boundary_results = await self._test_boundary_leakage(model, X)
        metrics["boundary_leakage"] = boundary_results["leakage"]
        findings.extend(boundary_results.get("findings", []))
        
        # Check for watermarking
        watermark_results = await self._check_watermark(model, X)
        metrics["watermark_detected"] = watermark_results["detected"]
        
        # Calculate score (higher = more resistant to extraction)
        score = self._calculate_score(metrics)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PillarResult(
            pillar_name=self.pillar_name,
            score=score,
            status=self._score_to_status(score),
            findings=findings,
            metrics=metrics,
            details={
                "query_budget": self.query_budget,
                "extraction_threshold": self.extraction_threshold,
            },
            execution_time_ms=execution_time,
            samples_tested=len(X),
        )
    
    async def _simulate_extraction(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> dict[str, Any]:
        """Simulate a model extraction attack."""
        results = {
            "metrics": {
                "extraction_fidelity": 0.0,
                "query_complexity": 0,
            },
            "findings": [],
        }
        
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.tree import DecisionTreeClassifier
        except ImportError:
            results["findings"].append(self._create_finding(
                finding_type="dependency_missing",
                severity="low",
                message="sklearn not available for extraction simulation",
            ))
            return results
        
        # Sample queries within budget
        n_queries = min(self.query_budget, len(X))
        query_indices = np.random.choice(len(X), n_queries, replace=False)
        X_query = X[query_indices]
        
        # Get labels from target model
        y_stolen = model.predict(X_query)
        
        results["metrics"]["query_complexity"] = n_queries
        
        # Train surrogate models
        surrogates = [
            ("logistic", LogisticRegression(max_iter=1000)),
            ("decision_tree", DecisionTreeClassifier(max_depth=10)),
        ]
        
        best_fidelity = 0.0
        
        for name, surrogate in surrogates:
            try:
                surrogate.fit(X_query, y_stolen)
                
                # Test fidelity on held-out data
                test_mask = ~np.isin(np.arange(len(X)), query_indices)
                if test_mask.any():
                    X_test = X[test_mask]
                    y_target = model.predict(X_test)
                    y_surrogate = surrogate.predict(X_test)
                    
                    fidelity = np.mean(y_target == y_surrogate)
                    best_fidelity = max(best_fidelity, fidelity)
                    
            except Exception as e:
                logger.warning(f"Surrogate {name} training failed: {e}")
        
        results["metrics"]["extraction_fidelity"] = float(best_fidelity)
        
        # Check if extraction was successful
        if best_fidelity >= self.extraction_threshold:
            results["findings"].append(self._create_finding(
                finding_type="extraction_vulnerability",
                severity="critical",
                message=f"Model can be extracted with {best_fidelity:.2%} fidelity",
                fidelity=float(best_fidelity),
                queries_used=n_queries,
            ))
        
        return results
    
    async def _test_boundary_leakage(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Test decision boundary information leakage."""
        results = {
            "leakage": 0.0,
            "findings": [],
        }
        
        if not hasattr(model, "predict_proba"):
            results["leakage"] = 0.5  # Assume moderate leakage without probabilities
            return results
        
        # Get probability outputs
        probs = model.predict_proba(X)[:, 1]
        
        # Measure boundary leakage through probability distribution
        # High entropy near 0.5 indicates clear decision boundary
        boundary_mask = (probs > 0.4) & (probs < 0.6)
        boundary_ratio = np.mean(boundary_mask)
        
        # Calculate confidence distribution
        confidence = np.abs(probs - 0.5) * 2  # 0 at boundary, 1 at extremes
        avg_confidence = np.mean(confidence)
        
        # Leakage is higher when boundary is clearly defined
        results["leakage"] = float(1 - avg_confidence)
        
        if results["leakage"] > 0.6:
            results["findings"].append(self._create_finding(
                finding_type="boundary_leakage",
                severity="medium",
                message="Decision boundary information may be leaked through probabilities",
                leakage_score=results["leakage"],
                boundary_samples_ratio=float(boundary_ratio),
            ))
        
        return results
    
    async def _check_watermark(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Check if model has watermarking protection."""
        results = {
            "detected": False,
        }
        
        # Check for watermark metadata
        if hasattr(model.model, "watermark"):
            results["detected"] = True
            results["watermark_type"] = "metadata"
        
        # Check for watermark verification method
        if hasattr(model.model, "verify_watermark"):
            results["detected"] = True
            results["watermark_type"] = "verifiable"
        
        # Simple detection: check for unusual behavior on specific inputs
        # (Real watermarks would use cryptographic verification)
        
        return results
    
    def _calculate_score(self, metrics: dict[str, Any]) -> float:
        """Calculate imitation protection score."""
        score = 100.0
        
        # Penalize high extraction fidelity
        fidelity = metrics.get("extraction_fidelity", 0)
        score -= fidelity * 50  # Up to 50 point penalty
        
        # Penalize boundary leakage
        leakage = metrics.get("boundary_leakage", 0)
        score -= leakage * 30  # Up to 30 point penalty
        
        # Bonus for watermarking
        if metrics.get("watermark_detected"):
            score += 10
        
        # Bonus for high query complexity
        query_complexity = metrics.get("query_complexity", 0)
        if query_complexity > 500:
            score += 10  # Model requires many queries
        
        return max(0, min(100, score))


class ModelWatermark:
    """
    Utility for adding watermarks to models.
    
    Supports:
    - Trigger-based watermarks
    - Fingerprinting
    """
    
    @staticmethod
    def add_trigger_watermark(
        model: Any,
        trigger_pattern: np.ndarray,
        trigger_label: int,
    ) -> Any:
        """
        Add a trigger-based watermark to model.
        
        The model will predict trigger_label for inputs matching trigger_pattern.
        """
        # This would modify the model to recognize specific trigger inputs
        # Implementation depends on model type
        pass
    
    @staticmethod
    def verify_watermark(
        model: Any,
        trigger_pattern: np.ndarray,
        expected_label: int,
    ) -> bool:
        """Verify if model contains the watermark."""
        try:
            pred = model.predict(trigger_pattern.reshape(1, -1))[0]
            return pred == expected_label
        except Exception:
            return False
    
    @staticmethod
    def generate_fingerprint(model: Any, seed: int = 42) -> dict[str, Any]:
        """Generate a cryptographic fingerprint for the model."""
        import hashlib
        
        np.random.seed(seed)
        
        fingerprint_data = {
            "model_type": type(model).__name__,
        }
        
        # Generate random test inputs
        test_inputs = np.random.randn(10, 10)
        
        if hasattr(model, "predict"):
            predictions = model.predict(test_inputs)
            pred_hash = hashlib.sha256(predictions.tobytes()).hexdigest()
            fingerprint_data["prediction_hash"] = pred_hash
        
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(test_inputs)
            prob_hash = hashlib.sha256(probs.tobytes()).hexdigest()
            fingerprint_data["probability_hash"] = prob_hash
        
        return fingerprint_data
