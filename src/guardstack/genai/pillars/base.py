"""
Base Pillar Interface

Abstract base class for all evaluation pillars.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from guardstack.connectors.base import ModelConnector, ModelSession
from guardstack.models.core import RiskStatus


@dataclass
class PillarResult:
    """Result of a single pillar evaluation."""
    
    pillar_name: str
    score: float  # 0-100
    status: RiskStatus = RiskStatus.WARN
    
    # Detailed results
    findings: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    
    # Error handling
    error: Optional[str] = None
    
    # Execution info
    execution_time_ms: int = 0
    samples_tested: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pillar_name": self.pillar_name,
            "score": self.score,
            "status": self.status.value,
            "findings": self.findings,
            "metrics": self.metrics,
            "details": self.details,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "samples_tested": self.samples_tested,
            "created_at": self.created_at.isoformat(),
        }


class BasePillar(ABC):
    """
    Abstract base class for evaluation pillars.
    
    Each pillar must implement:
    - evaluate(): Run the pillar evaluation
    - get_standard_prompts(): Return standard test prompts
    """
    
    pillar_name: str = "base"
    pillar_category: str = "genai"
    
    @abstractmethod
    async def evaluate(
        self,
        connector: ModelConnector,
        session: ModelSession,
        prompts: list[str],
    ) -> PillarResult:
        """
        Run the pillar evaluation.
        
        Args:
            connector: Model connector for invoking the model.
            session: Active model session.
            prompts: List of test prompts to evaluate.
        
        Returns:
            PillarResult with score, status, and findings.
        """
        ...
    
    @abstractmethod
    def get_standard_prompts(self) -> list[str]:
        """
        Get standard test prompts for this pillar.
        
        Returns:
            List of prompt strings for testing.
        """
        ...
    
    def _score_to_status(self, score: float) -> RiskStatus:
        """Convert numeric score to risk status."""
        if score >= 80:
            return RiskStatus.PASS
        elif score >= 50:
            return RiskStatus.WARN
        else:
            return RiskStatus.FAIL
    
    def _create_finding(
        self,
        finding_type: str,
        severity: str,
        message: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Create a standardized finding dict."""
        return {
            "id": str(uuid4()),
            "pillar": self.pillar_name,
            "type": finding_type,
            "severity": severity,  # critical, high, medium, low, info
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }
