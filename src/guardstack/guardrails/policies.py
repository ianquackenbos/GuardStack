"""
Guardrail Policies for GuardStack.

Defines policy rules and conditions for guardrail enforcement.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Pattern
from dataclasses import dataclass, field
import re
import json
from datetime import datetime
import logging

from .runtime import GuardrailCheckpoint, GuardrailResult, GuardrailAction


logger = logging.getLogger(__name__)


class PolicyAction(Enum):
    """Actions a policy can take."""
    
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    WARN = "warn"
    AUDIT = "audit"
    ESCALATE = "escalate"


class ConditionOperator(Enum):
    """Operators for policy conditions."""
    
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"  # Regex
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


@dataclass
class PolicyCondition:
    """Condition for policy evaluation."""
    
    field: str  # Field to check (content, context.user_id, etc.)
    operator: ConditionOperator
    value: Any
    case_sensitive: bool = False
    
    def evaluate(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate the condition."""
        # Get field value
        if self.field == "content":
            field_value = content
        elif self.field.startswith("context."):
            key = self.field[8:]  # Remove "context."
            field_value = context.get(key)
        else:
            field_value = context.get(self.field, content)
        
        # Handle case sensitivity for strings
        if isinstance(field_value, str) and not self.case_sensitive:
            field_value = field_value.lower()
            compare_value = self.value.lower() if isinstance(self.value, str) else self.value
        else:
            compare_value = self.value
        
        # Evaluate based on operator
        op = self.operator
        
        if op == ConditionOperator.EQUALS:
            return field_value == compare_value
        
        elif op == ConditionOperator.NOT_EQUALS:
            return field_value != compare_value
        
        elif op == ConditionOperator.CONTAINS:
            if isinstance(field_value, str):
                return compare_value in field_value
            return compare_value in (field_value or [])
        
        elif op == ConditionOperator.NOT_CONTAINS:
            if isinstance(field_value, str):
                return compare_value not in field_value
            return compare_value not in (field_value or [])
        
        elif op == ConditionOperator.MATCHES:
            if field_value is None:
                return False
            flags = 0 if self.case_sensitive else re.IGNORECASE
            return bool(re.search(compare_value, str(field_value), flags))
        
        elif op == ConditionOperator.GREATER_THAN:
            return field_value is not None and field_value > compare_value
        
        elif op == ConditionOperator.LESS_THAN:
            return field_value is not None and field_value < compare_value
        
        elif op == ConditionOperator.IN:
            return field_value in compare_value
        
        elif op == ConditionOperator.NOT_IN:
            return field_value not in compare_value
        
        elif op == ConditionOperator.EXISTS:
            return field_value is not None
        
        elif op == ConditionOperator.NOT_EXISTS:
            return field_value is None
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
            "case_sensitive": self.case_sensitive,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyCondition":
        """Deserialize from dictionary."""
        return cls(
            field=data["field"],
            operator=ConditionOperator(data["operator"]),
            value=data["value"],
            case_sensitive=data.get("case_sensitive", False),
        )


@dataclass
class PolicyRule:
    """Rule within a policy."""
    
    name: str
    conditions: List[PolicyCondition]
    action: PolicyAction
    message: str = ""
    modifier: Optional[Callable[[str], str]] = None  # For MODIFY action
    priority: int = 0
    enabled: bool = True
    match_all: bool = True  # If True, all conditions must match (AND), else any (OR)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def evaluate(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> Optional[PolicyAction]:
        """
        Evaluate the rule against content and context.
        
        Returns:
            PolicyAction if rule matches, None otherwise
        """
        if not self.enabled:
            return None
        
        if not self.conditions:
            return None
        
        if self.match_all:
            # All conditions must match
            if all(c.evaluate(content, context) for c in self.conditions):
                return self.action
        else:
            # Any condition matches
            if any(c.evaluate(content, context) for c in self.conditions):
                return self.action
        
        return None
    
    def apply_modifier(self, content: str) -> str:
        """Apply modifier if action is MODIFY."""
        if self.modifier:
            return self.modifier(content)
        return content
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "conditions": [c.to_dict() for c in self.conditions],
            "action": self.action.value,
            "message": self.message,
            "priority": self.priority,
            "enabled": self.enabled,
            "match_all": self.match_all,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyRule":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            conditions=[PolicyCondition.from_dict(c) for c in data.get("conditions", [])],
            action=PolicyAction(data["action"]),
            message=data.get("message", ""),
            priority=data.get("priority", 0),
            enabled=data.get("enabled", True),
            match_all=data.get("match_all", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class GuardrailPolicy:
    """Policy containing multiple rules."""
    
    name: str
    rules: List[PolicyRule] = field(default_factory=list)
    description: str = ""
    version: str = "1.0"
    enabled: bool = True
    fail_action: PolicyAction = PolicyAction.WARN
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_rule(self, rule: PolicyRule) -> None:
        """Add a rule to the policy."""
        self.rules.append(rule)
        self.updated_at = datetime.utcnow()
    
    def remove_rule(self, name: str) -> Optional[PolicyRule]:
        """Remove a rule by name."""
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                self.updated_at = datetime.utcnow()
                return self.rules.pop(i)
        return None
    
    def evaluate(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> tuple[PolicyAction, List[PolicyRule]]:
        """
        Evaluate all rules against content.
        
        Returns:
            Tuple of (action, matching_rules)
        """
        if not self.enabled:
            return PolicyAction.ALLOW, []
        
        matching_rules = []
        highest_action = PolicyAction.ALLOW
        
        # Sort by priority (higher first)
        sorted_rules = sorted(
            [r for r in self.rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True,
        )
        
        for rule in sorted_rules:
            action = rule.evaluate(content, context)
            if action:
                matching_rules.append(rule)
                # Block takes precedence
                if action == PolicyAction.BLOCK:
                    return PolicyAction.BLOCK, matching_rules
                elif action.value > highest_action.value:
                    highest_action = action
        
        return highest_action, matching_rules
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "rules": [r.to_dict() for r in self.rules],
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "fail_action": self.fail_action.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GuardrailPolicy":
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            rules=[PolicyRule.from_dict(r) for r in data.get("rules", [])],
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
            enabled=data.get("enabled", True),
            fail_action=PolicyAction(data.get("fail_action", "warn")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "GuardrailPolicy":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


class PolicyCheckpoint(GuardrailCheckpoint):
    """Guardrail checkpoint that enforces policies."""
    
    def __init__(
        self,
        name: str = "policy_checkpoint",
        position: str = "both",
        policies: Optional[List[GuardrailPolicy]] = None,
        enabled: bool = True,
        fail_open: bool = False,
        timeout_ms: float = 5000.0,
    ):
        super().__init__(name, position, enabled, fail_open, timeout_ms)
        self.policies = policies or []
    
    async def check(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> GuardrailResult:
        """Run policy checks on content."""
        all_matching_rules = []
        highest_action = PolicyAction.ALLOW
        modified_content = content
        messages = []
        
        for policy in self.policies:
            if not policy.enabled:
                continue
            
            try:
                action, matching_rules = policy.evaluate(content, context)
                all_matching_rules.extend(matching_rules)
                
                if action == PolicyAction.BLOCK:
                    messages.extend([r.message for r in matching_rules if r.message])
                    return GuardrailResult(
                        action=GuardrailAction.BLOCK,
                        passed=False,
                        original_content=content,
                        guardrail_name=self.name,
                        reasons=messages or [f"Blocked by policy: {policy.name}"],
                        metadata={
                            "policy": policy.name,
                            "rules": [r.name for r in matching_rules],
                        },
                    )
                
                elif action == PolicyAction.MODIFY:
                    for rule in matching_rules:
                        if rule.action == PolicyAction.MODIFY:
                            modified_content = rule.apply_modifier(modified_content)
                
                if action.value > highest_action.value:
                    highest_action = action
                    
            except Exception as e:
                logger.error(f"Policy {policy.name} evaluation failed: {e}")
                if not self.fail_open:
                    return GuardrailResult(
                        action=GuardrailAction.BLOCK,
                        passed=False,
                        original_content=content,
                        guardrail_name=self.name,
                        reasons=[f"Policy evaluation failed: {str(e)}"],
                    )
        
        # Map PolicyAction to GuardrailAction
        action_map = {
            PolicyAction.ALLOW: GuardrailAction.ALLOW,
            PolicyAction.BLOCK: GuardrailAction.BLOCK,
            PolicyAction.MODIFY: GuardrailAction.MODIFY,
            PolicyAction.WARN: GuardrailAction.WARN,
            PolicyAction.AUDIT: GuardrailAction.LOG,
            PolicyAction.ESCALATE: GuardrailAction.REVIEW,
        }
        
        guardrail_action = action_map.get(highest_action, GuardrailAction.ALLOW)
        
        return GuardrailResult(
            action=guardrail_action,
            passed=True,
            original_content=content,
            modified_content=modified_content if modified_content != content else None,
            guardrail_name=self.name,
            reasons=[r.message for r in all_matching_rules if r.message],
            metadata={
                "matching_rules": [r.name for r in all_matching_rules],
                "policies_evaluated": [p.name for p in self.policies if p.enabled],
            },
        )
    
    def add_policy(self, policy: GuardrailPolicy) -> None:
        """Add a policy."""
        self.policies.append(policy)
    
    def remove_policy(self, name: str) -> Optional[GuardrailPolicy]:
        """Remove a policy by name."""
        for i, policy in enumerate(self.policies):
            if policy.name == name:
                return self.policies.pop(i)
        return None


class PolicyManager:
    """Manages multiple guardrail policies."""
    
    def __init__(self):
        self.policies: Dict[str, GuardrailPolicy] = {}
    
    def add_policy(self, policy: GuardrailPolicy) -> None:
        """Add a policy."""
        self.policies[policy.name] = policy
    
    def get_policy(self, name: str) -> Optional[GuardrailPolicy]:
        """Get a policy by name."""
        return self.policies.get(name)
    
    def remove_policy(self, name: str) -> Optional[GuardrailPolicy]:
        """Remove a policy by name."""
        return self.policies.pop(name, None)
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """List all policies."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "enabled": p.enabled,
                "rule_count": len(p.rules),
            }
            for p in self.policies.values()
        ]
    
    def enable_policy(self, name: str) -> bool:
        """Enable a policy."""
        if name in self.policies:
            self.policies[name].enabled = True
            return True
        return False
    
    def disable_policy(self, name: str) -> bool:
        """Disable a policy."""
        if name in self.policies:
            self.policies[name].enabled = False
            return True
        return False
    
    def create_checkpoint(
        self,
        name: str = "policy_manager",
        position: str = "both",
        policy_names: Optional[List[str]] = None,
    ) -> PolicyCheckpoint:
        """Create a checkpoint from selected policies."""
        if policy_names:
            policies = [
                self.policies[n]
                for n in policy_names
                if n in self.policies
            ]
        else:
            policies = list(self.policies.values())
        
        return PolicyCheckpoint(
            name=name,
            position=position,
            policies=policies,
        )
    
    def export_policies(self) -> Dict[str, Any]:
        """Export all policies."""
        return {
            name: policy.to_dict()
            for name, policy in self.policies.items()
        }
    
    def import_policies(self, data: Dict[str, Any]) -> None:
        """Import policies from dictionary."""
        for name, policy_data in data.items():
            self.policies[name] = GuardrailPolicy.from_dict(policy_data)
    
    def save_to_file(self, filepath: str) -> None:
        """Save policies to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.export_policies(), f, indent=2)
    
    def load_from_file(self, filepath: str) -> None:
        """Load policies from JSON file."""
        with open(filepath, "r") as f:
            self.import_policies(json.load(f))


# Pre-defined policies
def create_default_input_policy() -> GuardrailPolicy:
    """Create default input policy."""
    policy = GuardrailPolicy(
        name="default_input",
        description="Default input guardrail policy",
    )
    
    # Block prompt injection attempts
    policy.add_rule(PolicyRule(
        name="block_prompt_injection",
        conditions=[
            PolicyCondition(
                field="content",
                operator=ConditionOperator.MATCHES,
                value=r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
            ),
        ],
        action=PolicyAction.BLOCK,
        message="Potential prompt injection detected",
        priority=100,
    ))
    
    # Block system prompt extraction
    policy.add_rule(PolicyRule(
        name="block_system_prompt_extraction",
        conditions=[
            PolicyCondition(
                field="content",
                operator=ConditionOperator.MATCHES,
                value=r"(show|reveal|tell|print|output|display)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions)",
            ),
        ],
        action=PolicyAction.BLOCK,
        message="System prompt extraction attempt detected",
        priority=95,
    ))
    
    # Warn on potential jailbreak
    policy.add_rule(PolicyRule(
        name="warn_jailbreak_attempt",
        conditions=[
            PolicyCondition(
                field="content",
                operator=ConditionOperator.MATCHES,
                value=r"(pretend|act\s+as\s+if|imagine)\s+(you\s+)?(are|have|were|can)",
            ),
        ],
        action=PolicyAction.WARN,
        message="Potential jailbreak attempt",
        priority=80,
    ))
    
    return policy


def create_default_output_policy() -> GuardrailPolicy:
    """Create default output policy."""
    policy = GuardrailPolicy(
        name="default_output",
        description="Default output guardrail policy",
    )
    
    # Block PII in output
    policy.add_rule(PolicyRule(
        name="block_ssn_output",
        conditions=[
            PolicyCondition(
                field="content",
                operator=ConditionOperator.MATCHES,
                value=r"\b\d{3}-\d{2}-\d{4}\b",
            ),
        ],
        action=PolicyAction.BLOCK,
        message="SSN detected in output",
        priority=100,
    ))
    
    policy.add_rule(PolicyRule(
        name="block_credit_card_output",
        conditions=[
            PolicyCondition(
                field="content",
                operator=ConditionOperator.MATCHES,
                value=r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            ),
        ],
        action=PolicyAction.BLOCK,
        message="Credit card number detected in output",
        priority=100,
    ))
    
    return policy
