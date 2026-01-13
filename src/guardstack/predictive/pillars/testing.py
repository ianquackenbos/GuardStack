"""
Testing Pillar

Behavioral testing and metamorphic testing for ML models.
"""

import logging
import time
from typing import Any, Callable, Optional

import numpy as np

from guardstack.predictive.pillars.base import BasePillar, PillarResult
from guardstack.models.core import RiskStatus

logger = logging.getLogger(__name__)


class TestingPillar(BasePillar):
    """
    Testing pillar for predictive models.
    
    Implements:
    - Behavioral testing (CheckList-style)
    - Metamorphic testing
    - Invariance testing
    - Directional expectation tests
    """
    
    pillar_name = "testing"
    pillar_category = "predictive"
    
    def __init__(
        self,
        metamorphic_relations: Optional[list[dict[str, Any]]] = None,
        invariance_transforms: Optional[list[Callable]] = None,
    ) -> None:
        self.metamorphic_relations = metamorphic_relations or self._default_relations()
        self.invariance_transforms = invariance_transforms or []
    
    async def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate model through behavioral and metamorphic testing.
        """
        start_time = time.time()
        
        findings = []
        metrics = {
            "metamorphic_tests": 0,
            "metamorphic_failures": 0,
            "invariance_tests": 0,
            "invariance_violations": 0,
            "directional_tests": 0,
            "directional_failures": 0,
            "test_coverage": 0.0,
        }
        
        # Run metamorphic tests
        meta_results = await self._run_metamorphic_tests(model, X, y)
        metrics["metamorphic_tests"] = meta_results["total"]
        metrics["metamorphic_failures"] = meta_results["failures"]
        findings.extend(meta_results.get("findings", []))
        
        # Run invariance tests
        inv_results = await self._run_invariance_tests(model, X)
        metrics["invariance_tests"] = inv_results["total"]
        metrics["invariance_violations"] = inv_results["violations"]
        findings.extend(inv_results.get("findings", []))
        
        # Run directional expectation tests
        dir_results = await self._run_directional_tests(model, X, y)
        metrics["directional_tests"] = dir_results["total"]
        metrics["directional_failures"] = dir_results["failures"]
        findings.extend(dir_results.get("findings", []))
        
        # Calculate test coverage
        total_tests = (
            metrics["metamorphic_tests"] +
            metrics["invariance_tests"] +
            metrics["directional_tests"]
        )
        total_failures = (
            metrics["metamorphic_failures"] +
            metrics["invariance_violations"] +
            metrics["directional_failures"]
        )
        
        if total_tests > 0:
            metrics["test_coverage"] = (total_tests - total_failures) / total_tests
        
        score = self._calculate_score(metrics)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PillarResult(
            pillar_name=self.pillar_name,
            score=score,
            status=self._score_to_status(score),
            findings=findings,
            metrics=metrics,
            details={
                "metamorphic_relations": len(self.metamorphic_relations),
                "invariance_transforms": len(self.invariance_transforms),
            },
            execution_time_ms=execution_time,
            samples_tested=len(X),
        )
    
    async def _run_metamorphic_tests(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> dict[str, Any]:
        """Run metamorphic testing."""
        results = {
            "total": 0,
            "failures": 0,
            "findings": [],
        }
        
        for relation in self.metamorphic_relations:
            try:
                transform = relation["transform"]
                expected_relation = relation["expected"]
                name = relation.get("name", "unnamed")
                
                # Apply transformation
                X_transformed = transform(X)
                
                # Get predictions
                original_preds = model.predict(X)
                transformed_preds = model.predict(X_transformed)
                
                # Check expected relation
                results["total"] += 1
                
                if expected_relation == "equal":
                    violations = np.sum(original_preds != transformed_preds)
                elif expected_relation == "greater":
                    violations = np.sum(transformed_preds <= original_preds)
                elif expected_relation == "less":
                    violations = np.sum(transformed_preds >= original_preds)
                else:
                    violations = 0
                
                if violations > len(X) * 0.1:  # >10% violations
                    results["failures"] += 1
                    results["findings"].append(self._create_finding(
                        finding_type="metamorphic_violation",
                        severity="high",
                        message=f"Metamorphic relation '{name}' violated",
                        relation_name=name,
                        violation_rate=float(violations / len(X)),
                    ))
                    
            except Exception as e:
                logger.warning(f"Metamorphic test failed: {e}")
                results["findings"].append(self._create_finding(
                    finding_type="test_error",
                    severity="low",
                    message=f"Metamorphic test error: {str(e)}",
                ))
        
        return results
    
    async def _run_invariance_tests(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Run invariance testing."""
        results = {
            "total": 0,
            "violations": 0,
            "findings": [],
        }
        
        original_preds = model.predict(X)
        
        # Default invariance transforms if none provided
        transforms = self.invariance_transforms or [
            self._noise_invariance,
            self._scale_invariance,
        ]
        
        for transform in transforms:
            results["total"] += 1
            
            try:
                X_transformed = transform(X)
                transformed_preds = model.predict(X_transformed)
                
                # Check for invariance (predictions should be same)
                violations = np.sum(original_preds != transformed_preds)
                violation_rate = violations / len(X)
                
                if violation_rate > 0.05:  # >5% violations
                    results["violations"] += 1
                    transform_name = getattr(transform, "__name__", "unknown")
                    results["findings"].append(self._create_finding(
                        finding_type="invariance_violation",
                        severity="medium",
                        message=f"Invariance violated for transform '{transform_name}'",
                        transform=transform_name,
                        violation_rate=float(violation_rate),
                    ))
                    
            except Exception as e:
                logger.warning(f"Invariance test failed: {e}")
        
        return results
    
    async def _run_directional_tests(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
    ) -> dict[str, Any]:
        """Run directional expectation tests."""
        results = {
            "total": 0,
            "failures": 0,
            "findings": [],
        }
        
        if not hasattr(model, "predict_proba"):
            return results
        
        original_probs = model.predict_proba(X)[:, 1]
        n_features = X.shape[1] if X.ndim > 1 else 1
        
        for feature_idx in range(min(n_features, 5)):  # Test first 5 features
            results["total"] += 1
            
            # Increase feature value
            X_increased = X.copy()
            if X.ndim > 1:
                X_increased[:, feature_idx] += np.std(X[:, feature_idx])
            else:
                X_increased += np.std(X)
            
            increased_probs = model.predict_proba(X_increased)[:, 1]
            
            # Check for monotonic relationship
            increases = np.sum(increased_probs > original_probs)
            decreases = np.sum(increased_probs < original_probs)
            
            # If no clear direction, might indicate issues
            if min(increases, decreases) > len(X) * 0.3:
                results["failures"] += 1
                results["findings"].append(self._create_finding(
                    finding_type="non_monotonic",
                    severity="low",
                    message=f"Feature {feature_idx} shows non-monotonic behavior",
                    feature_index=feature_idx,
                    increase_rate=float(increases / len(X)),
                    decrease_rate=float(decreases / len(X)),
                ))
        
        return results
    
    def _default_relations(self) -> list[dict[str, Any]]:
        """Return default metamorphic relations."""
        return [
            {
                "name": "permutation_invariance",
                "transform": lambda X: X[np.random.permutation(len(X))],
                "expected": "equal",
            },
            {
                "name": "small_noise",
                "transform": lambda X: X + np.random.normal(0, 0.001, X.shape),
                "expected": "equal",
            },
        ]
    
    def _noise_invariance(self, X: np.ndarray) -> np.ndarray:
        """Apply small noise transformation."""
        return X + np.random.normal(0, 0.001, X.shape)
    
    def _scale_invariance(self, X: np.ndarray) -> np.ndarray:
        """Apply small scale transformation."""
        return X * 1.001
    
    def _calculate_score(self, metrics: dict[str, Any]) -> float:
        """Calculate testing score."""
        total_tests = (
            metrics["metamorphic_tests"] +
            metrics["invariance_tests"] +
            metrics["directional_tests"]
        )
        
        if total_tests == 0:
            return 50.0  # Default score if no tests
        
        total_failures = (
            metrics["metamorphic_failures"] +
            metrics["invariance_violations"] +
            metrics["directional_failures"]
        )
        
        pass_rate = (total_tests - total_failures) / total_tests
        return pass_rate * 100


class BehavioralTestSuite:
    """
    Suite for defining and running behavioral tests.
    
    Inspired by CheckList methodology.
    """
    
    def __init__(self) -> None:
        self.tests: list[dict[str, Any]] = []
    
    def add_minimum_functionality_test(
        self,
        name: str,
        test_data: np.ndarray,
        expected_labels: np.ndarray,
    ) -> None:
        """Add a minimum functionality test."""
        self.tests.append({
            "type": "mft",
            "name": name,
            "data": test_data,
            "expected": expected_labels,
        })
    
    def add_invariance_test(
        self,
        name: str,
        transform: Callable[[np.ndarray], np.ndarray],
    ) -> None:
        """Add an invariance test."""
        self.tests.append({
            "type": "inv",
            "name": name,
            "transform": transform,
        })
    
    def add_directional_test(
        self,
        name: str,
        transform: Callable[[np.ndarray], np.ndarray],
        expected_direction: str,  # "increase" or "decrease"
    ) -> None:
        """Add a directional expectation test."""
        self.tests.append({
            "type": "dir",
            "name": name,
            "transform": transform,
            "expected": expected_direction,
        })
    
    async def run(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Run all tests in the suite."""
        results = {
            "total": len(self.tests),
            "passed": 0,
            "failed": 0,
            "test_results": [],
        }
        
        for test in self.tests:
            test_result = {
                "name": test["name"],
                "type": test["type"],
            }
            
            try:
                if test["type"] == "mft":
                    preds = model.predict(test["data"])
                    accuracy = np.mean(preds == test["expected"])
                    passed = accuracy >= 0.95
                    test_result["accuracy"] = float(accuracy)
                    
                elif test["type"] == "inv":
                    original = model.predict(X)
                    transformed = model.predict(test["transform"](X))
                    match_rate = np.mean(original == transformed)
                    passed = match_rate >= 0.95
                    test_result["match_rate"] = float(match_rate)
                    
                elif test["type"] == "dir":
                    original = model.predict_proba(X)[:, 1]
                    transformed = model.predict_proba(test["transform"](X))[:, 1]
                    
                    if test["expected"] == "increase":
                        rate = np.mean(transformed > original)
                    else:
                        rate = np.mean(transformed < original)
                    passed = rate >= 0.8
                    test_result["direction_rate"] = float(rate)
                else:
                    passed = False
                
                test_result["passed"] = passed
                if passed:
                    results["passed"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                test_result["passed"] = False
                test_result["error"] = str(e)
                results["failed"] += 1
            
            results["test_results"].append(test_result)
        
        return results
