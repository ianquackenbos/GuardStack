"""
Content Filters for GuardStack Guardrails.

Provides pre-built filters for common safety checks including
PII detection, toxicity filtering, jailbreak detection, and topic filtering.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set, Pattern
from dataclasses import dataclass, field
import re
import asyncio
import logging

from .runtime import GuardrailCheckpoint, GuardrailResult, GuardrailAction


logger = logging.getLogger(__name__)


class ContentFilter(GuardrailCheckpoint, ABC):
    """Base class for content filters."""
    
    def __init__(
        self,
        name: str,
        position: str = "both",
        enabled: bool = True,
        fail_open: bool = False,
        timeout_ms: float = 5000.0,
        action_on_match: GuardrailAction = GuardrailAction.BLOCK,
    ):
        super().__init__(name, position, enabled, fail_open, timeout_ms)
        self.action_on_match = action_on_match
    
    @abstractmethod
    async def detect(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """
        Detect if content matches filter criteria.
        
        Returns:
            Tuple of (matched, reasons, metadata)
        """
        pass
    
    async def check(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> GuardrailResult:
        """Run the filter check."""
        try:
            matched, reasons, metadata = await self.detect(content, context)
            
            if matched:
                return GuardrailResult(
                    action=self.action_on_match,
                    passed=self.action_on_match not in (GuardrailAction.BLOCK,),
                    original_content=content,
                    guardrail_name=self.name,
                    reasons=reasons,
                    metadata=metadata,
                )
            
            return GuardrailResult(
                action=GuardrailAction.ALLOW,
                passed=True,
                original_content=content,
                guardrail_name=self.name,
            )
            
        except Exception as e:
            logger.error(f"Filter {self.name} error: {e}")
            if self.fail_open:
                return GuardrailResult(
                    action=GuardrailAction.ALLOW,
                    passed=True,
                    original_content=content,
                    guardrail_name=self.name,
                    reasons=[f"Filter error (fail_open): {str(e)}"],
                )
            raise


class PIIFilter(ContentFilter):
    """Filter for detecting and handling Personally Identifiable Information."""
    
    # Common PII patterns
    PII_PATTERNS = {
        "ssn": {
            "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
            "description": "Social Security Number",
        },
        "credit_card": {
            "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "description": "Credit Card Number",
        },
        "email": {
            "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "description": "Email Address",
        },
        "phone_us": {
            "pattern": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "description": "US Phone Number",
        },
        "ip_address": {
            "pattern": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "description": "IP Address",
        },
        "date_of_birth": {
            "pattern": r"\b(?:0[1-9]|1[0-2])[/\-](?:0[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b",
            "description": "Date of Birth",
        },
        "passport": {
            "pattern": r"\b[A-Z]{1,2}\d{6,9}\b",
            "description": "Passport Number",
        },
        "drivers_license": {
            "pattern": r"\b[A-Z]{1,2}\d{5,8}\b",
            "description": "Driver's License",
        },
    }
    
    def __init__(
        self,
        name: str = "pii_filter",
        position: str = "both",
        enabled: bool = True,
        pii_types: Optional[List[str]] = None,
        custom_patterns: Optional[Dict[str, Dict[str, str]]] = None,
        redaction_char: str = "*",
        action_on_match: GuardrailAction = GuardrailAction.MODIFY,
    ):
        super().__init__(name, position, enabled, action_on_match=action_on_match)
        
        # Select which PII types to detect
        self.pii_types = pii_types or list(self.PII_PATTERNS.keys())
        
        # Build patterns
        self.patterns = {}
        for pii_type in self.pii_types:
            if pii_type in self.PII_PATTERNS:
                self.patterns[pii_type] = self.PII_PATTERNS[pii_type]
        
        # Add custom patterns
        if custom_patterns:
            self.patterns.update(custom_patterns)
        
        # Compile patterns
        self.compiled_patterns = {
            pii_type: re.compile(info["pattern"], re.IGNORECASE)
            for pii_type, info in self.patterns.items()
        }
        
        self.redaction_char = redaction_char
    
    async def detect(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """Detect PII in content."""
        detections = {}
        reasons = []
        
        for pii_type, pattern in self.compiled_patterns.items():
            matches = pattern.findall(content)
            if matches:
                detections[pii_type] = {
                    "count": len(matches),
                    "description": self.patterns[pii_type].get("description", pii_type),
                }
                reasons.append(
                    f"Found {len(matches)} {self.patterns[pii_type].get('description', pii_type)}"
                )
        
        return bool(detections), reasons, {"pii_detections": detections}
    
    async def check(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> GuardrailResult:
        """Run PII filter with optional redaction."""
        matched, reasons, metadata = await self.detect(content, context)
        
        if not matched:
            return GuardrailResult(
                action=GuardrailAction.ALLOW,
                passed=True,
                original_content=content,
                guardrail_name=self.name,
            )
        
        # If action is MODIFY, redact PII
        if self.action_on_match == GuardrailAction.MODIFY:
            modified_content = self._redact_pii(content)
            return GuardrailResult(
                action=GuardrailAction.MODIFY,
                passed=True,
                original_content=content,
                modified_content=modified_content,
                guardrail_name=self.name,
                reasons=reasons,
                metadata=metadata,
            )
        
        return GuardrailResult(
            action=self.action_on_match,
            passed=self.action_on_match != GuardrailAction.BLOCK,
            original_content=content,
            guardrail_name=self.name,
            reasons=reasons,
            metadata=metadata,
        )
    
    def _redact_pii(self, content: str) -> str:
        """Redact PII from content."""
        redacted = content
        for pattern in self.compiled_patterns.values():
            redacted = pattern.sub(
                lambda m: self.redaction_char * len(m.group()),
                redacted,
            )
        return redacted


class ToxicityFilter(ContentFilter):
    """Filter for detecting toxic content."""
    
    # Word lists (simplified - in production, use ML models)
    TOXIC_PATTERNS = [
        r"\b(hate|kill|murder|attack)\s+(all|every|those)\s+\w+",
        r"\b(stupid|idiot|moron|dumb)\s+(people|person|users?)\b",
        r"\b(die|death)\s+(to|for)\s+\w+",
    ]
    
    PROFANITY_PATTERNS = [
        # Add profanity patterns as needed
    ]
    
    def __init__(
        self,
        name: str = "toxicity_filter",
        position: str = "output",
        enabled: bool = True,
        toxicity_threshold: float = 0.7,
        use_ml_model: bool = False,
        ml_model_endpoint: Optional[str] = None,
        action_on_match: GuardrailAction = GuardrailAction.BLOCK,
    ):
        super().__init__(name, position, enabled, action_on_match=action_on_match)
        
        self.toxicity_threshold = toxicity_threshold
        self.use_ml_model = use_ml_model
        self.ml_model_endpoint = ml_model_endpoint
        
        # Compile patterns
        self.toxic_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.TOXIC_PATTERNS
        ]
    
    async def detect(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """Detect toxic content."""
        if self.use_ml_model and self.ml_model_endpoint:
            return await self._ml_detect(content)
        return await self._pattern_detect(content)
    
    async def _pattern_detect(
        self,
        content: str,
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """Detect using pattern matching."""
        matches = []
        for pattern in self.toxic_patterns:
            found = pattern.findall(content)
            if found:
                matches.extend(found)
        
        if matches:
            return True, [f"Toxic content detected: {len(matches)} matches"], {
                "pattern_matches": len(matches),
            }
        
        return False, [], {}
    
    async def _ml_detect(
        self,
        content: str,
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """Detect using ML model."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ml_model_endpoint,
                    json={"text": content},
                ) as response:
                    result = await response.json()
                    
                    toxicity_score = result.get("toxicity_score", 0)
                    if toxicity_score >= self.toxicity_threshold:
                        return True, [
                            f"Toxicity score {toxicity_score:.2f} exceeds threshold"
                        ], {
                            "toxicity_score": toxicity_score,
                            "categories": result.get("categories", {}),
                        }
                    
                    return False, [], {"toxicity_score": toxicity_score}
                    
        except Exception as e:
            logger.error(f"ML toxicity detection failed: {e}")
            # Fall back to pattern matching
            return await self._pattern_detect(content)


class JailbreakFilter(ContentFilter):
    """Filter for detecting jailbreak attempts."""
    
    JAILBREAK_PATTERNS = [
        # DAN (Do Anything Now)
        r"\bDAN\b.*mode",
        r"do\s+anything\s+now",
        
        # Ignore instructions
        r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)",
        r"disregard\s+(all\s+)?(previous|prior|above)",
        
        # Role play exploits
        r"pretend\s+(you\s+)?(are|have|can|were)",
        r"act\s+as\s+if\s+(you\s+)?(have|are|can|were)",
        r"imagine\s+(you\s+)?(are|have|can|were)",
        
        # System prompt extraction
        r"(show|reveal|tell|print|display)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions)",
        r"what\s+(is|are)\s+(your|the)\s+(system\s+)?(prompt|instructions)",
        
        # Bypass attempts
        r"bypass\s+(your|the|any)\s+(safety|security|restrictions)",
        r"disable\s+(your|the|any)\s+(safety|security|filters)",
        r"turn\s+off\s+(your|the|any)\s+(safety|security)",
        
        # Encoding exploits
        r"base64\s*[:=]",
        r"decode\s+this",
        r"rot13",
    ]
    
    def __init__(
        self,
        name: str = "jailbreak_filter",
        position: str = "input",
        enabled: bool = True,
        custom_patterns: Optional[List[str]] = None,
        action_on_match: GuardrailAction = GuardrailAction.BLOCK,
    ):
        super().__init__(name, position, enabled, action_on_match=action_on_match)
        
        patterns = self.JAILBREAK_PATTERNS.copy()
        if custom_patterns:
            patterns.extend(custom_patterns)
        
        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in patterns
        ]
    
    async def detect(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """Detect jailbreak attempts."""
        detected_patterns = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(content):
                detected_patterns.append(i)
        
        if detected_patterns:
            return True, [
                f"Potential jailbreak attempt detected ({len(detected_patterns)} patterns)"
            ], {
                "pattern_indices": detected_patterns,
            }
        
        return False, [], {}


class TopicFilter(ContentFilter):
    """Filter for restricting discussion of certain topics."""
    
    def __init__(
        self,
        name: str = "topic_filter",
        position: str = "both",
        enabled: bool = True,
        blocked_topics: Optional[Dict[str, List[str]]] = None,
        allowed_topics: Optional[Dict[str, List[str]]] = None,
        action_on_match: GuardrailAction = GuardrailAction.BLOCK,
    ):
        super().__init__(name, position, enabled, action_on_match=action_on_match)
        
        # Topics to block (topic name -> keywords)
        self.blocked_topics = blocked_topics or {
            "weapons": ["bomb", "explosive", "weapon", "firearm", "gun", "ammunition"],
            "drugs": ["cocaine", "heroin", "meth", "synthesize drugs", "make drugs"],
            "hacking": ["hack into", "exploit vulnerability", "ddos", "malware"],
            "illegal": ["illegal", "crime", "criminal activity", "break the law"],
        }
        
        # Optional allowlist (only allow these topics)
        self.allowed_topics = allowed_topics
        
        # Compile patterns
        self.blocked_patterns = {}
        for topic, keywords in self.blocked_topics.items():
            pattern = r"\b(" + "|".join(re.escape(k) for k in keywords) + r")\b"
            self.blocked_patterns[topic] = re.compile(pattern, re.IGNORECASE)
    
    async def detect(
        self,
        content: str,
        context: Dict[str, Any],
    ) -> tuple[bool, List[str], Dict[str, Any]]:
        """Detect blocked topics."""
        detected_topics = []
        
        for topic, pattern in self.blocked_patterns.items():
            if pattern.search(content):
                detected_topics.append(topic)
        
        if detected_topics:
            return True, [
                f"Blocked topic(s) detected: {', '.join(detected_topics)}"
            ], {
                "blocked_topics": detected_topics,
            }
        
        return False, [], {}


class FilterChain:
    """Chain multiple filters together."""
    
    def __init__(
        self,
        filters: Optional[List[ContentFilter]] = None,
        stop_on_block: bool = True,
    ):
        self.filters = filters or []
        self.stop_on_block = stop_on_block
    
    def add_filter(self, filter_: ContentFilter) -> None:
        """Add a filter to the chain."""
        self.filters.append(filter_)
    
    def remove_filter(self, name: str) -> Optional[ContentFilter]:
        """Remove a filter by name."""
        for i, f in enumerate(self.filters):
            if f.name == name:
                return self.filters.pop(i)
        return None
    
    async def run(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[GuardrailResult]:
        """Run all filters on content."""
        context = context or {}
        results = []
        current_content = content
        
        for filter_ in self.filters:
            if not filter_.enabled:
                continue
            
            try:
                result = await filter_.check(current_content, context)
                results.append(result)
                
                if result.action == GuardrailAction.BLOCK and self.stop_on_block:
                    break
                
                if result.modified_content:
                    current_content = result.modified_content
                    
            except asyncio.TimeoutError:
                logger.error(f"Filter {filter_.name} timed out")
                if not filter_.fail_open:
                    results.append(GuardrailResult(
                        action=GuardrailAction.BLOCK,
                        passed=False,
                        original_content=content,
                        guardrail_name=filter_.name,
                        reasons=["Filter timed out"],
                    ))
                    if self.stop_on_block:
                        break
                        
            except Exception as e:
                logger.error(f"Filter {filter_.name} error: {e}")
                if not filter_.fail_open:
                    results.append(GuardrailResult(
                        action=GuardrailAction.BLOCK,
                        passed=False,
                        original_content=content,
                        guardrail_name=filter_.name,
                        reasons=[f"Filter error: {str(e)}"],
                    ))
                    if self.stop_on_block:
                        break
        
        return results
    
    async def run_parallel(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[GuardrailResult]:
        """Run all filters in parallel."""
        context = context or {}
        
        tasks = [
            filter_.check(content, context)
            for filter_ in self.filters
            if filter_.enabled
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to block results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                filter_ = [f for f in self.filters if f.enabled][i]
                if not filter_.fail_open:
                    final_results.append(GuardrailResult(
                        action=GuardrailAction.BLOCK,
                        passed=False,
                        original_content=content,
                        guardrail_name=filter_.name,
                        reasons=[f"Filter error: {str(result)}"],
                    ))
            else:
                final_results.append(result)
        
        return final_results
    
    def get_summary(self, results: List[GuardrailResult]) -> Dict[str, Any]:
        """Get summary of filter results."""
        blocked = [r for r in results if r.action == GuardrailAction.BLOCK]
        modified = [r for r in results if r.action == GuardrailAction.MODIFY]
        warnings = [r for r in results if r.action == GuardrailAction.WARN]
        
        return {
            "total_filters": len(self.filters),
            "filters_run": len(results),
            "blocked": len(blocked),
            "modified": len(modified),
            "warnings": len(warnings),
            "passed": len(blocked) == 0,
            "block_reasons": [r.reasons for r in blocked],
        }


# Factory function for creating default filter chain
def create_default_filter_chain() -> FilterChain:
    """Create a default filter chain with common filters."""
    return FilterChain(
        filters=[
            JailbreakFilter(position="input"),
            PIIFilter(position="both", action_on_match=GuardrailAction.MODIFY),
            TopicFilter(position="both"),
            ToxicityFilter(position="output"),
        ],
        stop_on_block=True,
    )
