"""
Robustness Pillar

Adversarial attack testing and perturbation analysis.
"""

import logging
import time
from typing import Any, Optional

import numpy as np

from guardstack.predictive.pillars.base import BasePillar, PillarResult
from guardstack.models.core import RiskStatus

logger = logging.getLogger(__name__)


class RobustnessPillar(BasePillar):
    """
    Robustness pillar for predictive models.
    
    Tests model resilience against:
    - Adversarial examples (FGSM, PGD)
    - Feature perturbations
    - Distribution shift
    - Noise injection
    """
    
    pillar_name = "robustness"
    pillar_category = "predictive"
    
    def __init__(
        self,
        perturbation_budget: float = 0.1,
        noise_levels: Optional[list[float]] = None,
        max_samples: int = 100,
    ) -> None:
        self.perturbation_budget = perturbation_budget
        self.noise_levels = noise_levels or [0.01, 0.05, 0.1, 0.2]
        self.max_samples = max_samples
    
    async def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate model robustness through adversarial testing.
        
        Metrics:
        - Adversarial accuracy
        - Perturbation sensitivity
        - Noise tolerance
        """
        start_time = time.time()
        
        findings = []
        metrics = {
            "clean_accuracy": 0.0,
            "adversarial_accuracy": {},
            "noise_tolerance": {},
            "perturbation_sensitivity": 0.0,
            "robustness_score": 0.0,
        }
        
        # Sample data if too large
        if len(X) > self.max_samples:
            indices = np.random.choice(len(X), self.max_samples, replace=False)
            X = X[indices]
            y = y[indices]
        
        # Calculate clean accuracy
        predictions = model.predict(X)
        clean_accuracy = np.mean(predictions == y)
        metrics["clean_accuracy"] = float(clean_accuracy)
        
        # Test adversarial robustness
        adv_results = await self._test_adversarial(model, X, y)
        metrics["adversarial_accuracy"] = adv_results["accuracy"]
        findings.extend(adv_results.get("findings", []))
        
        # Test noise tolerance
        noise_results = await self._test_noise_tolerance(model, X, y)
        metrics["noise_tolerance"] = noise_results["tolerance"]
        findings.extend(noise_results.get("findings", []))
        
        # Test perturbation sensitivity
        sensitivity = await self._test_perturbation_sensitivity(model, X)
        metrics["perturbation_sensitivity"] = sensitivity
        
        if sensitivity > 0.5:
            findings.append(self._create_finding(
                finding_type="high_sensitivity",
                severity="high",
                message=f"Model is highly sensitive to perturbations ({sensitivity:.2f})",
                sensitivity=sensitivity,
            ))
        
        # Calculate overall score
        score = self._calculate_score(metrics)
        metrics["robustness_score"] = score
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PillarResult(
            pillar_name=self.pillar_name,
            score=score,
            status=self._score_to_status(score),
            findings=findings,
            metrics=metrics,
            details={
                "perturbation_budget": self.perturbation_budget,
                "noise_levels_tested": self.noise_levels,
            },
            execution_time_ms=execution_time,
            samples_tested=len(X),
        )
    
    async def _test_adversarial(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> dict[str, Any]:
        """Test adversarial robustness."""
        results = {
            "accuracy": {},
            "findings": [],
        }
        
        # Test different attack types
        attack_types = ["fgsm", "random", "boundary"]
        
        for attack in attack_types:
            if attack == "fgsm":
                X_adv = self._fgsm_attack(model, X, y)
            elif attack == "random":
                X_adv = self._random_perturbation(X)
            else:
                X_adv = self._boundary_attack(model, X)
            
            adv_predictions = model.predict(X_adv)
            adv_accuracy = float(np.mean(adv_predictions == y))
            results["accuracy"][attack] = adv_accuracy
            
            # Check for significant accuracy drop
            clean_predictions = model.predict(X)
            clean_accuracy = np.mean(clean_predictions == y)
            
            accuracy_drop = clean_accuracy - adv_accuracy
            if accuracy_drop > 0.2:
                results["findings"].append(self._create_finding(
                    finding_type="adversarial_vulnerability",
                    severity="critical",
                    message=f"Significant accuracy drop under {attack} attack",
                    attack_type=attack,
                    accuracy_drop=float(accuracy_drop),
                    adversarial_accuracy=adv_accuracy,
                ))
        
        return results
    
    async def _test_noise_tolerance(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> dict[str, Any]:
        """Test tolerance to noise injection."""
        results = {
            "tolerance": {},
            "findings": [],
        }
        
        clean_predictions = model.predict(X)
        clean_accuracy = np.mean(clean_predictions == y)
        
        for noise_level in self.noise_levels:
            # Add Gaussian noise
            noise = np.random.normal(0, noise_level, X.shape)
            X_noisy = X + noise
            
            noisy_predictions = model.predict(X_noisy)
            noisy_accuracy = float(np.mean(noisy_predictions == y))
            
            results["tolerance"][f"noise_{noise_level}"] = noisy_accuracy
            
            # Check for significant degradation
            if clean_accuracy - noisy_accuracy > 0.1:
                results["findings"].append(self._create_finding(
                    finding_type="noise_sensitivity",
                    severity="medium",
                    message=f"Model sensitive to noise level {noise_level}",
                    noise_level=noise_level,
                    accuracy_with_noise=noisy_accuracy,
                    accuracy_drop=float(clean_accuracy - noisy_accuracy),
                ))
        
        return results
    
    async def _test_perturbation_sensitivity(
        self,
        model: Any,
        X: np.ndarray,
    ) -> float:
        """Calculate perturbation sensitivity score."""
        original_preds = model.predict(X)
        
        if hasattr(model, "predict_proba"):
            original_probs = model.predict_proba(X)[:, 1]
        else:
            original_probs = original_preds.astype(float)
        
        # Small perturbations
        perturbation = np.random.uniform(
            -self.perturbation_budget,
            self.perturbation_budget,
            X.shape,
        )
        X_perturbed = X + perturbation
        
        if hasattr(model, "predict_proba"):
            perturbed_probs = model.predict_proba(X_perturbed)[:, 1]
        else:
            perturbed_probs = model.predict(X_perturbed).astype(float)
        
        # Calculate sensitivity as average change in prediction
        sensitivity = np.mean(np.abs(perturbed_probs - original_probs))
        
        return float(sensitivity)
    
    def _fgsm_attack(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> np.ndarray:
        """
        Fast Gradient Sign Method attack.
        
        For models without gradients, approximate with finite differences.
        """
        epsilon = self.perturbation_budget
        
        # Check if model has gradient support
        if hasattr(model, "model") and hasattr(model.model, "get_gradient"):
            # Use actual gradients
            gradient = model.model.get_gradient(X, y)
            perturbation = epsilon * np.sign(gradient)
        else:
            # Approximate with finite differences
            perturbation = np.zeros_like(X)
            delta = 0.01
            
            for i in range(X.shape[1] if X.ndim > 1 else 1):
                X_plus = X.copy()
                X_minus = X.copy()
                
                if X.ndim > 1:
                    X_plus[:, i] += delta
                    X_minus[:, i] -= delta
                else:
                    X_plus += delta
                    X_minus -= delta
                
                if hasattr(model, "predict_proba"):
                    grad = (
                        model.predict_proba(X_plus)[:, 1] -
                        model.predict_proba(X_minus)[:, 1]
                    ) / (2 * delta)
                else:
                    grad = (model.predict(X_plus) - model.predict(X_minus)) / (2 * delta)
                
                if X.ndim > 1:
                    perturbation[:, i] = epsilon * np.sign(grad)
                else:
                    perturbation = epsilon * np.sign(grad)
        
        return X + perturbation
    
    def _random_perturbation(self, X: np.ndarray) -> np.ndarray:
        """Apply random perturbation within budget."""
        perturbation = np.random.uniform(
            -self.perturbation_budget,
            self.perturbation_budget,
            X.shape,
        )
        return X + perturbation
    
    def _boundary_attack(
        self,
        model: Any,
        X: np.ndarray,
    ) -> np.ndarray:
        """Simplified boundary attack."""
        X_adv = X.copy()
        
        original_preds = model.predict(X)
        
        for i in range(len(X)):
            # Start with random perturbation
            direction = np.random.randn(*X[i].shape)
            direction = direction / np.linalg.norm(direction)
            
            for step in [0.5, 0.3, 0.1, 0.05]:
                X_candidate = X[i] + step * direction
                pred = model.predict(X_candidate.reshape(1, -1))[0]
                
                if pred != original_preds[i]:
                    X_adv[i] = X_candidate
                    break
        
        return X_adv
    
    def _calculate_score(self, metrics: dict[str, Any]) -> float:
        """Calculate overall robustness score."""
        score = 0.0
        
        # Adversarial accuracy score (50%)
        adv_accuracies = list(metrics.get("adversarial_accuracy", {}).values())
        if adv_accuracies:
            avg_adv_acc = np.mean(adv_accuracies)
            score += avg_adv_acc * 50
        else:
            score += 25  # Default if no adversarial tests
        
        # Noise tolerance score (30%)
        noise_tolerances = list(metrics.get("noise_tolerance", {}).values())
        if noise_tolerances:
            avg_noise_tol = np.mean(noise_tolerances)
            score += avg_noise_tol * 30
        else:
            score += 15
        
        # Perturbation sensitivity score (20%)
        sensitivity = metrics.get("perturbation_sensitivity", 0.5)
        score += (1 - sensitivity) * 20
        
        return min(100, score)
