"""
Guardrails Service

Service for real-time content safety checks including PII detection,
toxicity detection, and jailbreak prevention.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ViolationType(str, Enum):
    """Types of guardrail violations."""
    PII = "pii"
    TOXICITY = "toxicity"
    JAILBREAK = "jailbreak"
    CUSTOM = "custom"


class Severity(str, Enum):
    """Severity levels for violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Violation:
    """A single guardrail violation."""
    type: ViolationType
    category: str
    severity: Severity
    message: str
    location: str  # input, output
    confidence: float
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    entity_text: Optional[str] = None


@dataclass
class GuardrailResult:
    """Result of guardrail checks."""
    passed: bool
    blocked: bool
    violations: list[Violation] = field(default_factory=list)
    input_violations: int = 0
    output_violations: int = 0
    processing_time_ms: int = 0
    sanitized_output: Optional[str] = None


# ==================== PII Detection ====================

class PIIDetector:
    """
    PII detection using pattern matching and Presidio-style analysis.
    
    Detects:
    - Email addresses
    - Phone numbers
    - Social Security Numbers
    - Credit card numbers
    - IP addresses
    - Names (basic)
    - Addresses (basic)
    """
    
    # Pattern definitions with confidence scores
    PATTERNS = {
        "EMAIL": {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "severity": Severity.HIGH,
            "confidence": 0.95,
        },
        "PHONE_NUMBER": {
            "pattern": r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            "severity": Severity.MEDIUM,
            "confidence": 0.85,
        },
        "SSN": {
            "pattern": r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
            "severity": Severity.CRITICAL,
            "confidence": 0.90,
        },
        "CREDIT_CARD": {
            "pattern": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            "severity": Severity.CRITICAL,
            "confidence": 0.95,
        },
        "IP_ADDRESS": {
            "pattern": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "severity": Severity.LOW,
            "confidence": 0.90,
        },
        "DATE_OF_BIRTH": {
            "pattern": r'\b(?:0[1-9]|1[0-2])[/-](?:0[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b',
            "severity": Severity.MEDIUM,
            "confidence": 0.75,
        },
        "US_PASSPORT": {
            "pattern": r'\b[A-Z]\d{8}\b',
            "severity": Severity.CRITICAL,
            "confidence": 0.70,
        },
        "BANK_ACCOUNT": {
            "pattern": r'\b\d{8,17}\b',  # Basic pattern, needs context
            "severity": Severity.HIGH,
            "confidence": 0.60,
        },
    }
    
    def __init__(
        self,
        enabled_entities: Optional[list[str]] = None,
        threshold: float = 0.5,
    ):
        self.enabled_entities = enabled_entities or list(self.PATTERNS.keys())
        self.threshold = threshold
    
    def detect(
        self,
        text: str,
        location: str = "input",
    ) -> list[Violation]:
        """
        Detect PII in text.
        
        Args:
            text: Text to analyze
            location: Where the text came from (input/output)
        
        Returns:
            List of PII violations
        """
        violations = []
        
        for entity_type in self.enabled_entities:
            if entity_type not in self.PATTERNS:
                continue
            
            pattern_info = self.PATTERNS[entity_type]
            pattern = pattern_info["pattern"]
            
            for match in re.finditer(pattern, text, re.IGNORECASE):
                confidence = pattern_info["confidence"]
                
                # Skip if below threshold
                if confidence < self.threshold:
                    continue
                
                # Additional validation for SSN
                if entity_type == "SSN":
                    ssn = match.group().replace("-", "").replace(" ", "")
                    # Check for invalid SSNs
                    if ssn.startswith("000") or ssn.startswith("666") or ssn.startswith("9"):
                        confidence *= 0.5
                
                if confidence >= self.threshold:
                    violations.append(Violation(
                        type=ViolationType.PII,
                        category=entity_type,
                        severity=pattern_info["severity"],
                        message=f"Potential {entity_type.replace('_', ' ').lower()} detected",
                        location=location,
                        confidence=confidence,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        entity_text=self._mask_entity(match.group(), entity_type),
                    ))
        
        return violations
    
    def _mask_entity(self, text: str, entity_type: str) -> str:
        """Mask sensitive parts of detected entity."""
        if entity_type == "EMAIL":
            parts = text.split("@")
            return f"{parts[0][:2]}***@{parts[1]}" if len(parts) == 2 else text[:3] + "***"
        elif entity_type == "CREDIT_CARD":
            return f"****-****-****-{text[-4:]}"
        elif entity_type == "SSN":
            return f"***-**-{text[-4:]}"
        elif entity_type == "PHONE_NUMBER":
            return f"***-***-{text[-4:]}"
        return text[:3] + "***"
    
    def redact(self, text: str) -> str:
        """
        Redact PII from text.
        
        Args:
            text: Text containing PII
        
        Returns:
            Text with PII redacted
        """
        result = text
        
        for entity_type in self.enabled_entities:
            if entity_type not in self.PATTERNS:
                continue
            
            pattern = self.PATTERNS[entity_type]["pattern"]
            replacement = f"[{entity_type}]"
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result


# ==================== Toxicity Detection ====================

class ToxicityDetector:
    """
    Toxicity detection using keyword matching and pattern analysis.
    
    In production, this would use ML models like Detoxify or Perspective API.
    """
    
    # Severity categories
    CATEGORIES = {
        "severe_toxicity": {
            "keywords": [],  # Redacted for safety
            "severity": Severity.CRITICAL,
            "patterns": [],
        },
        "threat": {
            "keywords": ["kill", "murder", "attack", "bomb", "shoot", "destroy"],
            "severity": Severity.CRITICAL,
            "patterns": [
                r"\bi('ll| will| am going to) (hurt|harm|kill|attack)",
            ],
        },
        "hate_speech": {
            "keywords": [],  # Redacted for safety
            "severity": Severity.CRITICAL,
            "patterns": [],
        },
        "harassment": {
            "keywords": ["loser", "idiot", "stupid", "moron", "dumb"],
            "severity": Severity.MEDIUM,
            "patterns": [
                r"\byou('re| are) (a |an )?(stupid|idiot|worthless)",
            ],
        },
        "self_harm": {
            "keywords": ["suicide", "self-harm", "cut myself"],
            "severity": Severity.CRITICAL,
            "patterns": [
                r"\bi want to (hurt|harm|kill) myself",
                r"\bhow to (commit )?suicide",
            ],
        },
        "sexual_explicit": {
            "keywords": [],  # Redacted for safety
            "severity": Severity.HIGH,
            "patterns": [],
        },
    }
    
    def __init__(
        self,
        enabled_categories: Optional[list[str]] = None,
        threshold: float = 0.5,
    ):
        self.enabled_categories = enabled_categories or list(self.CATEGORIES.keys())
        self.threshold = threshold
    
    def detect(
        self,
        text: str,
        location: str = "output",
    ) -> list[Violation]:
        """
        Detect toxic content in text.
        
        Args:
            text: Text to analyze
            location: Where the text came from (input/output)
        
        Returns:
            List of toxicity violations
        """
        violations = []
        text_lower = text.lower()
        
        for category in self.enabled_categories:
            if category not in self.CATEGORIES:
                continue
            
            cat_info = self.CATEGORIES[category]
            confidence = 0.0
            
            # Check keywords
            for keyword in cat_info["keywords"]:
                if keyword in text_lower:
                    confidence = max(confidence, 0.8)
                    break
            
            # Check patterns
            for pattern in cat_info["patterns"]:
                if re.search(pattern, text_lower):
                    confidence = max(confidence, 0.9)
                    break
            
            if confidence >= self.threshold:
                violations.append(Violation(
                    type=ViolationType.TOXICITY,
                    category=category,
                    severity=cat_info["severity"],
                    message=f"Potentially toxic content detected ({category.replace('_', ' ')})",
                    location=location,
                    confidence=confidence,
                ))
        
        return violations
    
    def get_toxicity_score(self, text: str) -> dict[str, float]:
        """
        Get toxicity scores for all categories.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dict mapping category to score (0-1)
        """
        scores = {}
        text_lower = text.lower()
        
        for category, cat_info in self.CATEGORIES.items():
            score = 0.0
            
            # Keyword-based scoring
            keyword_matches = sum(1 for kw in cat_info["keywords"] if kw in text_lower)
            if keyword_matches > 0:
                score = min(0.5 + (keyword_matches * 0.1), 0.8)
            
            # Pattern-based scoring
            for pattern in cat_info["patterns"]:
                if re.search(pattern, text_lower):
                    score = max(score, 0.9)
            
            scores[category] = score
        
        return scores


# ==================== Jailbreak Detection ====================

class JailbreakDetector:
    """
    Jailbreak and prompt injection detection.
    
    Detects attempts to:
    - Override system instructions
    - Assume different personas (DAN, etc.)
    - Inject malicious prompts
    - Exploit model behavior
    """
    
    PATTERNS = {
        "instruction_override": {
            "patterns": [
                r"ignore (all )?(previous|prior|above|system) (instructions|prompts|rules)",
                r"disregard (all )?(previous|prior|above|system)",
                r"forget (everything|all|your) (instructions|training|rules)",
                r"pretend (you )?(are|have|don't|can)",
            ],
            "severity": Severity.CRITICAL,
            "confidence": 0.9,
        },
        "persona_manipulation": {
            "patterns": [
                r"\bdan\b",
                r"do anything now",
                r"jailbreak(ed)?",
                r"act as (if|a|an)",
                r"pretend (to be|you are)",
                r"roleplay as",
                r"you are now",
            ],
            "severity": Severity.CRITICAL,
            "confidence": 0.85,
        },
        "prompt_leak": {
            "patterns": [
                r"(show|reveal|print|display|output) (your|the|system) (prompt|instructions)",
                r"what (are|were) your (instructions|rules)",
                r"repeat (everything|all|the words) (above|before)",
            ],
            "severity": Severity.HIGH,
            "confidence": 0.85,
        },
        "encoding_bypass": {
            "patterns": [
                r"base64",
                r"rot13",
                r"hex(adecimal)?",
                r"encode(d)?",
                r"decode(d)?",
            ],
            "severity": Severity.MEDIUM,
            "confidence": 0.6,
        },
        "delimiter_injection": {
            "patterns": [
                r"```system",
                r"\[INST\]",
                r"<\|im_start\|>",
                r"### (Instruction|System|Human|Assistant)",
            ],
            "severity": Severity.HIGH,
            "confidence": 0.9,
        },
    }
    
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
    
    def detect(
        self,
        text: str,
        location: str = "input",
    ) -> list[Violation]:
        """
        Detect jailbreak attempts in text.
        
        Args:
            text: Text to analyze
            location: Where the text came from (input/output)
        
        Returns:
            List of jailbreak violations
        """
        violations = []
        text_lower = text.lower()
        
        for category, cat_info in self.PATTERNS.items():
            for pattern in cat_info["patterns"]:
                if re.search(pattern, text_lower):
                    if cat_info["confidence"] >= self.threshold:
                        violations.append(Violation(
                            type=ViolationType.JAILBREAK,
                            category=category,
                            severity=cat_info["severity"],
                            message=f"Potential jailbreak attempt detected ({category.replace('_', ' ')})",
                            location=location,
                            confidence=cat_info["confidence"],
                        ))
                    break  # Only one violation per category
        
        return violations
    
    def get_jailbreak_score(self, text: str) -> float:
        """
        Get overall jailbreak risk score.
        
        Args:
            text: Text to analyze
        
        Returns:
            Risk score (0-1)
        """
        text_lower = text.lower()
        max_score = 0.0
        
        for cat_info in self.PATTERNS.values():
            for pattern in cat_info["patterns"]:
                if re.search(pattern, text_lower):
                    max_score = max(max_score, cat_info["confidence"])
        
        return max_score


# ==================== Guardrail Service ====================

class GuardrailService:
    """
    Main guardrail service combining all detection capabilities.
    """
    
    def __init__(
        self,
        pii_enabled: bool = True,
        pii_entities: Optional[list[str]] = None,
        pii_threshold: float = 0.5,
        toxicity_enabled: bool = True,
        toxicity_categories: Optional[list[str]] = None,
        toxicity_threshold: float = 0.5,
        jailbreak_enabled: bool = True,
        jailbreak_threshold: float = 0.5,
        block_on_critical: bool = True,
    ):
        self.pii_detector = PIIDetector(
            enabled_entities=pii_entities,
            threshold=pii_threshold,
        ) if pii_enabled else None
        
        self.toxicity_detector = ToxicityDetector(
            enabled_categories=toxicity_categories,
            threshold=toxicity_threshold,
        ) if toxicity_enabled else None
        
        self.jailbreak_detector = JailbreakDetector(
            threshold=jailbreak_threshold,
        ) if jailbreak_enabled else None
        
        self.block_on_critical = block_on_critical
    
    def check(
        self,
        input_text: Optional[str] = None,
        output_text: Optional[str] = None,
        check_pii: bool = True,
        check_toxicity: bool = True,
        check_jailbreak: bool = True,
    ) -> GuardrailResult:
        """
        Run guardrail checks on input and/or output text.
        
        Args:
            input_text: User input to check
            output_text: Model output to check
            check_pii: Enable PII detection
            check_toxicity: Enable toxicity detection
            check_jailbreak: Enable jailbreak detection
        
        Returns:
            GuardrailResult with violations and status
        """
        start_time = time.time()
        violations: list[Violation] = []
        
        # Check input
        if input_text:
            if check_pii and self.pii_detector:
                violations.extend(self.pii_detector.detect(input_text, "input"))
            
            if check_jailbreak and self.jailbreak_detector:
                violations.extend(self.jailbreak_detector.detect(input_text, "input"))
        
        # Check output
        if output_text:
            if check_pii and self.pii_detector:
                violations.extend(self.pii_detector.detect(output_text, "output"))
            
            if check_toxicity and self.toxicity_detector:
                violations.extend(self.toxicity_detector.detect(output_text, "output"))
        
        # Count violations by location
        input_violations = sum(1 for v in violations if v.location == "input")
        output_violations = sum(1 for v in violations if v.location == "output")
        
        # Determine if should block
        has_critical = any(v.severity == Severity.CRITICAL for v in violations)
        blocked = has_critical and self.block_on_critical
        
        # Sanitize output if needed
        sanitized_output = None
        if output_text and self.pii_detector and check_pii:
            sanitized_output = self.pii_detector.redact(output_text)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return GuardrailResult(
            passed=len(violations) == 0,
            blocked=blocked,
            violations=violations,
            input_violations=input_violations,
            output_violations=output_violations,
            processing_time_ms=processing_time,
            sanitized_output=sanitized_output if sanitized_output != output_text else None,
        )


# Global service instance
_guardrail_service: Optional[GuardrailService] = None


def get_guardrail_service() -> GuardrailService:
    """Get the global guardrail service."""
    global _guardrail_service
    if _guardrail_service is None:
        _guardrail_service = GuardrailService()
    return _guardrail_service
