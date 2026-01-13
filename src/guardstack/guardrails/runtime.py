"""
Guardrails Runtime for GuardStack.

Core runtime for applying guardrails to AI model inference,
coordinating filters, policies, and logging.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
import asyncio
import time
from datetime import datetime
import logging
import hashlib
import json


logger = logging.getLogger(__name__)


class GuardrailAction(Enum):
    """Actions a guardrail can take."""
    
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    WARN = "warn"
    REVIEW = "review"
    LOG = "log"


@dataclass
class GuardrailResult:
    """Result from a guardrail check."""
    
    action: GuardrailAction
    passed: bool
    original_content: str
    modified_content: Optional[str] = None
    guardrail_name: str = ""
    confidence: float = 1.0
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "action": self.action.value,
            "passed": self.passed,
            "original_content": self.original_content[:100] + "..." if len(self.original_content) > 100 else self.original_content,
            "modified_content": (self.modified_content[:100] + "..." if self.modified_content and len(self.modified_content) > 100 else self.modified_content),
            "guardrail_name": self.guardrail_name,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class GuardrailCheckpoint:
    """Checkpoint in the guardrail pipeline."""
    
    name: str
    position: str  # "input", "output", "both"
    enabled: bool = True
    fail_open: bool = False  # If True, allow on error
    timeout_ms: float = 5000.0
    
    async def check(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> GuardrailResult:
        """Run the checkpoint check. Override in subclasses."""
        raise NotImplementedError


class GuardrailsRuntime:
    """
    Core runtime for applying guardrails to AI inference.
    
    Coordinates multiple guardrail checkpoints, handles failures,
    and provides logging and metrics.
    """
    
    def __init__(
        self,
        checkpoints: Optional[List[GuardrailCheckpoint]] = None,
        default_action: GuardrailAction = GuardrailAction.ALLOW,
        fail_open: bool = False,
        enable_logging: bool = True,
        enable_metrics: bool = True,
    ):
        self.input_checkpoints: List[GuardrailCheckpoint] = []
        self.output_checkpoints: List[GuardrailCheckpoint] = []
        
        if checkpoints:
            for cp in checkpoints:
                self.add_checkpoint(cp)
        
        self.default_action = default_action
        self.fail_open = fail_open
        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics
        
        # Metrics tracking
        self._metrics = {
            "total_checks": 0,
            "passed": 0,
            "blocked": 0,
            "modified": 0,
            "errors": 0,
            "avg_latency_ms": 0.0,
            "checkpoints": {},
        }
        
        # Callbacks
        self._on_block_callbacks: List[Callable[[GuardrailResult], None]] = []
        self._on_modify_callbacks: List[Callable[[GuardrailResult], None]] = []
    
    def add_checkpoint(self, checkpoint: GuardrailCheckpoint) -> None:
        """Add a checkpoint to the pipeline."""
        if checkpoint.position in ("input", "both"):
            self.input_checkpoints.append(checkpoint)
        if checkpoint.position in ("output", "both"):
            self.output_checkpoints.append(checkpoint)
    
    def remove_checkpoint(self, name: str) -> bool:
        """Remove a checkpoint by name."""
        removed = False
        self.input_checkpoints = [cp for cp in self.input_checkpoints if cp.name != name]
        self.output_checkpoints = [cp for cp in self.output_checkpoints if cp.name != name]
        return removed
    
    async def check_input(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardrailResult:
        """
        Run input guardrails on content before model inference.
        
        Args:
            content: Input content (prompt, query, etc.)
            context: Optional context (user info, session, etc.)
            
        Returns:
            GuardrailResult with action and any modifications
        """
        return await self._run_checkpoints(
            content,
            self.input_checkpoints,
            context or {},
            "input",
        )
    
    async def check_output(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardrailResult:
        """
        Run output guardrails on model response.
        
        Args:
            content: Output content (response, completion, etc.)
            context: Optional context (original prompt, etc.)
            
        Returns:
            GuardrailResult with action and any modifications
        """
        return await self._run_checkpoints(
            content,
            self.output_checkpoints,
            context or {},
            "output",
        )
    
    async def check_both(
        self,
        input_content: str,
        model_fn: Callable[[str], Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run both input and output guardrails around model inference.
        
        Args:
            input_content: Input content
            model_fn: Async function to call model
            context: Optional context
            
        Returns:
            Dictionary with input_result, output_result, and final content
        """
        context = context or {}
        
        # Check input
        input_result = await self.check_input(input_content, context)
        
        if not input_result.passed:
            return {
                "input_result": input_result,
                "output_result": None,
                "final_content": None,
                "blocked_at": "input",
            }
        
        # Use modified content if available
        processed_input = input_result.modified_content or input_content
        
        # Call model
        try:
            model_output = await model_fn(processed_input)
        except Exception as e:
            logger.error(f"Model inference failed: {e}")
            return {
                "input_result": input_result,
                "output_result": None,
                "final_content": None,
                "error": str(e),
            }
        
        # Check output
        context["original_input"] = input_content
        context["processed_input"] = processed_input
        output_result = await self.check_output(str(model_output), context)
        
        return {
            "input_result": input_result,
            "output_result": output_result,
            "final_content": output_result.modified_content or model_output if output_result.passed else None,
            "blocked_at": "output" if not output_result.passed else None,
        }
    
    async def _run_checkpoints(
        self,
        content: str,
        checkpoints: List[GuardrailCheckpoint],
        context: Dict[str, Any],
        phase: str,
    ) -> GuardrailResult:
        """Run a list of checkpoints sequentially."""
        start_time = time.time()
        current_content = content
        all_reasons = []
        all_metadata = {}
        
        self._metrics["total_checks"] += 1
        
        for checkpoint in checkpoints:
            if not checkpoint.enabled:
                continue
            
            cp_start = time.time()
            try:
                result = await asyncio.wait_for(
                    checkpoint.check(current_content, context),
                    timeout=checkpoint.timeout_ms / 1000.0,
                )
                
                # Track checkpoint metrics
                cp_latency = (time.time() - cp_start) * 1000
                self._track_checkpoint_metrics(checkpoint.name, result, cp_latency)
                
                # Handle result
                if result.action == GuardrailAction.BLOCK:
                    self._metrics["blocked"] += 1
                    result.processing_time_ms = (time.time() - start_time) * 1000
                    
                    if self.enable_logging:
                        logger.warning(
                            f"Guardrail {checkpoint.name} blocked {phase}: {result.reasons}"
                        )
                    
                    self._notify_block(result)
                    return result
                
                elif result.action == GuardrailAction.MODIFY:
                    self._metrics["modified"] += 1
                    current_content = result.modified_content or current_content
                    all_reasons.extend(result.reasons)
                    all_metadata[checkpoint.name] = result.metadata
                    
                    self._notify_modify(result)
                
                elif result.action == GuardrailAction.WARN:
                    all_reasons.extend(result.reasons)
                    all_metadata[checkpoint.name] = {"warning": result.reasons}
                    
                    if self.enable_logging:
                        logger.warning(
                            f"Guardrail {checkpoint.name} warning on {phase}: {result.reasons}"
                        )
                
            except asyncio.TimeoutError:
                self._metrics["errors"] += 1
                logger.error(f"Checkpoint {checkpoint.name} timed out")
                
                if not checkpoint.fail_open and not self.fail_open:
                    return GuardrailResult(
                        action=GuardrailAction.BLOCK,
                        passed=False,
                        original_content=content,
                        guardrail_name=checkpoint.name,
                        reasons=[f"Checkpoint {checkpoint.name} timed out"],
                        processing_time_ms=(time.time() - start_time) * 1000,
                    )
            
            except Exception as e:
                self._metrics["errors"] += 1
                logger.error(f"Checkpoint {checkpoint.name} error: {e}")
                
                if not checkpoint.fail_open and not self.fail_open:
                    return GuardrailResult(
                        action=GuardrailAction.BLOCK,
                        passed=False,
                        original_content=content,
                        guardrail_name=checkpoint.name,
                        reasons=[f"Checkpoint {checkpoint.name} error: {str(e)}"],
                        processing_time_ms=(time.time() - start_time) * 1000,
                    )
        
        # All checkpoints passed
        self._metrics["passed"] += 1
        processing_time = (time.time() - start_time) * 1000
        self._update_avg_latency(processing_time)
        
        return GuardrailResult(
            action=GuardrailAction.ALLOW if current_content == content else GuardrailAction.MODIFY,
            passed=True,
            original_content=content,
            modified_content=current_content if current_content != content else None,
            guardrail_name="pipeline",
            reasons=all_reasons,
            metadata=all_metadata,
            processing_time_ms=processing_time,
        )
    
    def _track_checkpoint_metrics(
        self,
        name: str,
        result: GuardrailResult,
        latency_ms: float,
    ) -> None:
        """Track metrics for a checkpoint."""
        if name not in self._metrics["checkpoints"]:
            self._metrics["checkpoints"][name] = {
                "total": 0,
                "passed": 0,
                "blocked": 0,
                "avg_latency_ms": 0.0,
            }
        
        cp_metrics = self._metrics["checkpoints"][name]
        cp_metrics["total"] += 1
        
        if result.passed:
            cp_metrics["passed"] += 1
        else:
            cp_metrics["blocked"] += 1
        
        # Update running average
        cp_metrics["avg_latency_ms"] = (
            (cp_metrics["avg_latency_ms"] * (cp_metrics["total"] - 1) + latency_ms)
            / cp_metrics["total"]
        )
    
    def _update_avg_latency(self, latency_ms: float) -> None:
        """Update overall average latency."""
        total = self._metrics["total_checks"]
        self._metrics["avg_latency_ms"] = (
            (self._metrics["avg_latency_ms"] * (total - 1) + latency_ms) / total
        )
    
    def _notify_block(self, result: GuardrailResult) -> None:
        """Notify block callbacks."""
        for callback in self._on_block_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Block callback error: {e}")
    
    def _notify_modify(self, result: GuardrailResult) -> None:
        """Notify modify callbacks."""
        for callback in self._on_modify_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Modify callback error: {e}")
    
    def on_block(self, callback: Callable[[GuardrailResult], None]) -> None:
        """Register a callback for block events."""
        self._on_block_callbacks.append(callback)
    
    def on_modify(self, callback: Callable[[GuardrailResult], None]) -> None:
        """Register a callback for modify events."""
        self._on_modify_callbacks.append(callback)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            **self._metrics,
            "pass_rate": self._metrics["passed"] / max(self._metrics["total_checks"], 1),
            "block_rate": self._metrics["blocked"] / max(self._metrics["total_checks"], 1),
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = {
            "total_checks": 0,
            "passed": 0,
            "blocked": 0,
            "modified": 0,
            "errors": 0,
            "avg_latency_ms": 0.0,
            "checkpoints": {},
        }
    
    def list_checkpoints(self) -> Dict[str, List[str]]:
        """List all configured checkpoints."""
        return {
            "input": [cp.name for cp in self.input_checkpoints],
            "output": [cp.name for cp in self.output_checkpoints],
        }
    
    def enable_checkpoint(self, name: str) -> bool:
        """Enable a checkpoint by name."""
        enabled = False
        for cp in self.input_checkpoints + self.output_checkpoints:
            if cp.name == name:
                cp.enabled = True
                enabled = True
        return enabled
    
    def disable_checkpoint(self, name: str) -> bool:
        """Disable a checkpoint by name."""
        disabled = False
        for cp in self.input_checkpoints + self.output_checkpoints:
            if cp.name == name:
                cp.enabled = False
                disabled = True
        return disabled


class SimpleCheckpoint(GuardrailCheckpoint):
    """Simple checkpoint using a callable check function."""
    
    def __init__(
        self,
        name: str,
        position: str,
        check_fn: Callable[[str, Dict[str, Any]], GuardrailResult],
        enabled: bool = True,
        fail_open: bool = False,
        timeout_ms: float = 5000.0,
    ):
        super().__init__(name, position, enabled, fail_open, timeout_ms)
        self.check_fn = check_fn
    
    async def check(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> GuardrailResult:
        """Run the check function."""
        if asyncio.iscoroutinefunction(self.check_fn):
            return await self.check_fn(content, context)
        return self.check_fn(content, context)


class CachingGuardrailsRuntime(GuardrailsRuntime):
    """Guardrails runtime with caching for identical checks."""
    
    def __init__(
        self,
        *args,
        cache_ttl_seconds: int = 300,
        max_cache_size: int = 10000,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.cache_ttl = cache_ttl_seconds
        self.max_cache_size = max_cache_size
        self._cache: Dict[str, tuple[GuardrailResult, float]] = {}
    
    def _get_cache_key(
        self,
        content: str,
        checkpoints: List[str],
    ) -> str:
        """Generate cache key for content and checkpoint configuration."""
        key_data = {
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "checkpoints": sorted(checkpoints),
        }
        return hashlib.sha256(json.dumps(key_data).encode()).hexdigest()
    
    async def check_input(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardrailResult:
        """Check input with caching."""
        checkpoint_names = [cp.name for cp in self.input_checkpoints if cp.enabled]
        cache_key = self._get_cache_key(content, checkpoint_names)
        
        # Check cache
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                del self._cache[cache_key]
        
        # Run checkpoints
        result = await super().check_input(content, context)
        
        # Cache result
        if len(self._cache) >= self.max_cache_size:
            # Evict oldest entries
            oldest_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k][1],
            )[:len(self._cache) // 10]
            for key in oldest_keys:
                del self._cache[key]
        
        self._cache[cache_key] = (result, time.time())
        return result
    
    def clear_cache(self) -> None:
        """Clear the result cache."""
        self._cache.clear()
