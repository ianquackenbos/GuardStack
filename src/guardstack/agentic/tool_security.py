"""
Tool Security Checker

Security analysis for agent tools and functions.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ToolRiskLevel(Enum):
    """Risk levels for tools."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


class ToolPermission(Enum):
    """Permission types for tools."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    ADMIN = "admin"


@dataclass
class ToolSecurityProfile:
    """Security profile for a tool."""
    
    tool_name: str
    risk_level: ToolRiskLevel
    permissions: list[ToolPermission]
    description: str = ""
    allowed_arguments: dict[str, Any] = field(default_factory=dict)
    blocked_patterns: list[str] = field(default_factory=list)
    rate_limit: Optional[int] = None
    requires_approval: bool = False
    audit_required: bool = True


class ToolSecurityChecker:
    """
    Security checker for agent tools.
    
    Analyzes tools for:
    - Permission requirements
    - Risk level assessment
    - Argument validation
    - Pattern blocking
    """
    
    def __init__(self) -> None:
        self._profiles: dict[str, ToolSecurityProfile] = {}
        self._default_blocked_patterns = [
            r"rm\s+-rf",
            r"sudo\s+",
            r"chmod\s+777",
            r";\s*rm\s+",
            r"\|\s*rm\s+",
            r"DROP\s+TABLE",
            r"DELETE\s+FROM\s+\w+\s*;",
            r"TRUNCATE\s+TABLE",
            r"<script[\s>]",
            r"javascript:",
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__",
            r"os\.system",
            r"subprocess\.",
            r"shell=True",
        ]
    
    def register_tool(self, profile: ToolSecurityProfile) -> None:
        """Register a tool security profile."""
        self._profiles[profile.tool_name] = profile
    
    def get_profile(self, tool_name: str) -> Optional[ToolSecurityProfile]:
        """Get security profile for a tool."""
        return self._profiles.get(tool_name)
    
    def analyze_tool(
        self,
        tool_name: str,
        tool_schema: Optional[dict[str, Any]] = None,
    ) -> ToolSecurityProfile:
        """
        Analyze a tool and generate security profile.
        
        Args:
            tool_name: Name of the tool
            tool_schema: Optional JSON schema for the tool
        
        Returns:
            Generated security profile
        """
        # Check for existing profile
        if tool_name in self._profiles:
            return self._profiles[tool_name]
        
        # Analyze based on name and schema
        risk_level = self._assess_risk_from_name(tool_name)
        permissions = self._infer_permissions(tool_name, tool_schema)
        
        profile = ToolSecurityProfile(
            tool_name=tool_name,
            risk_level=risk_level,
            permissions=permissions,
            blocked_patterns=self._default_blocked_patterns.copy(),
            requires_approval=risk_level in [ToolRiskLevel.CRITICAL, ToolRiskLevel.HIGH],
            audit_required=risk_level != ToolRiskLevel.SAFE,
        )
        
        return profile
    
    def check_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> tuple[bool, str, ToolRiskLevel]:
        """
        Check if a tool call is safe.
        
        Returns:
            Tuple of (is_safe, reason, risk_level)
        """
        profile = self._profiles.get(tool_name)
        
        if not profile:
            # Generate temporary profile
            profile = self.analyze_tool(tool_name)
        
        # Check blocked patterns
        args_str = str(arguments)
        for pattern in profile.blocked_patterns:
            if re.search(pattern, args_str, re.IGNORECASE):
                return False, f"Blocked pattern detected: {pattern}", ToolRiskLevel.CRITICAL
        
        # Check allowed arguments if specified
        if profile.allowed_arguments:
            for key, value in arguments.items():
                if key in profile.allowed_arguments:
                    allowed = profile.allowed_arguments[key]
                    if isinstance(allowed, list) and value not in allowed:
                        return False, f"Invalid value for {key}", profile.risk_level
                    elif isinstance(allowed, dict):
                        if "pattern" in allowed:
                            if not re.match(allowed["pattern"], str(value)):
                                return False, f"Value for {key} doesn't match pattern", profile.risk_level
                        if "max_length" in allowed:
                            if len(str(value)) > allowed["max_length"]:
                                return False, f"Value for {key} exceeds max length", profile.risk_level
        
        # Check for dangerous patterns in values
        danger_result = self._check_dangerous_values(arguments)
        if not danger_result[0]:
            return danger_result
        
        return True, "", profile.risk_level
    
    def _assess_risk_from_name(self, tool_name: str) -> ToolRiskLevel:
        """Assess risk level from tool name."""
        tool_lower = tool_name.lower()
        
        critical_keywords = [
            "exec", "execute", "shell", "command", "system",
            "delete_all", "drop", "truncate", "admin", "root",
            "sudo", "privilege",
        ]
        
        high_keywords = [
            "delete", "remove", "write", "modify", "update",
            "create", "insert", "upload", "download", "install",
            "uninstall", "deploy",
        ]
        
        medium_keywords = [
            "read", "get", "fetch", "query", "search",
            "list", "browse", "access", "retrieve",
        ]
        
        low_keywords = [
            "view", "display", "show", "print", "format",
            "parse", "validate", "check",
        ]
        
        for keyword in critical_keywords:
            if keyword in tool_lower:
                return ToolRiskLevel.CRITICAL
        
        for keyword in high_keywords:
            if keyword in tool_lower:
                return ToolRiskLevel.HIGH
        
        for keyword in medium_keywords:
            if keyword in tool_lower:
                return ToolRiskLevel.MEDIUM
        
        for keyword in low_keywords:
            if keyword in tool_lower:
                return ToolRiskLevel.LOW
        
        return ToolRiskLevel.MEDIUM  # Default
    
    def _infer_permissions(
        self,
        tool_name: str,
        tool_schema: Optional[dict[str, Any]],
    ) -> list[ToolPermission]:
        """Infer required permissions from tool name and schema."""
        permissions = []
        tool_lower = tool_name.lower()
        
        # Read permissions
        if any(k in tool_lower for k in ["read", "get", "fetch", "query", "list", "search"]):
            permissions.append(ToolPermission.READ)
        
        # Write permissions
        if any(k in tool_lower for k in ["write", "create", "update", "insert", "modify", "set"]):
            permissions.append(ToolPermission.WRITE)
        
        # Execute permissions
        if any(k in tool_lower for k in ["exec", "execute", "run", "shell", "command"]):
            permissions.append(ToolPermission.EXECUTE)
        
        # Network permissions
        if any(k in tool_lower for k in ["http", "api", "request", "fetch", "download", "upload"]):
            permissions.append(ToolPermission.NETWORK)
        
        # Filesystem permissions
        if any(k in tool_lower for k in ["file", "directory", "folder", "path"]):
            permissions.append(ToolPermission.FILESYSTEM)
        
        # Database permissions
        if any(k in tool_lower for k in ["sql", "database", "db", "query", "table"]):
            permissions.append(ToolPermission.DATABASE)
        
        # Admin permissions
        if any(k in tool_lower for k in ["admin", "sudo", "root", "privilege", "permission"]):
            permissions.append(ToolPermission.ADMIN)
        
        return permissions if permissions else [ToolPermission.READ]
    
    def _check_dangerous_values(
        self,
        arguments: dict[str, Any],
    ) -> tuple[bool, str, ToolRiskLevel]:
        """Check argument values for dangerous patterns."""
        for key, value in arguments.items():
            value_str = str(value)
            
            # Check for command injection
            if re.search(r'[;&|`$]', value_str):
                return False, f"Potential command injection in {key}", ToolRiskLevel.CRITICAL
            
            # Check for path traversal
            if re.search(r'\.\.[/\\]', value_str):
                return False, f"Path traversal attempt in {key}", ToolRiskLevel.HIGH
            
            # Check for SQL injection patterns
            sql_patterns = [
                r"'\s*OR\s+",
                r"'\s*AND\s+",
                r"--\s*$",
                r";\s*DROP\s+",
                r"UNION\s+SELECT",
            ]
            for pattern in sql_patterns:
                if re.search(pattern, value_str, re.IGNORECASE):
                    return False, f"Potential SQL injection in {key}", ToolRiskLevel.CRITICAL
        
        return True, "", ToolRiskLevel.SAFE


# ============================================================================
# Default Tool Profiles
# ============================================================================

def get_common_tool_profiles() -> list[ToolSecurityProfile]:
    """Get security profiles for common tools."""
    return [
        # File operations
        ToolSecurityProfile(
            tool_name="read_file",
            risk_level=ToolRiskLevel.MEDIUM,
            permissions=[ToolPermission.READ, ToolPermission.FILESYSTEM],
            allowed_arguments={
                "path": {"pattern": r"^[a-zA-Z0-9_\-./]+$", "max_length": 500},
            },
            blocked_patterns=[r"\.\.\/", r"\/etc\/", r"\/root\/"],
        ),
        ToolSecurityProfile(
            tool_name="write_file",
            risk_level=ToolRiskLevel.HIGH,
            permissions=[ToolPermission.WRITE, ToolPermission.FILESYSTEM],
            requires_approval=True,
            blocked_patterns=[r"\.\.\/", r"\/etc\/", r"\/root\/", r"\.exe$", r"\.sh$"],
        ),
        ToolSecurityProfile(
            tool_name="delete_file",
            risk_level=ToolRiskLevel.HIGH,
            permissions=[ToolPermission.WRITE, ToolPermission.FILESYSTEM],
            requires_approval=True,
        ),
        # Network operations
        ToolSecurityProfile(
            tool_name="http_request",
            risk_level=ToolRiskLevel.MEDIUM,
            permissions=[ToolPermission.NETWORK],
            blocked_patterns=[r"localhost", r"127\.0\.0\.1", r"0\.0\.0\.0", r"169\.254\."],
        ),
        # Database operations
        ToolSecurityProfile(
            tool_name="sql_query",
            risk_level=ToolRiskLevel.HIGH,
            permissions=[ToolPermission.DATABASE, ToolPermission.READ],
            blocked_patterns=[r"DROP\s+", r"DELETE\s+FROM", r"TRUNCATE\s+", r"ALTER\s+"],
        ),
        ToolSecurityProfile(
            tool_name="sql_execute",
            risk_level=ToolRiskLevel.CRITICAL,
            permissions=[ToolPermission.DATABASE, ToolPermission.WRITE, ToolPermission.EXECUTE],
            requires_approval=True,
        ),
        # Shell operations
        ToolSecurityProfile(
            tool_name="run_command",
            risk_level=ToolRiskLevel.CRITICAL,
            permissions=[ToolPermission.EXECUTE],
            requires_approval=True,
            blocked_patterns=[
                r"rm\s+", r"sudo\s+", r"chmod\s+", r"chown\s+",
                r"curl\s+", r"wget\s+", r"nc\s+", r"netcat\s+",
            ],
        ),
    ]
