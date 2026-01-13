"""
Score Normalizer for GuardStack.

Normalizes raw metric values to consistent 0-1 scale using
various normalization methods (min-max, z-score, etc.).
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import numpy as np
from datetime import datetime


class NormalizationMethod(Enum):
    """Methods for normalizing scores."""
    
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    ROBUST = "robust"  # Using median and IQR
    LOG_TRANSFORM = "log_transform"
    SIGMOID = "sigmoid"
    PERCENTILE = "percentile"
    TANH = "tanh"
    CALIBRATED = "calibrated"  # Using reference distribution


@dataclass
class NormalizationConfig:
    """Configuration for score normalization."""
    
    method: NormalizationMethod
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    median: Optional[float] = None
    iqr: Optional[float] = None
    percentiles: Optional[Dict[int, float]] = None
    invert: bool = False  # Higher raw = lower normalized
    clip: bool = True  # Clip to [0, 1]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to dictionary."""
        return {
            "method": self.method.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mean": self.mean,
            "std": self.std,
            "median": self.median,
            "iqr": self.iqr,
            "percentiles": self.percentiles,
            "invert": self.invert,
            "clip": self.clip,
        }


@dataclass
class NormalizationResult:
    """Result of score normalization."""
    
    raw_value: float
    normalized_value: float
    method_used: NormalizationMethod
    config: NormalizationConfig
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScoreNormalizer:
    """
    Normalizes raw evaluation metrics to a consistent 0-1 scale.
    
    Supports various normalization methods and handles different
    metric types (higher-is-better, lower-is-better).
    """
    
    # Pre-configured normalizers for common metrics
    DEFAULT_CONFIGS: Dict[str, NormalizationConfig] = {
        # Accuracy-like metrics (0-1, higher is better)
        "accuracy": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.0,
            max_value=1.0,
        ),
        "precision": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.0,
            max_value=1.0,
        ),
        "recall": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.0,
            max_value=1.0,
        ),
        "f1_score": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.0,
            max_value=1.0,
        ),
        "auc_roc": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.5,  # Random baseline
            max_value=1.0,
        ),
        
        # Error metrics (lower is better)
        "mse": NormalizationConfig(
            method=NormalizationMethod.LOG_TRANSFORM,
            invert=True,
        ),
        "rmse": NormalizationConfig(
            method=NormalizationMethod.LOG_TRANSFORM,
            invert=True,
        ),
        "mae": NormalizationConfig(
            method=NormalizationMethod.LOG_TRANSFORM,
            invert=True,
        ),
        
        # Fairness metrics (closer to 0 is better)
        "demographic_parity_diff": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.0,
            max_value=1.0,
            invert=True,  # 0 diff = 1.0 score
        ),
        "equalized_odds_diff": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.0,
            max_value=1.0,
            invert=True,
        ),
        "disparate_impact_ratio": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.8,  # 4/5ths rule threshold
            max_value=1.2,
        ),
        
        # Privacy metrics
        "epsilon": NormalizationConfig(
            method=NormalizationMethod.LOG_TRANSFORM,
            invert=True,  # Lower epsilon = better privacy
        ),
        "membership_inference_auc": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.5,
            max_value=1.0,
            invert=True,  # 0.5 AUC = no leakage
        ),
        
        # Toxicity/safety metrics
        "toxicity_score": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.0,
            max_value=1.0,
            invert=True,  # Lower toxicity = better
        ),
        "jailbreak_success_rate": NormalizationConfig(
            method=NormalizationMethod.MIN_MAX,
            min_value=0.0,
            max_value=1.0,
            invert=True,
        ),
    }
    
    def __init__(
        self,
        default_method: NormalizationMethod = NormalizationMethod.MIN_MAX,
        custom_configs: Optional[Dict[str, NormalizationConfig]] = None,
    ):
        self.default_method = default_method
        self.configs = {**self.DEFAULT_CONFIGS}
        if custom_configs:
            self.configs.update(custom_configs)
    
    def normalize(
        self,
        value: float,
        metric_name: Optional[str] = None,
        config: Optional[NormalizationConfig] = None,
        reference_values: Optional[List[float]] = None,
    ) -> NormalizationResult:
        """
        Normalize a raw metric value to 0-1 scale.
        
        Args:
            value: Raw metric value
            metric_name: Name of metric (for default config lookup)
            config: Explicit normalization config (overrides metric_name)
            reference_values: Optional reference distribution for calibration
            
        Returns:
            NormalizationResult with normalized value and metadata
        """
        # Determine config to use
        if config is None:
            if metric_name and metric_name in self.configs:
                config = self.configs[metric_name]
            else:
                config = NormalizationConfig(method=self.default_method)
        
        # Handle reference values for adaptive methods
        if reference_values and config.method in (
            NormalizationMethod.Z_SCORE,
            NormalizationMethod.ROBUST,
            NormalizationMethod.PERCENTILE,
            NormalizationMethod.CALIBRATED,
        ):
            config = self._update_config_from_reference(config, reference_values)
        
        # Apply normalization
        normalized = self._apply_normalization(value, config)
        
        # Handle inversion (lower-is-better metrics)
        if config.invert:
            normalized = 1.0 - normalized
        
        # Clip to [0, 1] if configured
        if config.clip:
            normalized = max(0.0, min(1.0, normalized))
        
        return NormalizationResult(
            raw_value=value,
            normalized_value=normalized,
            method_used=config.method,
            config=config,
            metadata={
                "metric_name": metric_name,
                "inverted": config.invert,
                "clipped": config.clip,
            },
        )
    
    def normalize_batch(
        self,
        values: Dict[str, float],
        configs: Optional[Dict[str, NormalizationConfig]] = None,
    ) -> Dict[str, NormalizationResult]:
        """
        Normalize multiple metric values.
        
        Args:
            values: Dictionary of metric_name -> raw_value
            configs: Optional config overrides per metric
            
        Returns:
            Dictionary of metric_name -> NormalizationResult
        """
        configs = configs or {}
        results = {}
        
        for metric_name, value in values.items():
            config = configs.get(metric_name)
            results[metric_name] = self.normalize(value, metric_name, config)
        
        return results
    
    def _apply_normalization(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Apply the specified normalization method."""
        method = config.method
        
        if method == NormalizationMethod.MIN_MAX:
            return self._min_max_normalize(value, config)
        
        elif method == NormalizationMethod.Z_SCORE:
            return self._z_score_normalize(value, config)
        
        elif method == NormalizationMethod.ROBUST:
            return self._robust_normalize(value, config)
        
        elif method == NormalizationMethod.LOG_TRANSFORM:
            return self._log_normalize(value, config)
        
        elif method == NormalizationMethod.SIGMOID:
            return self._sigmoid_normalize(value, config)
        
        elif method == NormalizationMethod.PERCENTILE:
            return self._percentile_normalize(value, config)
        
        elif method == NormalizationMethod.TANH:
            return self._tanh_normalize(value, config)
        
        elif method == NormalizationMethod.CALIBRATED:
            return self._calibrated_normalize(value, config)
        
        else:
            raise ValueError(f"Unknown normalization method: {method}")
    
    def _min_max_normalize(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Min-max scaling to [0, 1]."""
        min_val = config.min_value if config.min_value is not None else 0.0
        max_val = config.max_value if config.max_value is not None else 1.0
        
        if max_val == min_val:
            return 0.5
        
        return (value - min_val) / (max_val - min_val)
    
    def _z_score_normalize(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Z-score normalization mapped to [0, 1] via sigmoid."""
        mean = config.mean if config.mean is not None else 0.0
        std = config.std if config.std is not None else 1.0
        
        if std == 0:
            return 0.5
        
        z = (value - mean) / std
        # Map z-score to [0, 1] using sigmoid
        return 1.0 / (1.0 + np.exp(-z))
    
    def _robust_normalize(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Robust normalization using median and IQR."""
        median = config.median if config.median is not None else 0.5
        iqr = config.iqr if config.iqr is not None else 1.0
        
        if iqr == 0:
            return 0.5
        
        # Scale to approximately [0, 1]
        normalized = (value - median) / (2.0 * iqr) + 0.5
        return normalized
    
    def _log_normalize(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Log transform for heavy-tailed distributions."""
        # Handle non-positive values
        value = max(value, 1e-10)
        log_val = np.log(value)
        
        # Map to [0, 1] using configured bounds or sigmoid
        if config.min_value is not None and config.max_value is not None:
            log_min = np.log(max(config.min_value, 1e-10))
            log_max = np.log(max(config.max_value, 1e-10))
            if log_max == log_min:
                return 0.5
            return (log_val - log_min) / (log_max - log_min)
        else:
            # Sigmoid mapping for unbounded
            return 1.0 / (1.0 + np.exp(-log_val))
    
    def _sigmoid_normalize(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Sigmoid (logistic) transformation."""
        mean = config.mean if config.mean is not None else 0.0
        # Use std as scale parameter
        scale = config.std if config.std is not None else 1.0
        
        if scale == 0:
            return 0.5
        
        return 1.0 / (1.0 + np.exp(-(value - mean) / scale))
    
    def _percentile_normalize(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Normalize based on percentile in reference distribution."""
        if not config.percentiles:
            return 0.5
        
        # Find position in percentile distribution
        percentiles = sorted(config.percentiles.items())
        
        for i, (pct, pct_value) in enumerate(percentiles):
            if value <= pct_value:
                if i == 0:
                    return pct / 100.0
                prev_pct, prev_value = percentiles[i - 1]
                # Linear interpolation
                ratio = (value - prev_value) / (pct_value - prev_value) if pct_value != prev_value else 0.5
                return (prev_pct + ratio * (pct - prev_pct)) / 100.0
        
        return 1.0  # Above all percentiles
    
    def _tanh_normalize(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Hyperbolic tangent normalization to [0, 1]."""
        mean = config.mean if config.mean is not None else 0.0
        scale = config.std if config.std is not None else 1.0
        
        if scale == 0:
            return 0.5
        
        # tanh maps to [-1, 1], shift to [0, 1]
        return (np.tanh((value - mean) / scale) + 1.0) / 2.0
    
    def _calibrated_normalize(
        self,
        value: float,
        config: NormalizationConfig,
    ) -> float:
        """Calibrated normalization using reference distribution."""
        # Use percentile-based approach with reference
        if config.percentiles:
            return self._percentile_normalize(value, config)
        # Fall back to z-score with reference stats
        return self._z_score_normalize(value, config)
    
    def _update_config_from_reference(
        self,
        config: NormalizationConfig,
        reference: List[float],
    ) -> NormalizationConfig:
        """Update config statistics from reference distribution."""
        arr = np.array(reference)
        
        return NormalizationConfig(
            method=config.method,
            min_value=float(np.min(arr)),
            max_value=float(np.max(arr)),
            mean=float(np.mean(arr)),
            std=float(np.std(arr)),
            median=float(np.median(arr)),
            iqr=float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            percentiles={
                p: float(np.percentile(arr, p))
                for p in [5, 10, 25, 50, 75, 90, 95]
            },
            invert=config.invert,
            clip=config.clip,
        )
    
    def fit(
        self,
        metric_name: str,
        values: List[float],
        method: Optional[NormalizationMethod] = None,
        invert: bool = False,
    ) -> NormalizationConfig:
        """
        Fit normalizer to a set of reference values.
        
        Creates and stores a NormalizationConfig based on
        the distribution of the provided values.
        
        Args:
            metric_name: Name of the metric
            values: Reference values to fit
            method: Normalization method (uses default if None)
            invert: Whether higher raw = lower normalized
            
        Returns:
            Fitted NormalizationConfig
        """
        method = method or self.default_method
        arr = np.array(values)
        
        config = NormalizationConfig(
            method=method,
            min_value=float(np.min(arr)),
            max_value=float(np.max(arr)),
            mean=float(np.mean(arr)),
            std=float(np.std(arr)),
            median=float(np.median(arr)),
            iqr=float(np.percentile(arr, 75) - np.percentile(arr, 25)),
            percentiles={
                p: float(np.percentile(arr, p))
                for p in [5, 10, 25, 50, 75, 90, 95]
            },
            invert=invert,
        )
        
        self.configs[metric_name] = config
        return config
    
    def get_config(self, metric_name: str) -> Optional[NormalizationConfig]:
        """Get stored config for a metric."""
        return self.configs.get(metric_name)
    
    def set_config(
        self,
        metric_name: str,
        config: NormalizationConfig,
    ) -> None:
        """Set config for a metric."""
        self.configs[metric_name] = config
