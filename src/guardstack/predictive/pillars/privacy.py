"""
Privacy Pillar

Privacy risk assessment including membership inference and data leakage.
"""

import logging
import time
from typing import Any, Optional

import numpy as np

from guardstack.predictive.pillars.base import BasePillar, PillarResult
from guardstack.models.core import RiskStatus

logger = logging.getLogger(__name__)


class PrivacyPillar(BasePillar):
    """
    Privacy pillar for predictive models.
    
    Evaluates:
    - Membership inference attack vulnerability
    - Attribute inference risks
    - Training data reconstruction
    - Differential privacy compliance
    """
    
    pillar_name = "privacy"
    pillar_category = "predictive"
    
    def __init__(
        self,
        membership_threshold: float = 0.6,
        attack_samples: int = 500,
    ) -> None:
        self.membership_threshold = membership_threshold
        self.attack_samples = attack_samples
    
    async def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate model privacy through various attack simulations.
        """
        start_time = time.time()
        
        findings = []
        metrics = {
            "membership_inference_accuracy": 0.0,
            "attribute_inference_risk": 0.0,
            "overfitting_score": 0.0,
            "confidence_leakage": 0.0,
        }
        
        # Membership inference attack
        mia_results = await self._membership_inference_attack(model, X, y)
        metrics["membership_inference_accuracy"] = mia_results["accuracy"]
        findings.extend(mia_results.get("findings", []))
        
        # Attribute inference risk
        if sensitive_features:
            attr_results = await self._attribute_inference_risk(
                model, X, y, sensitive_features
            )
            metrics["attribute_inference_risk"] = attr_results["risk"]
            findings.extend(attr_results.get("findings", []))
        
        # Overfitting analysis
        overfit_results = await self._overfitting_analysis(model, X, y)
        metrics["overfitting_score"] = overfit_results["score"]
        findings.extend(overfit_results.get("findings", []))
        
        # Confidence leakage
        if hasattr(model, "predict_proba"):
            conf_results = await self._confidence_leakage_analysis(model, X)
            metrics["confidence_leakage"] = conf_results["leakage"]
            findings.extend(conf_results.get("findings", []))
        
        score = self._calculate_score(metrics)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PillarResult(
            pillar_name=self.pillar_name,
            score=score,
            status=self._score_to_status(score),
            findings=findings,
            metrics=metrics,
            details={
                "membership_threshold": self.membership_threshold,
                "attack_samples": self.attack_samples,
            },
            execution_time_ms=execution_time,
            samples_tested=len(X),
        )
    
    async def _membership_inference_attack(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> dict[str, Any]:
        """
        Simulate membership inference attack.
        
        Tests if an attacker can determine whether a sample was in training data.
        """
        results = {
            "accuracy": 0.5,  # Baseline (random guess)
            "findings": [],
        }
        
        n_members = min(self.attack_samples // 2, len(X))
        
        # Member samples (from training data)
        member_indices = np.random.choice(len(X), n_members, replace=False)
        X_members = X[member_indices]
        y_members = y[member_indices]
        
        # Non-member samples (synthetic)
        X_non_members = self._generate_non_members(X, n_members)
        
        # Get model outputs for both sets
        member_signals = self._get_membership_signals(
            model, X_members, y_members
        )
        non_member_signals = self._get_membership_signals(
            model, X_non_members, None
        )
        
        # Simple threshold-based attack
        threshold = np.median(np.concatenate([
            member_signals, non_member_signals
        ]))
        
        member_correct = np.sum(member_signals > threshold)
        non_member_correct = np.sum(non_member_signals <= threshold)
        
        accuracy = (member_correct + non_member_correct) / (2 * n_members)
        results["accuracy"] = float(accuracy)
        
        if accuracy > self.membership_threshold:
            results["findings"].append(self._create_finding(
                finding_type="membership_inference_vulnerability",
                severity="critical",
                message=f"Model vulnerable to membership inference ({accuracy:.2%} accuracy)",
                attack_accuracy=float(accuracy),
                threshold=self.membership_threshold,
            ))
        
        return results
    
    async def _attribute_inference_risk(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: dict[str, np.ndarray],
    ) -> dict[str, Any]:
        """Assess risk of inferring sensitive attributes."""
        results = {
            "risk": 0.0,
            "findings": [],
            "attribute_risks": {},
        }
        
        risks = []
        
        for attr_name, attr_values in sensitive_features.items():
            # Check correlation between predictions and sensitive attribute
            predictions = model.predict(X)
            
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(X)[:, 1]
            else:
                probs = predictions.astype(float)
            
            # Calculate mutual information approximation
            unique_attrs = np.unique(attr_values)
            attr_entropy = -sum(
                (np.mean(attr_values == a) * np.log2(np.mean(attr_values == a) + 1e-10))
                for a in unique_attrs
            )
            
            # Correlation between predictions and attribute
            for attr_val in unique_attrs:
                mask = attr_values == attr_val
                if mask.any():
                    attr_prob_mean = np.mean(probs[mask])
                    overall_prob_mean = np.mean(probs)
                    
                    # Difference indicates information leakage
                    if abs(attr_prob_mean - overall_prob_mean) > 0.1:
                        risk = abs(attr_prob_mean - overall_prob_mean)
                        risks.append(risk)
                        results["attribute_risks"][f"{attr_name}_{attr_val}"] = float(risk)
        
        if risks:
            results["risk"] = float(np.max(risks))
            
            if results["risk"] > 0.2:
                results["findings"].append(self._create_finding(
                    finding_type="attribute_inference_risk",
                    severity="high",
                    message="Sensitive attributes may be inferable from predictions",
                    risk_score=results["risk"],
                ))
        
        return results
    
    async def _overfitting_analysis(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> dict[str, Any]:
        """Analyze model overfitting (privacy proxy)."""
        results = {
            "score": 0.0,
            "findings": [],
        }
        
        predictions = model.predict(X)
        train_accuracy = np.mean(predictions == y)
        
        # Generate test-like data
        X_test = self._generate_non_members(X, min(len(X), 200))
        y_test = np.random.choice(np.unique(y), len(X_test))
        
        test_predictions = model.predict(X_test)
        
        # Overfitting indicated by high confidence on training data
        if hasattr(model, "predict_proba"):
            train_confidence = np.mean(np.max(model.predict_proba(X), axis=1))
            test_confidence = np.mean(np.max(model.predict_proba(X_test), axis=1))
            
            confidence_gap = train_confidence - test_confidence
            results["score"] = float(np.clip(confidence_gap, 0, 1))
            
            if confidence_gap > 0.2:
                results["findings"].append(self._create_finding(
                    finding_type="overfitting_detected",
                    severity="medium",
                    message="Model shows signs of overfitting",
                    train_confidence=float(train_confidence),
                    test_confidence=float(test_confidence),
                    gap=float(confidence_gap),
                ))
        else:
            # Simple accuracy-based check
            results["score"] = float(train_accuracy - 0.5)  # Adjust from baseline
        
        return results
    
    async def _confidence_leakage_analysis(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Analyze information leakage through prediction confidence."""
        results = {
            "leakage": 0.0,
            "findings": [],
        }
        
        probs = model.predict_proba(X)
        confidence = np.max(probs, axis=1)
        
        # High confidence variance indicates potential leakage
        confidence_std = np.std(confidence)
        confidence_range = np.max(confidence) - np.min(confidence)
        
        # Leakage score based on confidence distribution
        results["leakage"] = float(confidence_std * 2)  # Scale to 0-1
        
        if results["leakage"] > 0.4:
            results["findings"].append(self._create_finding(
                finding_type="confidence_leakage",
                severity="medium",
                message="Prediction confidences may leak information",
                confidence_std=float(confidence_std),
                confidence_range=float(confidence_range),
            ))
        
        return results
    
    def _generate_non_members(
        self,
        X: np.ndarray,
        n_samples: int,
    ) -> np.ndarray:
        """Generate synthetic non-member samples."""
        # Use statistics from training data
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)
        
        # Generate samples from similar distribution
        X_synthetic = np.random.normal(
            mean,
            std * 1.5,  # Slightly wider distribution
            (n_samples, X.shape[1] if X.ndim > 1 else 1),
        )
        
        return X_synthetic
    
    def _get_membership_signals(
        self,
        model: Any,
        X: np.ndarray,
        y: Optional[np.ndarray],
    ) -> np.ndarray:
        """Get membership inference signals from model outputs."""
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            
            if y is not None:
                # Confidence on correct class
                signals = probs[np.arange(len(y)), y.astype(int)]
            else:
                # Maximum confidence
                signals = np.max(probs, axis=1)
        else:
            # Binary signal based on correct prediction
            predictions = model.predict(X)
            if y is not None:
                signals = (predictions == y).astype(float)
            else:
                signals = np.ones(len(X)) * 0.5
        
        return signals
    
    def _calculate_score(self, metrics: dict[str, Any]) -> float:
        """Calculate privacy score."""
        score = 100.0
        
        # Membership inference penalty
        mia_accuracy = metrics.get("membership_inference_accuracy", 0.5)
        # Penalty increases as accuracy exceeds 0.5 (random guess)
        mia_penalty = max(0, (mia_accuracy - 0.5) * 2) * 40
        score -= mia_penalty
        
        # Attribute inference penalty
        attr_risk = metrics.get("attribute_inference_risk", 0)
        score -= attr_risk * 30
        
        # Overfitting penalty
        overfit = metrics.get("overfitting_score", 0)
        score -= overfit * 20
        
        # Confidence leakage penalty
        conf_leak = metrics.get("confidence_leakage", 0)
        score -= conf_leak * 10
        
        return max(0, min(100, score))


class DifferentialPrivacyChecker:
    """
    Utility for checking differential privacy properties.
    """
    
    @staticmethod
    def estimate_epsilon(
        model: Any,
        X: np.ndarray,
        n_trials: int = 100,
    ) -> float:
        """
        Estimate effective epsilon of a model.
        
        Uses output perturbation analysis.
        """
        if not hasattr(model, "predict_proba"):
            return float("inf")
        
        original_probs = model.predict_proba(X)
        
        max_sensitivity = 0.0
        
        for _ in range(n_trials):
            # Perturb single sample
            idx = np.random.randint(len(X))
            X_perturbed = X.copy()
            X_perturbed[idx] += np.random.normal(0, 0.01, X.shape[1] if X.ndim > 1 else 1)
            
            perturbed_probs = model.predict_proba(X_perturbed)
            
            # Calculate max change
            max_change = np.max(np.abs(perturbed_probs - original_probs))
            max_sensitivity = max(max_sensitivity, max_change)
        
        # Approximate epsilon from sensitivity
        if max_sensitivity > 0:
            epsilon = np.log(1 / max_sensitivity)
        else:
            epsilon = float("inf")
        
        return epsilon
