"""
Pillar to Control Mapper

Maps evaluation pillar results to compliance framework controls.
"""

from dataclasses import dataclass
from typing import Any

from .frameworks import (
    ComplianceFramework,
    Control,
    ControlStatus,
    get_framework,
    FRAMEWORKS,
)


@dataclass
class PillarMapping:
    """Mapping between a pillar and compliance controls."""
    pillar_name: str
    framework_id: str
    control_id: str
    control_name: str
    relevance_score: float  # How relevant this pillar is to the control (0-1)
    weight: float  # Weight of this mapping in compliance scoring


class PillarToControlMapper:
    """Maps evaluation pillars to compliance framework controls."""
    
    # Comprehensive pillar to control relevance mapping
    PILLAR_RELEVANCE = {
        # Predictive AI Pillars
        "explain": {
            "eu-ai-act": {
                "art13-1": 1.0,  # Transparency - direct mapping
                "art14-4": 0.7,  # Human oversight - understanding
            },
            "nist-ai-rmf": {
                "mea-2": 0.8,
                "gov-1.1": 0.5,
            },
            "gdpr": {
                "art22": 1.0,  # Right to explanation
            },
            "iso-42001": {
                "iso-9.1": 0.6,
            },
        },
        "actions": {
            "eu-ai-act": {
                "art15-3": 0.9,  # Robustness
                "art15-4": 0.8,  # Cybersecurity
            },
            "nist-ai-rmf": {
                "mea-2": 0.7,
                "man-2": 0.8,
            },
        },
        "fairness": {
            "eu-ai-act": {
                "art10-5": 1.0,  # Bias examination
                "art10-3": 0.7,  # Data quality
            },
            "nist-ai-rmf": {
                "mea-3": 1.0,
                "gov-3": 0.6,
            },
            "gdpr": {
                "art35": 0.7,
            },
            "iso-42001": {
                "iso-8.4": 0.8,
            },
        },
        "robustness": {
            "eu-ai-act": {
                "art15-3": 1.0,  # Robustness requirements
                "art9-2b": 0.8,
            },
            "nist-ai-rmf": {
                "mea-2": 0.9,
                "man-4": 0.7,
            },
            "soc2": {
                "a1.1": 0.8,
                "pi1.1": 0.7,
            },
            "iso-42001": {
                "iso-9.1": 0.8,
            },
        },
        "trace": {
            "eu-ai-act": {
                "art10-2": 1.0,  # Data governance
                "art10-3": 0.8,
            },
            "nist-ai-rmf": {
                "map-1": 0.6,
            },
            "iso-42001": {
                "iso-8.1": 0.7,
            },
        },
        "testing": {
            "eu-ai-act": {
                "art15-1": 1.0,  # Accuracy
                "art13-3b": 0.8,
            },
            "nist-ai-rmf": {
                "mea-1": 1.0,
                "mea-2": 0.8,
            },
            "soc2": {
                "pi1.1": 0.8,
            },
            "iso-42001": {
                "iso-9.1": 0.9,
            },
        },
        "imitation": {
            "eu-ai-act": {
                "art15-4": 0.7,
            },
            "soc2": {
                "c1.1": 0.9,
            },
        },
        "privacy": {
            "eu-ai-act": {
                "art10-2": 0.7,
            },
            "nist-ai-rmf": {
                "map-3": 0.6,
            },
            "soc2": {
                "p1.1": 1.0,
                "c1.1": 0.7,
            },
            "gdpr": {
                "art6": 0.8,
                "art25": 1.0,
                "art35": 0.9,
            },
        },
        
        # Gen AI Pillars (use same names where overlapping)
        "security": {
            "eu-ai-act": {
                "art15-4": 1.0,
                "art9-4": 0.8,
            },
            "nist-ai-rmf": {
                "mea-2": 0.8,
                "man-2": 0.9,
            },
            "soc2": {
                "cc6.1": 1.0,
                "cc6.7": 0.8,
            },
        },
        "toxicity": {
            "eu-ai-act": {
                "art9-2a": 0.8,  # Risk to fundamental rights
            },
            "nist-ai-rmf": {
                "map-3": 0.7,
                "mea-2": 0.6,
            },
        },
        
        # Governance pillar (cross-cutting)
        "governance": {
            "eu-ai-act": {
                "art9-1": 1.0,
                "art14-1": 0.8,
            },
            "nist-ai-rmf": {
                "gov-1": 1.0,
                "gov-1.1": 1.0,
                "map-1": 0.8,
                "map-2": 0.9,
                "man-1": 0.7,
            },
            "iso-42001": {
                "iso-4.1": 0.9,
                "iso-6.1": 0.8,
                "iso-7.2": 0.7,
                "iso-8.1": 0.8,
            },
            "gdpr": {
                "art6": 0.6,
            },
        },
        
        # Accuracy pillar
        "accuracy": {
            "eu-ai-act": {
                "art15-1": 1.0,
                "art13-3b": 0.9,
            },
            "nist-ai-rmf": {
                "mea-1": 1.0,
                "mea-2": 0.8,
            },
            "soc2": {
                "pi1.1": 0.9,
            },
            "iso-42001": {
                "iso-9.1": 0.9,
            },
        },
    }
    
    def __init__(self):
        self._mappings_cache: dict[str, list[PillarMapping]] = {}
    
    def get_mappings_for_pillar(
        self,
        pillar_name: str,
        framework_id: str | None = None,
    ) -> list[PillarMapping]:
        """
        Get all control mappings for a pillar.
        
        Args:
            pillar_name: Name of the evaluation pillar
            framework_id: Optional filter by framework
            
        Returns:
            List of PillarMapping objects
        """
        cache_key = f"{pillar_name}:{framework_id or 'all'}"
        if cache_key in self._mappings_cache:
            return self._mappings_cache[cache_key]
        
        mappings = []
        pillar_relevance = self.PILLAR_RELEVANCE.get(pillar_name, {})
        
        for fw_id, controls in pillar_relevance.items():
            if framework_id and fw_id != framework_id:
                continue
            
            framework = get_framework(fw_id)
            if not framework:
                continue
            
            for control_id, relevance in controls.items():
                control = framework.get_control(control_id)
                if control:
                    mappings.append(PillarMapping(
                        pillar_name=pillar_name,
                        framework_id=fw_id,
                        control_id=control_id,
                        control_name=control.name,
                        relevance_score=relevance,
                        weight=relevance,  # Default weight equals relevance
                    ))
        
        self._mappings_cache[cache_key] = mappings
        return mappings
    
    def get_mappings_for_control(
        self,
        control_id: str,
        framework_id: str,
    ) -> list[PillarMapping]:
        """
        Get all pillar mappings for a specific control.
        
        Args:
            control_id: The control ID
            framework_id: The framework ID
            
        Returns:
            List of PillarMapping objects
        """
        mappings = []
        
        for pillar_name, fw_controls in self.PILLAR_RELEVANCE.items():
            controls = fw_controls.get(framework_id, {})
            relevance = controls.get(control_id)
            
            if relevance is not None:
                framework = get_framework(framework_id)
                control = framework.get_control(control_id) if framework else None
                
                mappings.append(PillarMapping(
                    pillar_name=pillar_name,
                    framework_id=framework_id,
                    control_id=control_id,
                    control_name=control.name if control else control_id,
                    relevance_score=relevance,
                    weight=relevance,
                ))
        
        return mappings
    
    def calculate_control_score(
        self,
        control_id: str,
        framework_id: str,
        pillar_scores: dict[str, float],
    ) -> float:
        """
        Calculate a control's compliance score based on pillar scores.
        
        Args:
            control_id: The control ID
            framework_id: The framework ID
            pillar_scores: Dict of pillar name to score (0-1)
            
        Returns:
            Weighted average score for the control
        """
        mappings = self.get_mappings_for_control(control_id, framework_id)
        
        if not mappings:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for mapping in mappings:
            pillar_score = pillar_scores.get(mapping.pillar_name, 0)
            weighted_sum += pillar_score * mapping.weight
            total_weight += mapping.weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def get_coverage_by_framework(
        self,
        pillar_scores: dict[str, float],
    ) -> dict[str, dict]:
        """
        Calculate coverage for each framework based on pillar scores.
        
        Args:
            pillar_scores: Dict of pillar name to score (0-1)
            
        Returns:
            Dict of framework_id to coverage info
        """
        coverage = {}
        
        for framework_id in FRAMEWORKS:
            framework = get_framework(framework_id)
            if not framework:
                continue
            
            controls = framework.get_controls()
            control_scores = {}
            
            for control in controls:
                score = self.calculate_control_score(
                    control.id, framework_id, pillar_scores
                )
                control_scores[control.id] = score
            
            # Calculate overall coverage
            avg_score = sum(control_scores.values()) / len(control_scores) if control_scores else 0
            
            coverage[framework_id] = {
                "framework_name": framework.name,
                "average_score": round(avg_score, 3),
                "coverage_percentage": round(avg_score * 100, 1),
                "controls_assessed": len(control_scores),
                "high_risk_controls": [
                    cid for cid, score in control_scores.items()
                    if score < 0.5
                ],
            }
        
        return coverage
    
    def get_required_pillars(
        self,
        framework_id: str,
    ) -> list[str]:
        """
        Get list of pillars required for a framework.
        
        Args:
            framework_id: The framework ID
            
        Returns:
            List of pillar names
        """
        required = set()
        
        for pillar_name, fw_controls in self.PILLAR_RELEVANCE.items():
            if framework_id in fw_controls:
                required.add(pillar_name)
        
        return list(required)
    
    def get_gap_analysis(
        self,
        framework_id: str,
        pillar_scores: dict[str, float],
        threshold: float = 0.7,
    ) -> dict:
        """
        Analyze gaps in compliance based on pillar scores.
        
        Args:
            framework_id: The framework ID
            pillar_scores: Dict of pillar scores
            threshold: Score threshold for compliance
            
        Returns:
            Gap analysis dict
        """
        framework = get_framework(framework_id)
        if not framework:
            return {"error": f"Unknown framework: {framework_id}"}
        
        gaps = []
        recommendations = []
        
        for control in framework.get_controls():
            score = self.calculate_control_score(
                control.id, framework_id, pillar_scores
            )
            
            if score < threshold:
                # Find which pillars are causing the low score
                mappings = self.get_mappings_for_control(control.id, framework_id)
                contributing_pillars = []
                
                for mapping in mappings:
                    pillar_score = pillar_scores.get(mapping.pillar_name, 0)
                    if pillar_score < threshold:
                        contributing_pillars.append({
                            "pillar": mapping.pillar_name,
                            "score": pillar_score,
                            "impact": mapping.weight,
                        })
                
                gaps.append({
                    "control_id": control.id,
                    "control_name": control.name,
                    "current_score": round(score, 3),
                    "threshold": threshold,
                    "gap": round(threshold - score, 3),
                    "contributing_pillars": contributing_pillars,
                })
                
                # Generate recommendation
                if contributing_pillars:
                    top_contributor = max(
                        contributing_pillars,
                        key=lambda p: p["impact"]
                    )
                    recommendations.append({
                        "control_id": control.id,
                        "priority": "high" if score < 0.5 else "medium",
                        "focus_pillar": top_contributor["pillar"],
                        "expected_improvement": round(
                            (threshold - score) / len(contributing_pillars), 3
                        ),
                    })
        
        return {
            "framework_id": framework_id,
            "framework_name": framework.name,
            "total_controls": len(framework.get_controls()),
            "gaps_count": len(gaps),
            "gaps": gaps,
            "recommendations": recommendations,
        }
