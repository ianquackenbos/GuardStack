"""
Explain Pillar

Model explainability using SHAP and LIME.
"""

import logging
import time
from typing import Any, Optional

import numpy as np

from guardstack.predictive.pillars.base import BasePillar, PillarResult
from guardstack.models.core import RiskStatus

logger = logging.getLogger(__name__)


class ExplainPillar(BasePillar):
    """
    Explainability pillar for predictive models.
    
    Generates explanations using:
    - SHAP (SHapley Additive exPlanations)
    - LIME (Local Interpretable Model-agnostic Explanations)
    - Feature importance analysis
    """
    
    pillar_name = "explain"
    pillar_category = "predictive"
    
    def __init__(
        self,
        method: str = "shap",
        max_samples: int = 100,
        background_samples: int = 50,
    ) -> None:
        self.method = method
        self.max_samples = max_samples
        self.background_samples = background_samples
    
    async def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate model explainability.
        
        Metrics:
        - Feature importance consistency
        - Explanation stability
        - Coverage (% of predictions explainable)
        """
        start_time = time.time()
        
        findings = []
        metrics = {
            "method": self.method,
            "samples_explained": 0,
            "feature_importance": {},
            "stability_score": 0.0,
            "coverage": 0.0,
        }
        
        # Sample data if too large
        if len(X) > self.max_samples:
            indices = np.random.choice(len(X), self.max_samples, replace=False)
            X_sample = X[indices]
        else:
            X_sample = X
        
        try:
            if self.method == "shap":
                explanation_result = await self._run_shap(model, X_sample)
            elif self.method == "lime":
                explanation_result = await self._run_lime(model, X_sample)
            else:
                explanation_result = await self._run_basic(model, X_sample)
            
            metrics.update(explanation_result["metrics"])
            findings.extend(explanation_result.get("findings", []))
            
        except Exception as e:
            logger.error(f"Explainability analysis failed: {e}")
            findings.append(self._create_finding(
                finding_type="explanation_error",
                severity="high",
                message=f"Failed to generate explanations: {str(e)}",
            ))
        
        # Calculate score based on metrics
        score = self._calculate_score(metrics)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PillarResult(
            pillar_name=self.pillar_name,
            score=score,
            status=self._score_to_status(score),
            findings=findings,
            metrics=metrics,
            details={
                "method": self.method,
                "sample_size": len(X_sample),
            },
            execution_time_ms=execution_time,
            samples_tested=len(X_sample),
        )
    
    async def _run_shap(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Run SHAP analysis."""
        try:
            import shap
        except ImportError:
            return {
                "metrics": {"shap_available": False},
                "findings": [self._create_finding(
                    finding_type="dependency_missing",
                    severity="medium",
                    message="SHAP library not installed",
                )],
            }
        
        results = {
            "metrics": {
                "shap_available": True,
                "samples_explained": len(X),
            },
            "findings": [],
        }
        
        try:
            # Create explainer
            if hasattr(model, "predict_proba"):
                explainer = shap.KernelExplainer(
                    model.predict_proba,
                    X[:self.background_samples],
                )
            else:
                explainer = shap.KernelExplainer(
                    model.predict,
                    X[:self.background_samples],
                )
            
            # Calculate SHAP values
            shap_values = explainer.shap_values(X[:self.max_samples])
            
            # Handle multi-class case
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            
            # Calculate feature importance
            feature_importance = np.abs(shap_values).mean(axis=0)
            
            # Normalize importance
            total_importance = feature_importance.sum()
            if total_importance > 0:
                feature_importance = feature_importance / total_importance
            
            # Store as dict with feature indices
            importance_dict = {
                f"feature_{i}": float(imp) 
                for i, imp in enumerate(feature_importance)
            }
            
            results["metrics"]["feature_importance"] = importance_dict
            results["metrics"]["coverage"] = 1.0
            
            # Calculate stability (consistency across samples)
            stability = self._calculate_stability(shap_values)
            results["metrics"]["stability_score"] = stability
            
            # Add findings for low stability
            if stability < 0.7:
                results["findings"].append(self._create_finding(
                    finding_type="low_stability",
                    severity="medium",
                    message=f"Explanation stability is low ({stability:.2f})",
                    stability_score=stability,
                ))
            
            # Check for dominant features
            max_importance = max(feature_importance)
            if max_importance > 0.5:
                results["findings"].append(self._create_finding(
                    finding_type="dominant_feature",
                    severity="low",
                    message=f"Single feature dominates explanations ({max_importance:.2f})",
                    importance=float(max_importance),
                ))
            
        except Exception as e:
            logger.warning(f"SHAP analysis error: {e}")
            results["metrics"]["shap_error"] = str(e)
            results["findings"].append(self._create_finding(
                finding_type="shap_error",
                severity="medium",
                message=f"SHAP analysis failed: {str(e)}",
            ))
        
        return results
    
    async def _run_lime(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Run LIME analysis."""
        try:
            import lime
            import lime.lime_tabular
        except ImportError:
            return {
                "metrics": {"lime_available": False},
                "findings": [self._create_finding(
                    finding_type="dependency_missing",
                    severity="medium",
                    message="LIME library not installed",
                )],
            }
        
        results = {
            "metrics": {
                "lime_available": True,
                "samples_explained": 0,
            },
            "findings": [],
        }
        
        try:
            # Create LIME explainer
            explainer = lime.lime_tabular.LimeTabularExplainer(
                X,
                mode="classification" if hasattr(model, "predict_proba") else "regression",
                discretize_continuous=True,
            )
            
            # Explain samples
            feature_weights = []
            explained_count = 0
            
            for i in range(min(len(X), self.max_samples)):
                try:
                    if hasattr(model, "predict_proba"):
                        exp = explainer.explain_instance(
                            X[i],
                            model.predict_proba,
                            num_features=X.shape[1] if X.ndim > 1 else 1,
                        )
                    else:
                        exp = explainer.explain_instance(
                            X[i],
                            model.predict,
                            num_features=X.shape[1] if X.ndim > 1 else 1,
                        )
                    
                    # Extract weights
                    weights = dict(exp.as_list())
                    feature_weights.append(weights)
                    explained_count += 1
                    
                except Exception:
                    continue
            
            results["metrics"]["samples_explained"] = explained_count
            results["metrics"]["coverage"] = explained_count / len(X) if len(X) > 0 else 0
            
            # Calculate average feature importance
            if feature_weights:
                all_features = set()
                for weights in feature_weights:
                    all_features.update(weights.keys())
                
                avg_importance = {}
                for feature in all_features:
                    values = [
                        abs(w.get(feature, 0)) for w in feature_weights
                    ]
                    avg_importance[feature] = np.mean(values) if values else 0
                
                results["metrics"]["feature_importance"] = avg_importance
            
        except Exception as e:
            logger.warning(f"LIME analysis error: {e}")
            results["findings"].append(self._create_finding(
                finding_type="lime_error",
                severity="medium",
                message=f"LIME analysis failed: {str(e)}",
            ))
        
        return results
    
    async def _run_basic(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Run basic feature importance analysis."""
        results = {
            "metrics": {
                "method": "basic",
                "samples_explained": len(X),
            },
            "findings": [],
        }
        
        # Check for built-in feature importance
        if hasattr(model.model, "feature_importances_"):
            importance = model.model.feature_importances_
            results["metrics"]["feature_importance"] = {
                f"feature_{i}": float(imp)
                for i, imp in enumerate(importance)
            }
            results["metrics"]["coverage"] = 1.0
            results["metrics"]["stability_score"] = 0.9
        elif hasattr(model.model, "coef_"):
            coef = model.model.coef_
            if coef.ndim > 1:
                coef = coef[0]
            importance = np.abs(coef)
            results["metrics"]["feature_importance"] = {
                f"feature_{i}": float(imp)
                for i, imp in enumerate(importance)
            }
            results["metrics"]["coverage"] = 1.0
            results["metrics"]["stability_score"] = 0.9
        else:
            results["metrics"]["coverage"] = 0.0
            results["metrics"]["stability_score"] = 0.0
            results["findings"].append(self._create_finding(
                finding_type="no_importance",
                severity="medium",
                message="Model does not provide feature importance",
            ))
        
        return results
    
    def _calculate_stability(self, shap_values: np.ndarray) -> float:
        """Calculate explanation stability score."""
        if shap_values.ndim == 1:
            return 1.0
        
        # Calculate coefficient of variation for each feature
        feature_std = np.std(shap_values, axis=0)
        feature_mean = np.abs(np.mean(shap_values, axis=0))
        
        # Avoid division by zero
        mask = feature_mean > 1e-10
        cv = np.zeros_like(feature_std)
        cv[mask] = feature_std[mask] / feature_mean[mask]
        
        # Convert to stability score (1 - normalized CV)
        stability = 1 - np.clip(np.mean(cv), 0, 1)
        return float(stability)
    
    def _calculate_score(self, metrics: dict[str, Any]) -> float:
        """Calculate overall explainability score."""
        score = 0.0
        
        # Coverage score (40%)
        coverage = metrics.get("coverage", 0)
        score += coverage * 40
        
        # Stability score (40%)
        stability = metrics.get("stability_score", 0)
        score += stability * 40
        
        # Feature importance available (20%)
        if metrics.get("feature_importance"):
            score += 20
        
        return min(100, score)
