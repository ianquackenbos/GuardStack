"""
Trace Pillar

Model lineage, versioning, and provenance tracking.
"""

import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Optional

import numpy as np

from guardstack.predictive.pillars.base import BasePillar, PillarResult
from guardstack.models.core import RiskStatus

logger = logging.getLogger(__name__)


class TracePillar(BasePillar):
    """
    Traceability pillar for predictive models.
    
    Tracks:
    - Model lineage and versioning
    - Training data provenance
    - Hyperparameter history
    - Deployment history
    """
    
    pillar_name = "trace"
    pillar_category = "predictive"
    
    def __init__(
        self,
        require_lineage: bool = True,
        require_data_provenance: bool = True,
    ) -> None:
        self.require_lineage = require_lineage
        self.require_data_provenance = require_data_provenance
    
    async def evaluate(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate model traceability.
        
        Checks for lineage information and generates fingerprints.
        """
        start_time = time.time()
        
        findings = []
        metrics = {
            "has_lineage": False,
            "has_data_provenance": False,
            "model_fingerprint": "",
            "data_fingerprint": "",
            "traceability_score": 0.0,
        }
        
        # Generate model fingerprint
        model_fingerprint = self._generate_model_fingerprint(model)
        metrics["model_fingerprint"] = model_fingerprint
        
        # Generate data fingerprint
        data_fingerprint = self._generate_data_fingerprint(X, y)
        metrics["data_fingerprint"] = data_fingerprint
        
        # Check for lineage information
        lineage_result = await self._check_lineage(model)
        metrics["has_lineage"] = lineage_result["has_lineage"]
        metrics["lineage_info"] = lineage_result.get("info", {})
        findings.extend(lineage_result.get("findings", []))
        
        # Check for data provenance
        provenance_result = await self._check_data_provenance(model, X)
        metrics["has_data_provenance"] = provenance_result["has_provenance"]
        metrics["provenance_info"] = provenance_result.get("info", {})
        findings.extend(provenance_result.get("findings", []))
        
        # Generate traceability record
        trace_record = self._generate_trace_record(model, X, y, metrics)
        metrics["trace_record"] = trace_record
        
        # Calculate score
        score = self._calculate_score(metrics)
        metrics["traceability_score"] = score
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return PillarResult(
            pillar_name=self.pillar_name,
            score=score,
            status=self._score_to_status(score),
            findings=findings,
            metrics=metrics,
            details={
                "fingerprints": {
                    "model": model_fingerprint,
                    "data": data_fingerprint,
                },
            },
            execution_time_ms=execution_time,
            samples_tested=len(X),
        )
    
    def _generate_model_fingerprint(self, model: Any) -> str:
        """Generate unique fingerprint for model."""
        fingerprint_data = []
        
        # Model type
        model_type = type(model.model).__name__
        fingerprint_data.append(f"type:{model_type}")
        
        # Model parameters
        if hasattr(model.model, "get_params"):
            params = model.model.get_params()
            param_str = str(sorted(params.items()))
            fingerprint_data.append(f"params:{param_str}")
        
        # Model weights (sample)
        if hasattr(model.model, "coef_"):
            coef_hash = hashlib.md5(
                model.model.coef_.tobytes()
            ).hexdigest()[:8]
            fingerprint_data.append(f"coef:{coef_hash}")
        elif hasattr(model.model, "feature_importances_"):
            imp_hash = hashlib.md5(
                model.model.feature_importances_.tobytes()
            ).hexdigest()[:8]
            fingerprint_data.append(f"imp:{imp_hash}")
        
        # Generate final fingerprint
        combined = "|".join(fingerprint_data)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _generate_data_fingerprint(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> str:
        """Generate fingerprint for training data."""
        # Use statistical properties instead of raw data
        stats = {
            "n_samples": len(X),
            "n_features": X.shape[1] if X.ndim > 1 else 1,
            "X_mean": float(np.mean(X)),
            "X_std": float(np.std(X)),
            "y_mean": float(np.mean(y)),
            "y_unique": len(np.unique(y)),
        }
        
        stats_str = str(sorted(stats.items()))
        return hashlib.sha256(stats_str.encode()).hexdigest()[:16]
    
    async def _check_lineage(self, model: Any) -> dict[str, Any]:
        """Check for model lineage information."""
        result = {
            "has_lineage": False,
            "info": {},
            "findings": [],
        }
        
        # Check for MLflow tracking
        if hasattr(model.model, "mlflow_run_id"):
            result["has_lineage"] = True
            result["info"]["mlflow_run_id"] = model.model.mlflow_run_id
        
        # Check for custom metadata
        if hasattr(model.model, "metadata"):
            result["has_lineage"] = True
            result["info"]["metadata"] = model.model.metadata
        
        # Check for sklearn metadata
        if hasattr(model.model, "_sklearn_version"):
            result["info"]["sklearn_version"] = model.model._sklearn_version
        
        # Check for training history
        if hasattr(model.model, "history"):
            result["has_lineage"] = True
            result["info"]["has_training_history"] = True
        
        if not result["has_lineage"] and self.require_lineage:
            result["findings"].append(self._create_finding(
                finding_type="missing_lineage",
                severity="high",
                message="Model lacks lineage information",
                recommendation="Add MLflow tracking or custom metadata",
            ))
        
        return result
    
    async def _check_data_provenance(
        self,
        model: Any,
        X: np.ndarray,
    ) -> dict[str, Any]:
        """Check for data provenance information."""
        result = {
            "has_provenance": False,
            "info": {},
            "findings": [],
        }
        
        # Check for data source metadata
        if hasattr(model, "training_data_source"):
            result["has_provenance"] = True
            result["info"]["data_source"] = model.training_data_source
        
        # Check for feature names (indicates documented data)
        if model.feature_names:
            result["has_provenance"] = True
            result["info"]["feature_names"] = model.feature_names
        
        # Infer data characteristics
        result["info"]["data_shape"] = X.shape
        result["info"]["data_dtype"] = str(X.dtype)
        
        if not result["has_provenance"] and self.require_data_provenance:
            result["findings"].append(self._create_finding(
                finding_type="missing_provenance",
                severity="medium",
                message="Training data lacks provenance information",
                recommendation="Document data sources and transformations",
            ))
        
        return result
    
    def _generate_trace_record(
        self,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate comprehensive trace record."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "model_type": type(model.model).__name__,
            "model_fingerprint": metrics["model_fingerprint"],
            "data_fingerprint": metrics["data_fingerprint"],
            "data_shape": {
                "samples": len(X),
                "features": X.shape[1] if X.ndim > 1 else 1,
            },
            "label_distribution": {
                str(label): int(count)
                for label, count in zip(*np.unique(y, return_counts=True))
            },
            "lineage_available": metrics["has_lineage"],
            "provenance_available": metrics["has_data_provenance"],
        }
    
    def _calculate_score(self, metrics: dict[str, Any]) -> float:
        """Calculate traceability score."""
        score = 0.0
        
        # Model fingerprint (always available)
        score += 30
        
        # Data fingerprint (always available)
        score += 20
        
        # Lineage information (25%)
        if metrics.get("has_lineage"):
            score += 25
        elif not self.require_lineage:
            score += 12.5
        
        # Data provenance (25%)
        if metrics.get("has_data_provenance"):
            score += 25
        elif not self.require_data_provenance:
            score += 12.5
        
        return min(100, score)


class ModelRegistry:
    """
    Registry for tracking model versions and lineage.
    
    Provides:
    - Version tracking
    - Fingerprint comparison
    - Deployment history
    """
    
    def __init__(self) -> None:
        self._models: dict[str, list[dict[str, Any]]] = {}
    
    def register(
        self,
        model_id: str,
        model: Any,
        X: np.ndarray,
        y: np.ndarray,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Register a model version."""
        trace_pillar = TracePillar()
        
        record = {
            "version": len(self._models.get(model_id, [])) + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "model_fingerprint": trace_pillar._generate_model_fingerprint(model),
            "data_fingerprint": trace_pillar._generate_data_fingerprint(X, y),
            "metadata": metadata or {},
        }
        
        if model_id not in self._models:
            self._models[model_id] = []
        
        self._models[model_id].append(record)
        
        return record
    
    def get_history(self, model_id: str) -> list[dict[str, Any]]:
        """Get version history for a model."""
        return self._models.get(model_id, [])
    
    def compare_versions(
        self,
        model_id: str,
        version_a: int,
        version_b: int,
    ) -> dict[str, Any]:
        """Compare two model versions."""
        history = self.get_history(model_id)
        
        if version_a > len(history) or version_b > len(history):
            return {"error": "Invalid version number"}
        
        record_a = history[version_a - 1]
        record_b = history[version_b - 1]
        
        return {
            "model_changed": record_a["model_fingerprint"] != record_b["model_fingerprint"],
            "data_changed": record_a["data_fingerprint"] != record_b["data_fingerprint"],
            "version_a": record_a,
            "version_b": record_b,
        }
