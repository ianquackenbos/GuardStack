"""
SPM Security Checks

Security check definitions for AI systems.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from guardstack.spm.inventory import AIAsset, AssetType

logger = logging.getLogger(__name__)


class CheckSeverity(Enum):
    """Severity levels for security checks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CheckResult:
    """Result of a security check."""
    
    check_id: str
    check_name: str
    severity: CheckSeverity
    passed: bool
    message: str
    remediation: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


class BaseCheck(ABC):
    """Base class for security checks."""
    
    check_id: str = "base"
    name: str = "Base Check"
    description: str = ""
    category: str = "general"
    severity: CheckSeverity = CheckSeverity.MEDIUM
    applicable_types: list[AssetType] = []
    
    def applies_to(self, asset: AIAsset) -> bool:
        """Check if this check applies to the asset."""
        if not self.applicable_types:
            return True
        return asset.asset_type in [t.value for t in self.applicable_types]
    
    @abstractmethod
    async def run(self, asset: AIAsset) -> CheckResult:
        """Run the security check."""
        pass
    
    def _pass(self, message: str = "Check passed", **details: Any) -> CheckResult:
        """Create a passing result."""
        return CheckResult(
            check_id=self.check_id,
            check_name=self.name,
            severity=self.severity,
            passed=True,
            message=message,
            details=details,
        )
    
    def _fail(
        self,
        message: str,
        remediation: Optional[str] = None,
        **details: Any,
    ) -> CheckResult:
        """Create a failing result."""
        return CheckResult(
            check_id=self.check_id,
            check_name=self.name,
            severity=self.severity,
            passed=False,
            message=message,
            remediation=remediation,
            details=details,
        )


# ============================================================================
# Authentication & Access Control Checks
# ============================================================================

class APIKeyRotationCheck(BaseCheck):
    """Check for API key rotation policy."""
    
    check_id = "spm-auth-001"
    name = "API Key Rotation"
    description = "Verify API keys are rotated regularly"
    category = "authentication"
    severity = CheckSeverity.HIGH
    applicable_types = [AssetType.LLM_ENDPOINT, AssetType.ML_MODEL]
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        rotation_days = config.get("api_key_rotation_days")
        
        if rotation_days is None:
            return self._fail(
                "No API key rotation policy configured",
                remediation="Configure API key rotation with maximum 90 day lifetime",
            )
        
        if rotation_days > 90:
            return self._fail(
                f"API key rotation period too long: {rotation_days} days",
                remediation="Reduce API key rotation period to 90 days or less",
                current_rotation_days=rotation_days,
            )
        
        return self._pass(
            f"API key rotation configured: {rotation_days} days",
            rotation_days=rotation_days,
        )


class RBACEnabledCheck(BaseCheck):
    """Check for Role-Based Access Control."""
    
    check_id = "spm-auth-002"
    name = "RBAC Enabled"
    description = "Verify Role-Based Access Control is enabled"
    category = "authentication"
    severity = CheckSeverity.CRITICAL
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        rbac_enabled = config.get("rbac_enabled", False)
        
        if not rbac_enabled:
            return self._fail(
                "RBAC is not enabled",
                remediation="Enable Role-Based Access Control for the AI system",
            )
        
        return self._pass("RBAC is enabled")


class MFARequiredCheck(BaseCheck):
    """Check for Multi-Factor Authentication requirement."""
    
    check_id = "spm-auth-003"
    name = "MFA Required"
    description = "Verify MFA is required for administrative access"
    category = "authentication"
    severity = CheckSeverity.HIGH
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        mfa_required = config.get("mfa_required", False)
        
        if not mfa_required:
            return self._fail(
                "MFA is not required for administrative access",
                remediation="Enable MFA requirement for all administrative access",
            )
        
        return self._pass("MFA is required for administrative access")


# ============================================================================
# Data Protection Checks
# ============================================================================

class EncryptionAtRestCheck(BaseCheck):
    """Check for encryption at rest."""
    
    check_id = "spm-data-001"
    name = "Encryption at Rest"
    description = "Verify data is encrypted at rest"
    category = "data_protection"
    severity = CheckSeverity.CRITICAL
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        encryption_enabled = config.get("encryption_at_rest", False)
        
        if not encryption_enabled:
            return self._fail(
                "Data encryption at rest is not enabled",
                remediation="Enable encryption at rest using AES-256 or equivalent",
            )
        
        encryption_algorithm = config.get("encryption_algorithm", "unknown")
        
        weak_algorithms = ["des", "3des", "rc4", "md5"]
        if encryption_algorithm.lower() in weak_algorithms:
            return self._fail(
                f"Weak encryption algorithm: {encryption_algorithm}",
                remediation="Use AES-256 or stronger encryption",
                algorithm=encryption_algorithm,
            )
        
        return self._pass(
            f"Encryption at rest enabled with {encryption_algorithm}",
            algorithm=encryption_algorithm,
        )


class EncryptionInTransitCheck(BaseCheck):
    """Check for encryption in transit."""
    
    check_id = "spm-data-002"
    name = "Encryption in Transit"
    description = "Verify data is encrypted in transit"
    category = "data_protection"
    severity = CheckSeverity.CRITICAL
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        tls_enabled = config.get("tls_enabled", False)
        
        if not tls_enabled:
            return self._fail(
                "TLS is not enabled for data in transit",
                remediation="Enable TLS 1.2 or higher for all communications",
            )
        
        tls_version = config.get("tls_version", "1.2")
        
        if float(tls_version) < 1.2:
            return self._fail(
                f"TLS version {tls_version} is outdated",
                remediation="Upgrade to TLS 1.2 or higher",
                tls_version=tls_version,
            )
        
        return self._pass(
            f"TLS {tls_version} enabled for data in transit",
            tls_version=tls_version,
        )


class PIIProtectionCheck(BaseCheck):
    """Check for PII protection measures."""
    
    check_id = "spm-data-003"
    name = "PII Protection"
    description = "Verify PII protection measures are in place"
    category = "data_protection"
    severity = CheckSeverity.HIGH
    applicable_types = [AssetType.LLM_ENDPOINT, AssetType.TRAINING_DATA]
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        pii_detection = config.get("pii_detection_enabled", False)
        pii_masking = config.get("pii_masking_enabled", False)
        
        if not pii_detection:
            return self._fail(
                "PII detection is not enabled",
                remediation="Enable PII detection using Presidio or equivalent",
            )
        
        if not pii_masking:
            return self._fail(
                "PII masking is not enabled",
                remediation="Enable automatic PII masking in inputs and outputs",
            )
        
        return self._pass("PII detection and masking enabled")


# ============================================================================
# Model Security Checks
# ============================================================================

class ModelVersioningCheck(BaseCheck):
    """Check for model versioning."""
    
    check_id = "spm-model-001"
    name = "Model Versioning"
    description = "Verify model versioning is enabled"
    category = "model_security"
    severity = CheckSeverity.MEDIUM
    applicable_types = [AssetType.ML_MODEL, AssetType.LLM_ENDPOINT]
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        versioning_enabled = config.get("versioning_enabled", False)
        
        if not versioning_enabled:
            return self._fail(
                "Model versioning is not enabled",
                remediation="Enable model versioning for traceability and rollback",
            )
        
        return self._pass("Model versioning is enabled")


class ModelSigningCheck(BaseCheck):
    """Check for model signing."""
    
    check_id = "spm-model-002"
    name = "Model Signing"
    description = "Verify models are cryptographically signed"
    category = "model_security"
    severity = CheckSeverity.HIGH
    applicable_types = [AssetType.ML_MODEL]
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        signing_enabled = config.get("model_signing_enabled", False)
        
        if not signing_enabled:
            return self._fail(
                "Model signing is not enabled",
                remediation="Enable cryptographic signing for model artifacts",
            )
        
        return self._pass("Model signing is enabled")


class InputValidationCheck(BaseCheck):
    """Check for input validation."""
    
    check_id = "spm-model-003"
    name = "Input Validation"
    description = "Verify input validation is configured"
    category = "model_security"
    severity = CheckSeverity.HIGH
    applicable_types = [AssetType.LLM_ENDPOINT, AssetType.ML_MODEL]
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        validation = config.get("input_validation", {})
        
        if not validation:
            return self._fail(
                "No input validation configured",
                remediation="Configure input validation with schema and length limits",
            )
        
        has_length_limit = "max_length" in validation
        has_schema = "schema" in validation or "allowed_types" in validation
        
        if not has_length_limit:
            return self._fail(
                "No input length limit configured",
                remediation="Set maximum input length to prevent resource exhaustion",
            )
        
        return self._pass(
            "Input validation configured",
            has_length_limit=has_length_limit,
            has_schema=has_schema,
        )


class OutputFilteringCheck(BaseCheck):
    """Check for output filtering."""
    
    check_id = "spm-model-004"
    name = "Output Filtering"
    description = "Verify output filtering is enabled"
    category = "model_security"
    severity = CheckSeverity.HIGH
    applicable_types = [AssetType.LLM_ENDPOINT]
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        output_filters = config.get("output_filters", [])
        
        recommended_filters = ["toxicity", "pii", "injection"]
        missing_filters = [f for f in recommended_filters if f not in output_filters]
        
        if len(missing_filters) == len(recommended_filters):
            return self._fail(
                "No output filters configured",
                remediation=f"Enable output filters: {', '.join(recommended_filters)}",
            )
        
        if missing_filters:
            return self._fail(
                f"Missing output filters: {', '.join(missing_filters)}",
                remediation=f"Enable additional output filters",
                missing_filters=missing_filters,
                severity=CheckSeverity.MEDIUM,
            )
        
        return self._pass(
            "All recommended output filters enabled",
            filters=output_filters,
        )


# ============================================================================
# Logging & Monitoring Checks
# ============================================================================

class AuditLoggingCheck(BaseCheck):
    """Check for audit logging."""
    
    check_id = "spm-log-001"
    name = "Audit Logging"
    description = "Verify audit logging is enabled"
    category = "logging"
    severity = CheckSeverity.HIGH
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        audit_logging = config.get("audit_logging_enabled", False)
        
        if not audit_logging:
            return self._fail(
                "Audit logging is not enabled",
                remediation="Enable comprehensive audit logging for all AI interactions",
            )
        
        retention_days = config.get("log_retention_days", 0)
        
        if retention_days < 90:
            return self._fail(
                f"Log retention period too short: {retention_days} days",
                remediation="Set log retention to at least 90 days for compliance",
                retention_days=retention_days,
            )
        
        return self._pass(
            f"Audit logging enabled with {retention_days} day retention",
            retention_days=retention_days,
        )


class MonitoringEnabledCheck(BaseCheck):
    """Check for monitoring."""
    
    check_id = "spm-log-002"
    name = "Monitoring Enabled"
    description = "Verify monitoring and alerting is configured"
    category = "logging"
    severity = CheckSeverity.MEDIUM
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        monitoring = config.get("monitoring_enabled", False)
        alerting = config.get("alerting_enabled", False)
        
        if not monitoring:
            return self._fail(
                "Monitoring is not enabled",
                remediation="Enable monitoring for performance and security metrics",
            )
        
        if not alerting:
            return self._fail(
                "Alerting is not configured",
                remediation="Configure alerting for anomaly detection",
            )
        
        return self._pass("Monitoring and alerting enabled")


# ============================================================================
# Rate Limiting & Resource Checks
# ============================================================================

class RateLimitingCheck(BaseCheck):
    """Check for rate limiting."""
    
    check_id = "spm-rate-001"
    name = "Rate Limiting"
    description = "Verify rate limiting is configured"
    category = "resource_protection"
    severity = CheckSeverity.HIGH
    applicable_types = [AssetType.LLM_ENDPOINT]
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        rate_limit = config.get("rate_limit", {})
        
        if not rate_limit:
            return self._fail(
                "No rate limiting configured",
                remediation="Configure rate limiting to prevent abuse",
            )
        
        rpm = rate_limit.get("requests_per_minute")
        daily_limit = rate_limit.get("requests_per_day")
        
        if not rpm and not daily_limit:
            return self._fail(
                "Rate limits not specified",
                remediation="Set requests_per_minute and/or requests_per_day limits",
            )
        
        return self._pass(
            "Rate limiting configured",
            requests_per_minute=rpm,
            requests_per_day=daily_limit,
        )


class TokenLimitCheck(BaseCheck):
    """Check for token limits."""
    
    check_id = "spm-rate-002"
    name = "Token Limits"
    description = "Verify token limits are configured"
    category = "resource_protection"
    severity = CheckSeverity.MEDIUM
    applicable_types = [AssetType.LLM_ENDPOINT]
    
    async def run(self, asset: AIAsset) -> CheckResult:
        config = asset.config or {}
        
        max_input_tokens = config.get("max_input_tokens")
        max_output_tokens = config.get("max_output_tokens")
        
        if not max_input_tokens:
            return self._fail(
                "No input token limit configured",
                remediation="Set max_input_tokens to prevent resource exhaustion",
            )
        
        if not max_output_tokens:
            return self._fail(
                "No output token limit configured",
                remediation="Set max_output_tokens to control costs and latency",
            )
        
        return self._pass(
            "Token limits configured",
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
        )


# ============================================================================
# Registry
# ============================================================================

def get_all_checks() -> list[BaseCheck]:
    """Get all available security checks."""
    return [
        # Authentication
        APIKeyRotationCheck(),
        RBACEnabledCheck(),
        MFARequiredCheck(),
        # Data Protection
        EncryptionAtRestCheck(),
        EncryptionInTransitCheck(),
        PIIProtectionCheck(),
        # Model Security
        ModelVersioningCheck(),
        ModelSigningCheck(),
        InputValidationCheck(),
        OutputFilteringCheck(),
        # Logging
        AuditLoggingCheck(),
        MonitoringEnabledCheck(),
        # Rate Limiting
        RateLimitingCheck(),
        TokenLimitCheck(),
    ]


def get_checks_by_category(category: str) -> list[BaseCheck]:
    """Get checks filtered by category."""
    return [c for c in get_all_checks() if c.category == category]


def get_checks_by_severity(severity: CheckSeverity) -> list[BaseCheck]:
    """Get checks filtered by severity."""
    return [c for c in get_all_checks() if c.severity == severity]
