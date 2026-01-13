"""
Compliance Assessor

Automatically assesses compliance based on evaluation results.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .frameworks import (
    ComplianceFramework,
    Control,
    ControlStatus,
    get_framework,
)


@dataclass
class AssessmentResult:
    """Result of a compliance assessment."""
    framework_id: str
    model_id: str
    timestamp: datetime
    overall_coverage: float
    controls_assessed: int
    controls_implemented: int
    controls_partial: int
    controls_not_implemented: int
    controls_not_applicable: int
    control_results: dict[str, ControlStatus]
    evidence: dict[str, list[dict]]
    gaps: list[dict]
    recommendations: list[dict]


class ComplianceAssessor:
    """Assesses compliance based on evaluation results."""
    
    def __init__(self, db=None):
        self.db = db
    
    async def assess(
        self,
        model_id: str,
        framework_id: str,
        evaluation_results: dict[str, Any],
    ) -> AssessmentResult:
        """
        Assess compliance for a model against a framework.
        
        Args:
            model_id: The model identifier
            framework_id: The compliance framework ID
            evaluation_results: Results from evaluation pillars
            
        Returns:
            AssessmentResult with compliance status
        """
        framework = get_framework(framework_id)
        if not framework:
            raise ValueError(f"Unknown framework: {framework_id}")
        
        controls = framework.get_controls()
        control_results: dict[str, ControlStatus] = {}
        evidence: dict[str, list[dict]] = {}
        gaps: list[dict] = []
        recommendations: list[dict] = []
        
        for control in controls:
            status, control_evidence = self._assess_control(
                control, evaluation_results
            )
            control_results[control.id] = status
            evidence[control.id] = control_evidence
            
            if status == ControlStatus.NOT_IMPLEMENTED:
                gaps.append({
                    "control_id": control.id,
                    "control_name": control.name,
                    "category": control.category,
                    "requirements": control.requirements,
                })
                recommendations.extend(
                    self._generate_recommendations(control, evaluation_results)
                )
            elif status == ControlStatus.PARTIAL:
                recommendations.extend(
                    self._generate_recommendations(control, evaluation_results)
                )
        
        # Calculate summary statistics
        implemented = sum(1 for s in control_results.values() if s == ControlStatus.IMPLEMENTED)
        partial = sum(1 for s in control_results.values() if s == ControlStatus.PARTIAL)
        not_implemented = sum(1 for s in control_results.values() if s == ControlStatus.NOT_IMPLEMENTED)
        not_applicable = sum(1 for s in control_results.values() if s == ControlStatus.NOT_APPLICABLE)
        
        coverage = framework.calculate_coverage(control_results)
        
        return AssessmentResult(
            framework_id=framework_id,
            model_id=model_id,
            timestamp=datetime.utcnow(),
            overall_coverage=coverage,
            controls_assessed=len(controls),
            controls_implemented=implemented,
            controls_partial=partial,
            controls_not_implemented=not_implemented,
            controls_not_applicable=not_applicable,
            control_results=control_results,
            evidence=evidence,
            gaps=gaps,
            recommendations=recommendations,
        )
    
    def _assess_control(
        self,
        control: Control,
        evaluation_results: dict[str, Any],
    ) -> tuple[ControlStatus, list[dict]]:
        """
        Assess a single control based on evaluation results.
        
        Returns tuple of (status, evidence).
        """
        evidence: list[dict] = []
        scores: list[float] = []
        
        # Check each mapped pillar
        for pillar in control.pillar_mappings:
            pillar_result = evaluation_results.get(pillar, {})
            if pillar_result:
                score = pillar_result.get("score", 0)
                scores.append(score)
                evidence.append({
                    "type": "evaluation_result",
                    "pillar": pillar,
                    "score": score,
                    "status": pillar_result.get("status"),
                    "metrics": pillar_result.get("metrics", {}),
                })
        
        if not scores:
            return ControlStatus.NOT_ASSESSED, evidence
        
        avg_score = sum(scores) / len(scores)
        
        # Determine status based on average score
        if avg_score >= 0.8:
            return ControlStatus.IMPLEMENTED, evidence
        elif avg_score >= 0.5:
            return ControlStatus.PARTIAL, evidence
        else:
            return ControlStatus.NOT_IMPLEMENTED, evidence
    
    def _generate_recommendations(
        self,
        control: Control,
        evaluation_results: dict[str, Any],
    ) -> list[dict]:
        """Generate recommendations for improving control compliance."""
        recommendations = []
        
        for pillar in control.pillar_mappings:
            pillar_result = evaluation_results.get(pillar, {})
            score = pillar_result.get("score", 0)
            
            if score < 0.8:
                rec = self._get_pillar_recommendation(pillar, score, control)
                if rec:
                    recommendations.append(rec)
        
        return recommendations
    
    def _get_pillar_recommendation(
        self,
        pillar: str,
        score: float,
        control: Control,
    ) -> dict | None:
        """Get specific recommendation for a pillar."""
        recommendations_map = {
            "accuracy": {
                "title": "Improve Model Accuracy",
                "description": "Model accuracy below threshold. Consider retraining with additional data or hyperparameter tuning.",
                "actions": [
                    "Review training data quality",
                    "Increase training data volume",
                    "Tune model hyperparameters",
                    "Consider ensemble methods",
                ],
            },
            "fairness": {
                "title": "Address Bias Issues",
                "description": "Fairness evaluation identified potential bias. Implement bias mitigation techniques.",
                "actions": [
                    "Analyze demographic parity metrics",
                    "Apply reweighting or resampling",
                    "Use fairness-aware algorithms",
                    "Review training data for representation",
                ],
            },
            "robustness": {
                "title": "Enhance Model Robustness",
                "description": "Model shows vulnerability to perturbations. Implement robustness improvements.",
                "actions": [
                    "Apply adversarial training",
                    "Add input validation",
                    "Implement confidence thresholds",
                    "Test with edge cases",
                ],
            },
            "security": {
                "title": "Strengthen Security Controls",
                "description": "Security vulnerabilities detected. Implement security hardening.",
                "actions": [
                    "Add prompt injection filters",
                    "Implement rate limiting",
                    "Enable input/output logging",
                    "Deploy guardrails",
                ],
            },
            "privacy": {
                "title": "Improve Privacy Protection",
                "description": "Privacy risks identified. Implement privacy-preserving measures.",
                "actions": [
                    "Enable PII detection and masking",
                    "Apply differential privacy",
                    "Review data retention policies",
                    "Implement access controls",
                ],
            },
            "explain": {
                "title": "Enhance Explainability",
                "description": "Model interpretability below requirements. Improve explanation capabilities.",
                "actions": [
                    "Implement SHAP/LIME explanations",
                    "Add feature importance reports",
                    "Generate human-readable explanations",
                    "Document decision factors",
                ],
            },
            "governance": {
                "title": "Strengthen Governance",
                "description": "Governance controls need improvement. Enhance documentation and processes.",
                "actions": [
                    "Complete model documentation",
                    "Establish review processes",
                    "Implement audit logging",
                    "Define ownership and accountability",
                ],
            },
            "trace": {
                "title": "Improve Data Lineage",
                "description": "Data lineage tracking incomplete. Implement comprehensive tracking.",
                "actions": [
                    "Document data sources",
                    "Track data transformations",
                    "Version training datasets",
                    "Implement data catalog",
                ],
            },
            "testing": {
                "title": "Expand Testing Coverage",
                "description": "Testing coverage insufficient. Expand test suite.",
                "actions": [
                    "Add unit tests for model components",
                    "Implement integration tests",
                    "Add performance benchmarks",
                    "Test edge cases",
                ],
            },
            "actions": {
                "title": "Address Adversarial Vulnerabilities",
                "description": "Model vulnerable to adversarial attacks. Implement defenses.",
                "actions": [
                    "Apply adversarial training",
                    "Add input preprocessing",
                    "Implement detection mechanisms",
                    "Monitor for attack patterns",
                ],
            },
            "imitation": {
                "title": "Protect Model IP",
                "description": "Model vulnerable to extraction attacks. Implement IP protection.",
                "actions": [
                    "Add watermarking",
                    "Implement rate limiting",
                    "Monitor for extraction attempts",
                    "Use differential privacy",
                ],
            },
        }
        
        rec_template = recommendations_map.get(pillar)
        if rec_template:
            return {
                "control_id": control.id,
                "control_name": control.name,
                "pillar": pillar,
                "current_score": score,
                "target_score": 0.8,
                **rec_template,
                "priority": "high" if score < 0.5 else "medium",
            }
        return None
    
    async def assess_all_frameworks(
        self,
        model_id: str,
        evaluation_results: dict[str, Any],
    ) -> dict[str, AssessmentResult]:
        """Assess model against all frameworks."""
        from .frameworks import FRAMEWORKS
        
        results = {}
        for framework_id in FRAMEWORKS:
            results[framework_id] = await self.assess(
                model_id, framework_id, evaluation_results
            )
        return results
    
    async def get_gap_analysis(
        self,
        model_id: str,
        framework_id: str,
        evaluation_results: dict[str, Any],
    ) -> dict:
        """Get detailed gap analysis for a framework."""
        assessment = await self.assess(model_id, framework_id, evaluation_results)
        
        return {
            "framework_id": framework_id,
            "model_id": model_id,
            "coverage": assessment.overall_coverage,
            "gaps": assessment.gaps,
            "recommendations": assessment.recommendations,
            "priority_actions": [
                r for r in assessment.recommendations
                if r.get("priority") == "high"
            ][:5],  # Top 5 priority actions
        }
