"""
MCP Interceptor

Intercepts and validates Model Context Protocol (MCP) tool calls.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class InterceptAction(Enum):
    """Actions for intercepted calls."""
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    AUDIT = "audit"


@dataclass
class InterceptResult:
    """Result of intercepting a tool call."""
    
    action: InterceptAction
    original_call: dict[str, Any]
    modified_call: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    risk_score: float = 0.0
    latency_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """Represents a tool/function call from an agent."""
    
    tool_name: str
    arguments: dict[str, Any]
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    context: dict[str, Any] = field(default_factory=dict)


class MCPInterceptor:
    """
    Model Context Protocol Interceptor.
    
    Intercepts, validates, and optionally modifies tool calls
    from AI agents before execution.
    
    Features:
    - Tool call validation
    - Argument sanitization
    - Rate limiting
    - Audit logging
    - Risk scoring
    """
    
    def __init__(
        self,
        allowed_tools: Optional[list[str]] = None,
        blocked_tools: Optional[list[str]] = None,
        rate_limit_per_minute: int = 60,
        enable_audit: bool = True,
    ) -> None:
        self.allowed_tools = set(allowed_tools) if allowed_tools else None
        self.blocked_tools = set(blocked_tools) if blocked_tools else set()
        self.rate_limit = rate_limit_per_minute
        self.enable_audit = enable_audit
        
        # Validators and modifiers
        self._validators: list[Callable[[ToolCall], tuple[bool, str]]] = []
        self._modifiers: list[Callable[[ToolCall], ToolCall]] = []
        self._risk_scorers: list[Callable[[ToolCall], float]] = []
        
        # Rate limiting state
        self._call_timestamps: dict[str, list[float]] = {}
        
        # Audit log
        self._audit_log: list[InterceptResult] = []
        
        # Initialize default validators
        self._setup_default_validators()
    
    def _setup_default_validators(self) -> None:
        """Set up default validation rules."""
        # Validate tool name
        self.add_validator(self._validate_tool_allowed)
        
        # Validate arguments
        self.add_validator(self._validate_arguments)
        
        # Add default risk scorer
        self.add_risk_scorer(self._default_risk_scorer)
    
    def add_validator(
        self,
        validator: Callable[[ToolCall], tuple[bool, str]],
    ) -> None:
        """Add a custom validator."""
        self._validators.append(validator)
    
    def add_modifier(
        self,
        modifier: Callable[[ToolCall], ToolCall],
    ) -> None:
        """Add a custom modifier."""
        self._modifiers.append(modifier)
    
    def add_risk_scorer(
        self,
        scorer: Callable[[ToolCall], float],
    ) -> None:
        """Add a risk scoring function."""
        self._risk_scorers.append(scorer)
    
    async def intercept(self, call: ToolCall) -> InterceptResult:
        """
        Intercept and process a tool call.
        
        Args:
            call: The tool call to intercept
        
        Returns:
            InterceptResult with action to take
        """
        start_time = time.time()
        
        # Check rate limit
        if not self._check_rate_limit(call.session_id or "default"):
            return InterceptResult(
                action=InterceptAction.BLOCK,
                original_call=self._call_to_dict(call),
                reason="Rate limit exceeded",
                latency_ms=int((time.time() - start_time) * 1000),
            )
        
        # Run validators
        for validator in self._validators:
            try:
                is_valid, reason = validator(call)
                if not is_valid:
                    result = InterceptResult(
                        action=InterceptAction.BLOCK,
                        original_call=self._call_to_dict(call),
                        reason=reason,
                        latency_ms=int((time.time() - start_time) * 1000),
                    )
                    self._log_audit(result)
                    return result
            except Exception as e:
                logger.error(f"Validator error: {e}")
        
        # Calculate risk score
        risk_score = self._calculate_risk(call)
        
        # Apply modifiers
        modified_call = call
        for modifier in self._modifiers:
            try:
                modified_call = modifier(modified_call)
            except Exception as e:
                logger.error(f"Modifier error: {e}")
        
        # Determine action based on risk score
        if risk_score >= 0.8:
            action = InterceptAction.BLOCK
            reason = f"High risk score: {risk_score:.2f}"
        elif risk_score >= 0.5:
            action = InterceptAction.AUDIT
            reason = f"Medium risk score: {risk_score:.2f}"
        elif modified_call != call:
            action = InterceptAction.MODIFY
            reason = "Arguments modified for safety"
        else:
            action = InterceptAction.ALLOW
            reason = None
        
        result = InterceptResult(
            action=action,
            original_call=self._call_to_dict(call),
            modified_call=self._call_to_dict(modified_call) if modified_call != call else None,
            reason=reason,
            risk_score=risk_score,
            latency_ms=int((time.time() - start_time) * 1000),
            metadata={
                "agent_id": call.agent_id,
                "session_id": call.session_id,
            },
        )
        
        self._log_audit(result)
        return result
    
    def _validate_tool_allowed(self, call: ToolCall) -> tuple[bool, str]:
        """Validate tool is allowed."""
        if call.tool_name in self.blocked_tools:
            return False, f"Tool '{call.tool_name}' is blocked"
        
        if self.allowed_tools and call.tool_name not in self.allowed_tools:
            return False, f"Tool '{call.tool_name}' is not in allowed list"
        
        return True, ""
    
    def _validate_arguments(self, call: ToolCall) -> tuple[bool, str]:
        """Validate tool arguments."""
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            "rm -rf",
            "sudo",
            "; rm ",
            "| rm ",
            "DROP TABLE",
            "DELETE FROM",
            "<script>",
            "javascript:",
        ]
        
        args_str = str(call.arguments).lower()
        
        for pattern in dangerous_patterns:
            if pattern.lower() in args_str:
                return False, f"Dangerous pattern detected: {pattern}"
        
        return True, ""
    
    def _default_risk_scorer(self, call: ToolCall) -> float:
        """Default risk scoring."""
        risk = 0.0
        
        # High-risk tool categories
        high_risk_tools = [
            "execute", "eval", "shell", "command", "run",
            "delete", "remove", "drop", "truncate",
            "write", "modify", "update",
        ]
        
        medium_risk_tools = [
            "read", "get", "fetch", "query", "search",
            "list", "browse", "access",
        ]
        
        tool_lower = call.tool_name.lower()
        
        for pattern in high_risk_tools:
            if pattern in tool_lower:
                risk += 0.4
                break
        
        for pattern in medium_risk_tools:
            if pattern in tool_lower:
                risk += 0.2
                break
        
        # Risk from argument complexity
        args_str = str(call.arguments)
        if len(args_str) > 1000:
            risk += 0.2
        
        # Risk from special characters
        special_chars = set(";&|`$(){}[]<>")
        if any(c in args_str for c in special_chars):
            risk += 0.2
        
        return min(risk, 1.0)
    
    def _calculate_risk(self, call: ToolCall) -> float:
        """Calculate combined risk score."""
        if not self._risk_scorers:
            return 0.0
        
        scores = []
        for scorer in self._risk_scorers:
            try:
                score = scorer(call)
                scores.append(score)
            except Exception as e:
                logger.error(f"Risk scorer error: {e}")
        
        return max(scores) if scores else 0.0
    
    def _check_rate_limit(self, session_id: str) -> bool:
        """Check if rate limit is exceeded."""
        now = time.time()
        window_start = now - 60
        
        if session_id not in self._call_timestamps:
            self._call_timestamps[session_id] = []
        
        # Remove old timestamps
        self._call_timestamps[session_id] = [
            ts for ts in self._call_timestamps[session_id]
            if ts > window_start
        ]
        
        # Check limit
        if len(self._call_timestamps[session_id]) >= self.rate_limit:
            return False
        
        # Record this call
        self._call_timestamps[session_id].append(now)
        return True
    
    def _call_to_dict(self, call: ToolCall) -> dict[str, Any]:
        """Convert tool call to dict."""
        return {
            "tool_name": call.tool_name,
            "arguments": call.arguments,
            "session_id": call.session_id,
            "agent_id": call.agent_id,
        }
    
    def _log_audit(self, result: InterceptResult) -> None:
        """Log result to audit log."""
        if self.enable_audit:
            self._audit_log.append(result)
            
            # Keep audit log bounded
            if len(self._audit_log) > 10000:
                self._audit_log = self._audit_log[-5000:]
    
    def get_audit_log(
        self,
        session_id: Optional[str] = None,
        action: Optional[InterceptAction] = None,
        since: Optional[str] = None,
    ) -> list[InterceptResult]:
        """Get audit log entries."""
        results = self._audit_log
        
        if session_id:
            results = [
                r for r in results
                if r.metadata.get("session_id") == session_id
            ]
        
        if action:
            results = [r for r in results if r.action == action]
        
        if since:
            results = [r for r in results if r.timestamp >= since]
        
        return results
    
    def get_statistics(self) -> dict[str, Any]:
        """Get interceptor statistics."""
        total = len(self._audit_log)
        
        if total == 0:
            return {
                "total_calls": 0,
                "blocked": 0,
                "allowed": 0,
                "modified": 0,
                "block_rate": 0.0,
            }
        
        action_counts = {
            InterceptAction.ALLOW: 0,
            InterceptAction.BLOCK: 0,
            InterceptAction.MODIFY: 0,
            InterceptAction.AUDIT: 0,
        }
        
        for result in self._audit_log:
            action_counts[result.action] += 1
        
        return {
            "total_calls": total,
            "blocked": action_counts[InterceptAction.BLOCK],
            "allowed": action_counts[InterceptAction.ALLOW],
            "modified": action_counts[InterceptAction.MODIFY],
            "audited": action_counts[InterceptAction.AUDIT],
            "block_rate": action_counts[InterceptAction.BLOCK] / total,
            "avg_risk_score": sum(r.risk_score for r in self._audit_log) / total,
        }


class MCPProxy:
    """
    MCP Proxy server for intercepting agent tool calls.
    
    Acts as a man-in-the-middle between agent and tool providers.
    """
    
    def __init__(
        self,
        interceptor: MCPInterceptor,
        upstream_url: str,
    ) -> None:
        self.interceptor = interceptor
        self.upstream_url = upstream_url
    
    async def handle_request(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle an MCP request."""
        method = request.get("method", "")
        
        if method == "tools/call":
            return await self._handle_tool_call(request)
        else:
            # Pass through non-tool-call requests
            return await self._forward_request(request)
    
    async def _handle_tool_call(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """Handle a tool call request."""
        params = request.get("params", {})
        
        call = ToolCall(
            tool_name=params.get("name", ""),
            arguments=params.get("arguments", {}),
            session_id=request.get("session_id"),
        )
        
        result = await self.interceptor.intercept(call)
        
        if result.action == InterceptAction.BLOCK:
            return {
                "error": {
                    "code": -32600,
                    "message": f"Tool call blocked: {result.reason}",
                }
            }
        
        # Use modified call if available
        if result.action == InterceptAction.MODIFY and result.modified_call:
            request["params"]["arguments"] = result.modified_call["arguments"]
        
        # Forward to upstream
        return await self._forward_request(request)
    
    async def _forward_request(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """Forward request to upstream server."""
        # In real implementation, would use httpx or aiohttp
        # to forward the request
        raise NotImplementedError("Upstream forwarding not implemented")
