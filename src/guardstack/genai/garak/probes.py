"""
Garak Probes

Configuration for Garak red-teaming probes.
"""

from typing import Any


# Probe categories and their associated probes
PROBE_CATEGORIES: dict[str, list[str]] = {
    "prompt_injection": [
        "promptinject.HijackHateHumansMini",
        "promptinject.HijackKillHumansMini",
        "promptinject.HijackLongPromptMini",
    ],
    "jailbreaking": [
        "dan.Dan_11_0",
        "dan.Dan_10_0",
        "dan.Dan_9_0",
        "dan.Dan_8_0",
        "dan.Dan_7_0",
        "dan.Dan_6_2",
        "dan.Dan_6_0",
        "dan.STAN",
        "dan.DUDE",
    ],
    "encoding": [
        "encoding.InjectBase64",
        "encoding.InjectBase32",
        "encoding.InjectHex",
        "encoding.InjectROT13",
        "encoding.InjectBase2048",
        "encoding.InjectBraille",
        "encoding.InjectMorse",
    ],
    "glitch": [
        "glitch.Glitch100",
        "glitch.Glitch250",
        "glitch.Glitch500",
        "glitch.Glitch1000",
    ],
    "known_signatures": [
        "knownbadsignatures.EICAR",
        "knownbadsignatures.GTUBE",
        "knownbadsignatures.GTphish",
    ],
    "continuation": [
        "continuation.ContinueSlursReclaimedSlurs50",
        "continuation.ContinueSexualContent",
    ],
    "leaking": [
        "leakreplay.LiteratureCloze",
        "leakreplay.GuardianCloze",
    ],
    "misleading": [
        "misleading.FalseAssertion50",
    ],
    "packagehallucination": [
        "packagehallucination.Python",
        "packagehallucination.JavaScript",
    ],
    "realtoxicityprompts": [
        "realtoxicityprompts.RTPSevere_Toxicity",
        "realtoxicityprompts.RTPIdentity_Attack",
        "realtoxicityprompts.RTPInsult",
        "realtoxicityprompts.RTPProfanity",
        "realtoxicityprompts.RTPThreat",
    ],
    "snowball": [
        "snowball.GraphConnectivity",
        "snowball.Primes",
        "snowball.Senators",
    ],
    "xss": [
        "xss.MarkdownImageExfil",
    ],
}


# Probe metadata
PROBE_METADATA: dict[str, dict[str, Any]] = {
    "promptinject": {
        "description": "Tests prompt injection vulnerabilities",
        "severity": "critical",
        "category": "injection",
    },
    "dan": {
        "description": "Tests DAN (Do Anything Now) jailbreak techniques",
        "severity": "critical",
        "category": "jailbreak",
    },
    "encoding": {
        "description": "Tests encoding-based bypass techniques",
        "severity": "high",
        "category": "encoding",
    },
    "glitch": {
        "description": "Tests glitch tokens and adversarial inputs",
        "severity": "medium",
        "category": "adversarial",
    },
    "knownbadsignatures": {
        "description": "Tests known malicious signatures",
        "severity": "high",
        "category": "malware",
    },
    "continuation": {
        "description": "Tests continuation attacks for harmful content",
        "severity": "high",
        "category": "content",
    },
    "leakreplay": {
        "description": "Tests for training data leakage",
        "severity": "high",
        "category": "privacy",
    },
    "misleading": {
        "description": "Tests model susceptibility to misleading prompts",
        "severity": "medium",
        "category": "reliability",
    },
    "packagehallucination": {
        "description": "Tests for hallucinated package names",
        "severity": "high",
        "category": "reliability",
    },
    "realtoxicityprompts": {
        "description": "Tests toxicity using RealToxicityPrompts dataset",
        "severity": "high",
        "category": "toxicity",
    },
    "snowball": {
        "description": "Tests for reasoning errors and hallucinations",
        "severity": "medium",
        "category": "reliability",
    },
    "xss": {
        "description": "Tests for XSS vulnerabilities in outputs",
        "severity": "critical",
        "category": "security",
    },
}


def get_probes_for_category(category: str) -> list[str]:
    """Get all probes for a given category."""
    return PROBE_CATEGORIES.get(category, [])


def get_all_probes() -> list[str]:
    """Get all available probes."""
    all_probes = []
    for probes in PROBE_CATEGORIES.values():
        all_probes.extend(probes)
    return all_probes


def get_probe_severity(probe_name: str) -> str:
    """Get severity for a probe based on its module."""
    module = probe_name.split(".")[0]
    metadata = PROBE_METADATA.get(module, {})
    return metadata.get("severity", "medium")


def get_probe_description(probe_name: str) -> str:
    """Get description for a probe based on its module."""
    module = probe_name.split(".")[0]
    metadata = PROBE_METADATA.get(module, {})
    return metadata.get("description", f"Tests using {module} probes")


def get_probe_category(probe_name: str) -> str:
    """Get category for a probe based on its module."""
    module = probe_name.split(".")[0]
    metadata = PROBE_METADATA.get(module, {})
    return metadata.get("category", "unknown")


def get_recommended_probes(risk_level: str = "standard") -> list[str]:
    """
    Get recommended probes based on risk level.
    
    Args:
        risk_level: One of 'minimal', 'standard', 'comprehensive'
    
    Returns:
        List of probe names
    """
    if risk_level == "minimal":
        # Quick security scan
        return [
            "promptinject.HijackHateHumansMini",
            "dan.Dan_11_0",
            "encoding.InjectBase64",
        ]
    elif risk_level == "standard":
        # Standard security assessment
        categories = ["prompt_injection", "jailbreaking", "encoding", "xss"]
        probes = []
        for cat in categories:
            probes.extend(get_probes_for_category(cat)[:3])
        return probes
    else:
        # Comprehensive testing
        return get_all_probes()
