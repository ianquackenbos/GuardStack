"""
Base Pillar for Predictive AI

Abstract base class and common types for evaluation pillars.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass, field

import numpy as np

from guardstack.models.core import RiskStatus


@dataclass
class PillarResult:
    """Result from a pillar evaluation."""
    
    pillar_name: str
    score: float
    status: RiskStatus
    findings: list[dict[str, Any]]
    metrics: dict[str, Any]
    details: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0
    samples_tested: int = 0


class BasePillar(ABC):
    """Abstract base class for predictive AI evaluation pillars."""
    
    pillar_name: str = "base"
    pillar_category: str = "predictive"
    
    @abstractmethod
    async def evaluate(
        self,
        model: Any,  # ModelWrapper
        X: np.ndarray,
        y: np.ndarray,
        sensitive_features: Optional[dict[str, np.ndarray]] = None,
    ) -> PillarResult:
        """
        Evaluate the model on this pillar.
        
        Args:
            model: ModelWrapper instance
            X: Feature matrix
            y: True labels
            sensitive_features: Dict of sensitive attribute arrays
        
        Returns:
            PillarResult with score, status, findings, and metrics
        """
        pass
    
    def _create_finding(
        self,
        finding_type: str,
        severity: str,
        message: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a standardized finding."""
        return {
            "finding_type": finding_type,
            "severity": severity,
            "message": message,
            "pillar": self.pillar_name,
            **kwargs,
        }
    
    def _score_to_status(self, score: float) -> RiskStatus:
        """Convert score to risk status."""
        if score >= 80:
            return RiskStatus.PASS
        elif score >= 60:
            return RiskStatus.WARN
        else:
            return RiskStatus.FAIL
