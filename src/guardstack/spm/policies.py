"""
SPM Policy Engine

Define and enforce security policies for AI systems.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from guardstack.spm.inventory import AIAsset
from guardstack.spm.checks import CheckSeverity

logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """Actions to take when policy is violated."""
    ALERT = "alert"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    LOG = "log"


class PolicyStatus(Enum):
    """Policy status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"


@dataclass
class PolicyViolation:
    """Record of a policy violation."""
    
    policy_id: str
    policy_name: str
    asset_id: str
    severity: CheckSeverity
    message: str
    action_taken: PolicyAction
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Policy:
    """Security policy definition."""
    
    policy_id: str
    name: str
    description: str
    severity: CheckSeverity
    condition: str  # Expression to evaluate
    action: PolicyAction
    status: PolicyStatus = PolicyStatus.ACTIVE
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "condition": self.condition,
            "action": self.action.value,
            "status": self.status.value,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class PolicyEngine:
    """
    Policy enforcement engine.
    
    Evaluates assets against security policies.
    """
    
    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._violations: list[PolicyViolation] = []
        self._custom_functions: dict[str, Callable] = {}
    
    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self._policies[policy.policy_id] = policy
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy."""
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False
    
    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        return self._policies.get(policy_id)
    
    def list_policies(
        self,
        status: Optional[PolicyStatus] = None,
        severity: Optional[CheckSeverity] = None,
    ) -> list[Policy]:
        """List policies with optional filters."""
        policies = list(self._policies.values())
        
        if status:
            policies = [p for p in policies if p.status == status]
        
        if severity:
            policies = [p for p in policies if p.severity == severity]
        
        return policies
    
    def register_function(
        self,
        name: str,
        func: Callable[[AIAsset], Any],
    ) -> None:
        """Register a custom function for use in conditions."""
        self._custom_functions[name] = func
    
    def evaluate(self, asset: AIAsset) -> list[PolicyViolation]:
        """
        Evaluate all active policies against an asset.
        
        Returns list of violations.
        """
        violations = []
        
        active_policies = [
            p for p in self._policies.values()
            if p.status == PolicyStatus.ACTIVE
        ]
        
        for policy in active_policies:
            try:
                result = self._evaluate_condition(policy.condition, asset)
                
                if result:
                    violation = PolicyViolation(
                        policy_id=policy.policy_id,
                        policy_name=policy.name,
                        asset_id=asset.asset_id,
                        severity=policy.severity,
                        message=f"Policy '{policy.name}' violated",
                        action_taken=policy.action,
                        details={
                            "condition": policy.condition,
                            "asset_name": asset.name,
                        },
                    )
                    violations.append(violation)
                    self._violations.append(violation)
                    
                    # Execute action
                    self._execute_action(policy, asset, violation)
                    
            except Exception as e:
                logger.error(f"Error evaluating policy {policy.policy_id}: {e}")
        
        return violations
    
    def _evaluate_condition(
        self,
        condition: str,
        asset: AIAsset,
    ) -> bool:
        """Evaluate a policy condition against an asset."""
        # Build evaluation context
        context = {
            "asset": asset,
            "config": asset.config or {},
            "metadata": asset.metadata or {},
            "tags": asset.tags or [],
            "asset_type": asset.asset_type,
            "status": asset.status.value,
            "risk_level": asset.risk_level or "unclassified",
            "data_classification": asset.data_classification or "unclassified",
        }
        
        # Add custom functions
        context.update(self._custom_functions)
        
        # Simple expression evaluator
        # In production, use a proper expression language (e.g., CEL)
        try:
            return self._safe_eval(condition, context)
        except Exception as e:
            logger.warning(f"Condition evaluation error: {e}")
            return False
    
    def _safe_eval(
        self,
        expression: str,
        context: dict[str, Any],
    ) -> bool:
        """Safely evaluate an expression."""
        # Replace common patterns with Python-safe equivalents
        expression = expression.replace("&&", " and ")
        expression = expression.replace("||", " or ")
        expression = expression.replace("!", " not ")
        
        # Only allow safe operations
        safe_builtins = {
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "any": any,
            "all": all,
            "min": min,
            "max": max,
            "sum": sum,
            "True": True,
            "False": False,
            "None": None,
        }
        
        # Merge context
        eval_context = {**safe_builtins, **context}
        
        # Validate expression doesn't contain dangerous operations
        dangerous_patterns = [
            r"__\w+__",  # Dunder methods
            r"import\s+",
            r"exec\s*\(",
            r"eval\s*\(",
            r"compile\s*\(",
            r"open\s*\(",
            r"file\s*\(",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression):
                raise ValueError(f"Dangerous pattern in expression: {pattern}")
        
        return eval(expression, {"__builtins__": {}}, eval_context)
    
    def _execute_action(
        self,
        policy: Policy,
        asset: AIAsset,
        violation: PolicyViolation,
    ) -> None:
        """Execute the policy action."""
        if policy.action == PolicyAction.ALERT:
            logger.warning(
                f"POLICY ALERT: {policy.name} violated by {asset.name}"
            )
        elif policy.action == PolicyAction.BLOCK:
            logger.error(
                f"POLICY BLOCK: {policy.name} - blocking {asset.name}"
            )
            # In real implementation, would disable the asset
        elif policy.action == PolicyAction.QUARANTINE:
            logger.warning(
                f"POLICY QUARANTINE: {policy.name} - quarantining {asset.name}"
            )
            # In real implementation, would move asset to quarantine
        elif policy.action == PolicyAction.LOG:
            logger.info(
                f"POLICY LOG: {policy.name} violated by {asset.name}"
            )
    
    def get_violations(
        self,
        asset_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        since: Optional[str] = None,
    ) -> list[PolicyViolation]:
        """Get recorded violations with optional filters."""
        violations = self._violations
        
        if asset_id:
            violations = [v for v in violations if v.asset_id == asset_id]
        
        if policy_id:
            violations = [v for v in violations if v.policy_id == policy_id]
        
        if since:
            violations = [v for v in violations if v.timestamp >= since]
        
        return violations
    
    def clear_violations(self) -> None:
        """Clear violation history."""
        self._violations = []


# ============================================================================
# Default Policies
# ============================================================================

def get_default_policies() -> list[Policy]:
    """Get default security policies."""
    return [
        Policy(
            policy_id="pol-001",
            name="No Public AI Endpoints",
            description="AI endpoints must not be publicly accessible without authentication",
            severity=CheckSeverity.CRITICAL,
            condition="config.get('public_access', False) and not config.get('authentication_required', False)",
            action=PolicyAction.BLOCK,
            tags=["security", "access-control"],
        ),
        Policy(
            policy_id="pol-002",
            name="PII Protection Required",
            description="Assets handling PII must have PII detection enabled",
            severity=CheckSeverity.HIGH,
            condition="data_classification == 'confidential' and not config.get('pii_detection_enabled', False)",
            action=PolicyAction.ALERT,
            tags=["privacy", "compliance"],
        ),
        Policy(
            policy_id="pol-003",
            name="High Risk Model Review",
            description="High risk models must be reviewed",
            severity=CheckSeverity.HIGH,
            condition="risk_level == 'high' and not metadata.get('reviewed', False)",
            action=PolicyAction.ALERT,
            tags=["governance", "review"],
        ),
        Policy(
            policy_id="pol-004",
            name="Encryption Required",
            description="All AI assets must use encryption",
            severity=CheckSeverity.CRITICAL,
            condition="not config.get('encryption_at_rest', False) or not config.get('tls_enabled', False)",
            action=PolicyAction.BLOCK,
            tags=["security", "encryption"],
        ),
        Policy(
            policy_id="pol-005",
            name="Rate Limiting Required",
            description="LLM endpoints must have rate limiting",
            severity=CheckSeverity.HIGH,
            condition="asset_type == 'llm_endpoint' and not config.get('rate_limit', {})",
            action=PolicyAction.ALERT,
            tags=["security", "availability"],
        ),
        Policy(
            policy_id="pol-006",
            name="Audit Logging Required",
            description="Production assets must have audit logging",
            severity=CheckSeverity.HIGH,
            condition="status == 'active' and not config.get('audit_logging_enabled', False)",
            action=PolicyAction.ALERT,
            tags=["compliance", "logging"],
        ),
        Policy(
            policy_id="pol-007",
            name="Model Versioning Required",
            description="ML models must have versioning enabled",
            severity=CheckSeverity.MEDIUM,
            condition="asset_type == 'ml_model' and not config.get('versioning_enabled', False)",
            action=PolicyAction.LOG,
            tags=["governance", "traceability"],
        ),
        Policy(
            policy_id="pol-008",
            name="Output Filtering Required",
            description="LLM endpoints must have output filtering",
            severity=CheckSeverity.HIGH,
            condition="asset_type == 'llm_endpoint' and len(config.get('output_filters', [])) == 0",
            action=PolicyAction.ALERT,
            tags=["security", "content-safety"],
        ),
    ]


def create_policy_engine_with_defaults() -> PolicyEngine:
    """Create a policy engine with default policies."""
    engine = PolicyEngine()
    
    for policy in get_default_policies():
        engine.add_policy(policy)
    
    return engine
