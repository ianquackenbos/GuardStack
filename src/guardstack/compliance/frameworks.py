"""
Compliance Frameworks

Defines regulatory compliance frameworks and their control structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    """AI system risk levels per EU AI Act."""
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class ControlStatus(str, Enum):
    """Control implementation status."""
    NOT_ASSESSED = "not_assessed"
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class Control:
    """A single compliance control/requirement."""
    id: str
    name: str
    description: str
    category: str
    requirements: list[str] = field(default_factory=list)
    evidence_types: list[str] = field(default_factory=list)
    pillar_mappings: list[str] = field(default_factory=list)
    status: ControlStatus = ControlStatus.NOT_ASSESSED
    evidence: list[dict] = field(default_factory=list)
    notes: str = ""


@dataclass
class ControlCategory:
    """Category grouping of controls."""
    id: str
    name: str
    description: str
    controls: list[Control] = field(default_factory=list)


class ComplianceFramework(ABC):
    """Base class for compliance frameworks."""
    
    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.version: str = ""
        self.description: str = ""
        self.categories: list[ControlCategory] = []
    
    @abstractmethod
    def get_controls(self) -> list[Control]:
        """Get all controls in the framework."""
        pass
    
    @abstractmethod
    def get_control(self, control_id: str) -> Control | None:
        """Get a specific control by ID."""
        pass
    
    @abstractmethod
    def get_pillar_mappings(self, pillar_name: str) -> list[Control]:
        """Get controls that map to a specific evaluation pillar."""
        pass
    
    def get_categories(self) -> list[ControlCategory]:
        """Get all control categories."""
        return self.categories
    
    def calculate_coverage(self, assessments: dict[str, ControlStatus]) -> float:
        """Calculate compliance coverage percentage."""
        controls = self.get_controls()
        if not controls:
            return 0.0
        
        implemented = sum(
            1 for c in controls
            if assessments.get(c.id) in [ControlStatus.IMPLEMENTED, ControlStatus.NOT_APPLICABLE]
        )
        return implemented / len(controls)


class EUAIActFramework(ComplianceFramework):
    """EU AI Act compliance framework."""
    
    def __init__(self):
        super().__init__()
        self.id = "eu-ai-act"
        self.name = "EU AI Act"
        self.version = "2024"
        self.description = "European Union Artificial Intelligence Act"
        self._init_controls()
    
    def _init_controls(self):
        """Initialize EU AI Act controls."""
        
        # Risk Management (Article 9)
        risk_mgmt = ControlCategory(
            id="risk-management",
            name="Risk Management System",
            description="Requirements for risk management of high-risk AI systems",
            controls=[
                Control(
                    id="art9-1",
                    name="Risk Management System Establishment",
                    description="Establish, implement, document and maintain a risk management system",
                    category="risk-management",
                    requirements=[
                        "Continuous iterative process throughout lifecycle",
                        "Regular systematic updates",
                        "Documentation of risk management activities",
                    ],
                    evidence_types=["documentation", "process_records"],
                    pillar_mappings=["robustness", "security", "governance"],
                ),
                Control(
                    id="art9-2a",
                    name="Risk Identification and Analysis",
                    description="Identification and analysis of known and foreseeable risks",
                    category="risk-management",
                    requirements=[
                        "Identify risks to health, safety, fundamental rights",
                        "Consider intended use and reasonably foreseeable misuse",
                        "Risk analysis documentation",
                    ],
                    evidence_types=["risk_assessment", "evaluation_results"],
                    pillar_mappings=["robustness", "fairness", "security"],
                ),
                Control(
                    id="art9-2b",
                    name="Risk Estimation and Evaluation",
                    description="Estimation and evaluation of risks during intended use and misuse",
                    category="risk-management",
                    requirements=[
                        "Quantitative risk estimation",
                        "Evaluation against thresholds",
                        "Continuous monitoring",
                    ],
                    evidence_types=["evaluation_results", "metrics"],
                    pillar_mappings=["accuracy", "robustness", "testing"],
                ),
                Control(
                    id="art9-4",
                    name="Risk Mitigation Measures",
                    description="Adoption of suitable risk management measures",
                    category="risk-management",
                    requirements=[
                        "Eliminate or reduce risks through design",
                        "Implement mitigation measures",
                        "Provide information and training",
                    ],
                    evidence_types=["mitigation_records", "guardrail_config"],
                    pillar_mappings=["robustness", "security"],
                ),
            ]
        )
        
        # Data Governance (Article 10)
        data_governance = ControlCategory(
            id="data-governance",
            name="Data and Data Governance",
            description="Requirements for training, validation and testing data",
            controls=[
                Control(
                    id="art10-2",
                    name="Data Governance Practices",
                    description="Training, validation and testing data subject to governance practices",
                    category="data-governance",
                    requirements=[
                        "Design choices documentation",
                        "Data collection processes",
                        "Data preparation operations",
                        "Relevant assumptions assessment",
                    ],
                    evidence_types=["data_documentation", "lineage_records"],
                    pillar_mappings=["trace", "governance", "privacy"],
                ),
                Control(
                    id="art10-3",
                    name="Data Quality Requirements",
                    description="Training, validation and testing datasets shall be relevant and representative",
                    category="data-governance",
                    requirements=[
                        "Relevant to intended purpose",
                        "Sufficiently representative",
                        "Free of errors",
                        "Complete",
                    ],
                    evidence_types=["data_quality_reports", "evaluation_results"],
                    pillar_mappings=["trace", "fairness", "accuracy"],
                ),
                Control(
                    id="art10-5",
                    name="Bias Examination",
                    description="Examination of data for possible biases",
                    category="data-governance",
                    requirements=[
                        "Bias detection in datasets",
                        "Bias mitigation measures",
                        "Documentation of bias analysis",
                    ],
                    evidence_types=["fairness_evaluation", "bias_reports"],
                    pillar_mappings=["fairness"],
                ),
            ]
        )
        
        # Transparency (Article 13)
        transparency = ControlCategory(
            id="transparency",
            name="Transparency and Information",
            description="Transparency requirements for high-risk AI systems",
            controls=[
                Control(
                    id="art13-1",
                    name="Transparency Design",
                    description="AI systems designed to be sufficiently transparent",
                    category="transparency",
                    requirements=[
                        "Interpretable operation",
                        "Appropriate user understanding",
                        "Explanation capabilities",
                    ],
                    evidence_types=["explainability_results", "documentation"],
                    pillar_mappings=["explain"],
                ),
                Control(
                    id="art13-3b",
                    name="Performance Characteristics",
                    description="Documentation of performance characteristics",
                    category="transparency",
                    requirements=[
                        "Level of accuracy",
                        "Robustness metrics",
                        "Cybersecurity measures",
                        "Known limitations",
                    ],
                    evidence_types=["evaluation_results", "metrics"],
                    pillar_mappings=["accuracy", "robustness", "security", "testing"],
                ),
            ]
        )
        
        # Human Oversight (Article 14)
        human_oversight = ControlCategory(
            id="human-oversight",
            name="Human Oversight",
            description="Human oversight requirements",
            controls=[
                Control(
                    id="art14-1",
                    name="Human Oversight Design",
                    description="AI systems designed for effective human oversight",
                    category="human-oversight",
                    requirements=[
                        "Oversight by natural persons",
                        "Prevention of automation bias",
                        "Intervention capabilities",
                    ],
                    evidence_types=["design_documentation", "ui_screenshots"],
                    pillar_mappings=["governance"],
                ),
                Control(
                    id="art14-4",
                    name="Oversight Measures",
                    description="Appropriate oversight measures",
                    category="human-oversight",
                    requirements=[
                        "Understanding AI capabilities and limitations",
                        "Monitoring of operation",
                        "Ability to override decisions",
                    ],
                    evidence_types=["operational_procedures", "guardrail_config"],
                    pillar_mappings=["governance", "explain"],
                ),
            ]
        )
        
        # Accuracy, Robustness, Cybersecurity (Article 15)
        technical_requirements = ControlCategory(
            id="technical-requirements",
            name="Accuracy, Robustness and Cybersecurity",
            description="Technical requirements for high-risk AI systems",
            controls=[
                Control(
                    id="art15-1",
                    name="Appropriate Accuracy",
                    description="AI systems achieve appropriate level of accuracy",
                    category="technical-requirements",
                    requirements=[
                        "Accuracy levels declared in documentation",
                        "Accuracy appropriate to intended purpose",
                        "Performance metrics documented",
                    ],
                    evidence_types=["accuracy_metrics", "evaluation_results"],
                    pillar_mappings=["accuracy", "testing"],
                ),
                Control(
                    id="art15-3",
                    name="Robustness Requirements",
                    description="AI systems resilient to errors and inconsistencies",
                    category="technical-requirements",
                    requirements=[
                        "Resilient to errors",
                        "Handle faults and inconsistencies",
                        "Redundancy measures where appropriate",
                    ],
                    evidence_types=["robustness_evaluation", "stress_test_results"],
                    pillar_mappings=["robustness", "actions"],
                ),
                Control(
                    id="art15-4",
                    name="Cybersecurity Resilience",
                    description="AI systems resilient to manipulation attempts",
                    category="technical-requirements",
                    requirements=[
                        "Resilient against third-party manipulation",
                        "Protection against adversarial attacks",
                        "Data poisoning prevention",
                    ],
                    evidence_types=["security_evaluation", "penetration_test_results"],
                    pillar_mappings=["security", "actions", "imitation"],
                ),
            ]
        )
        
        self.categories = [
            risk_mgmt,
            data_governance,
            transparency,
            human_oversight,
            technical_requirements,
        ]
    
    def get_controls(self) -> list[Control]:
        """Get all EU AI Act controls."""
        controls = []
        for category in self.categories:
            controls.extend(category.controls)
        return controls
    
    def get_control(self, control_id: str) -> Control | None:
        """Get a specific control by ID."""
        for control in self.get_controls():
            if control.id == control_id:
                return control
        return None
    
    def get_pillar_mappings(self, pillar_name: str) -> list[Control]:
        """Get controls that map to a specific evaluation pillar."""
        return [
            c for c in self.get_controls()
            if pillar_name in c.pillar_mappings
        ]
    
    def classify_risk_level(self, model_info: dict) -> RiskLevel:
        """Classify AI system risk level per EU AI Act categories."""
        use_case = model_info.get("use_case", "").lower()
        category = model_info.get("category", "").lower()
        
        # Unacceptable risk (Article 5)
        unacceptable_keywords = [
            "social_scoring", "subliminal", "exploitation",
            "biometric_categorization", "predictive_policing",
        ]
        if any(kw in use_case or kw in category for kw in unacceptable_keywords):
            return RiskLevel.UNACCEPTABLE
        
        # High risk (Article 6, Annex III)
        high_risk_categories = [
            "biometric", "critical_infrastructure", "education",
            "employment", "essential_services", "law_enforcement",
            "migration", "justice", "democratic_processes",
        ]
        if any(cat in use_case or cat in category for cat in high_risk_categories):
            return RiskLevel.HIGH
        
        # Limited risk (Article 52)
        limited_risk = ["chatbot", "emotion_recognition", "deepfake"]
        if any(lr in use_case or lr in category for lr in limited_risk):
            return RiskLevel.LIMITED
        
        return RiskLevel.MINIMAL


class NISTAIRMFFramework(ComplianceFramework):
    """NIST AI Risk Management Framework."""
    
    def __init__(self):
        super().__init__()
        self.id = "nist-ai-rmf"
        self.name = "NIST AI RMF"
        self.version = "1.0"
        self.description = "NIST AI Risk Management Framework"
        self._init_controls()
    
    def _init_controls(self):
        """Initialize NIST AI RMF controls."""
        
        # GOVERN Function
        govern = ControlCategory(
            id="govern",
            name="GOVERN",
            description="Cultivate a culture of risk management",
            controls=[
                Control(
                    id="gov-1",
                    name="Legal and Regulatory Requirements",
                    description="Legal and regulatory requirements are identified",
                    category="govern",
                    requirements=[
                        "Identify applicable regulations",
                        "Map requirements to controls",
                        "Monitor regulatory changes",
                    ],
                    evidence_types=["compliance_mapping", "regulatory_analysis"],
                    pillar_mappings=["governance"],
                ),
                Control(
                    id="gov-1.1",
                    name="AI Policies",
                    description="Policies and procedures established for AI systems",
                    category="govern",
                    requirements=[
                        "Documented AI policies",
                        "Implementation procedures",
                        "Regular policy review",
                    ],
                    evidence_types=["policy_documents", "procedure_records"],
                    pillar_mappings=["governance"],
                ),
                Control(
                    id="gov-3",
                    name="Workforce Diversity",
                    description="Workforce diversity and domain expertise maintained",
                    category="govern",
                    requirements=[
                        "Diverse teams",
                        "Domain expertise",
                        "AI literacy training",
                    ],
                    evidence_types=["team_composition", "training_records"],
                    pillar_mappings=["governance", "fairness"],
                ),
            ]
        )
        
        # MAP Function
        map_function = ControlCategory(
            id="map",
            name="MAP",
            description="Understand context and identify risks",
            controls=[
                Control(
                    id="map-1",
                    name="Intended Purpose Documentation",
                    description="AI system purpose and context documented",
                    category="map",
                    requirements=[
                        "Intended purpose statement",
                        "Deployment context",
                        "Stakeholder identification",
                    ],
                    evidence_types=["system_documentation", "use_case_analysis"],
                    pillar_mappings=["governance"],
                ),
                Control(
                    id="map-2",
                    name="AI Actor Identification",
                    description="AI actors and their roles identified",
                    category="map",
                    requirements=[
                        "Actor mapping",
                        "Responsibility assignment",
                        "Access controls",
                    ],
                    evidence_types=["actor_mapping", "raci_matrix"],
                    pillar_mappings=["governance"],
                ),
                Control(
                    id="map-3",
                    name="AI Lifecycle Risks",
                    description="AI risks across lifecycle identified",
                    category="map",
                    requirements=[
                        "Development risks",
                        "Deployment risks",
                        "Operational risks",
                    ],
                    evidence_types=["risk_assessment", "lifecycle_analysis"],
                    pillar_mappings=["robustness", "security", "governance"],
                ),
            ]
        )
        
        # MEASURE Function
        measure = ControlCategory(
            id="measure",
            name="MEASURE",
            description="Analyze, assess, and track AI risks",
            controls=[
                Control(
                    id="mea-1",
                    name="Risk Metrics",
                    description="Appropriate metrics identified and applied",
                    category="measure",
                    requirements=[
                        "Performance metrics",
                        "Fairness metrics",
                        "Safety metrics",
                    ],
                    evidence_types=["metrics_definition", "evaluation_results"],
                    pillar_mappings=["accuracy", "fairness", "testing"],
                ),
                Control(
                    id="mea-2",
                    name="Trustworthiness Assessment",
                    description="AI system trustworthiness evaluated",
                    category="measure",
                    requirements=[
                        "Accuracy assessment",
                        "Reliability assessment",
                        "Safety assessment",
                    ],
                    evidence_types=["evaluation_results", "test_reports"],
                    pillar_mappings=["accuracy", "robustness", "security"],
                ),
                Control(
                    id="mea-3",
                    name="Bias Assessment",
                    description="AI system evaluated for bias",
                    category="measure",
                    requirements=[
                        "Fairness testing",
                        "Demographic analysis",
                        "Bias mitigation",
                    ],
                    evidence_types=["fairness_evaluation", "bias_reports"],
                    pillar_mappings=["fairness"],
                ),
            ]
        )
        
        # MANAGE Function
        manage = ControlCategory(
            id="manage",
            name="MANAGE",
            description="Prioritize, respond to, and manage AI risks",
            controls=[
                Control(
                    id="man-1",
                    name="Risk Prioritization",
                    description="AI risks prioritized based on impact",
                    category="manage",
                    requirements=[
                        "Risk ranking",
                        "Impact assessment",
                        "Mitigation prioritization",
                    ],
                    evidence_types=["risk_register", "impact_analysis"],
                    pillar_mappings=["governance"],
                ),
                Control(
                    id="man-2",
                    name="Risk Treatment",
                    description="AI risks treated and mitigated",
                    category="manage",
                    requirements=[
                        "Mitigation plans",
                        "Control implementation",
                        "Residual risk tracking",
                    ],
                    evidence_types=["mitigation_records", "control_evidence"],
                    pillar_mappings=["robustness", "security"],
                ),
                Control(
                    id="man-4",
                    name="Continuous Monitoring",
                    description="AI system performance continuously monitored",
                    category="manage",
                    requirements=[
                        "Performance monitoring",
                        "Drift detection",
                        "Incident response",
                    ],
                    evidence_types=["monitoring_dashboards", "alert_records"],
                    pillar_mappings=["testing", "robustness"],
                ),
            ]
        )
        
        self.categories = [govern, map_function, measure, manage]
    
    def get_controls(self) -> list[Control]:
        """Get all NIST AI RMF controls."""
        controls = []
        for category in self.categories:
            controls.extend(category.controls)
        return controls
    
    def get_control(self, control_id: str) -> Control | None:
        """Get a specific control by ID."""
        for control in self.get_controls():
            if control.id == control_id:
                return control
        return None
    
    def get_pillar_mappings(self, pillar_name: str) -> list[Control]:
        """Get controls that map to a specific evaluation pillar."""
        return [
            c for c in self.get_controls()
            if pillar_name in c.pillar_mappings
        ]


class SOC2Framework(ComplianceFramework):
    """SOC 2 Type II framework with AI-specific controls."""
    
    def __init__(self):
        super().__init__()
        self.id = "soc2"
        self.name = "SOC 2 Type II"
        self.version = "2017"
        self.description = "SOC 2 Trust Services Criteria with AI extensions"
        self._init_controls()
    
    def _init_controls(self):
        """Initialize SOC 2 controls."""
        
        security = ControlCategory(
            id="security",
            name="Security",
            description="Protection of system resources",
            controls=[
                Control(
                    id="cc6.1",
                    name="Logical Access Security",
                    description="Logical access security for AI systems",
                    category="security",
                    requirements=[
                        "Access controls for models",
                        "API authentication",
                        "Role-based access",
                    ],
                    evidence_types=["access_controls", "audit_logs"],
                    pillar_mappings=["security", "governance"],
                ),
                Control(
                    id="cc6.7",
                    name="Transmission Security",
                    description="Data in transit protected",
                    category="security",
                    requirements=[
                        "Encryption in transit",
                        "Secure API endpoints",
                        "Certificate management",
                    ],
                    evidence_types=["network_config", "certificate_records"],
                    pillar_mappings=["security", "privacy"],
                ),
            ]
        )
        
        availability = ControlCategory(
            id="availability",
            name="Availability",
            description="System availability commitments",
            controls=[
                Control(
                    id="a1.1",
                    name="AI System Availability",
                    description="AI inference availability maintained",
                    category="availability",
                    requirements=[
                        "SLA compliance",
                        "Failover mechanisms",
                        "Performance monitoring",
                    ],
                    evidence_types=["sla_metrics", "uptime_reports"],
                    pillar_mappings=["robustness", "testing"],
                ),
            ]
        )
        
        confidentiality = ControlCategory(
            id="confidentiality",
            name="Confidentiality",
            description="Protection of confidential information",
            controls=[
                Control(
                    id="c1.1",
                    name="AI Data Confidentiality",
                    description="Training data and model confidentiality",
                    category="confidentiality",
                    requirements=[
                        "Data encryption at rest",
                        "Model protection",
                        "Access logging",
                    ],
                    evidence_types=["encryption_config", "access_logs"],
                    pillar_mappings=["privacy", "imitation", "security"],
                ),
            ]
        )
        
        processing_integrity = ControlCategory(
            id="processing-integrity",
            name="Processing Integrity",
            description="System processing completeness and accuracy",
            controls=[
                Control(
                    id="pi1.1",
                    name="AI Processing Integrity",
                    description="AI inference integrity maintained",
                    category="processing-integrity",
                    requirements=[
                        "Input validation",
                        "Output verification",
                        "Audit trails",
                    ],
                    evidence_types=["validation_logs", "audit_trails"],
                    pillar_mappings=["accuracy", "robustness", "testing"],
                ),
            ]
        )
        
        privacy = ControlCategory(
            id="privacy",
            name="Privacy",
            description="Protection of personal information",
            controls=[
                Control(
                    id="p1.1",
                    name="AI Privacy Controls",
                    description="Personal data in AI systems protected",
                    category="privacy",
                    requirements=[
                        "PII detection and masking",
                        "Data minimization",
                        "Consent management",
                    ],
                    evidence_types=["privacy_assessments", "pii_scan_results"],
                    pillar_mappings=["privacy"],
                ),
            ]
        )
        
        self.categories = [security, availability, confidentiality, processing_integrity, privacy]
    
    def get_controls(self) -> list[Control]:
        """Get all SOC 2 controls."""
        controls = []
        for category in self.categories:
            controls.extend(category.controls)
        return controls
    
    def get_control(self, control_id: str) -> Control | None:
        """Get a specific control by ID."""
        for control in self.get_controls():
            if control.id == control_id:
                return control
        return None
    
    def get_pillar_mappings(self, pillar_name: str) -> list[Control]:
        """Get controls that map to a specific evaluation pillar."""
        return [
            c for c in self.get_controls()
            if pillar_name in c.pillar_mappings
        ]


class ISO42001Framework(ComplianceFramework):
    """ISO/IEC 42001 AI Management System Standard."""
    
    def __init__(self):
        super().__init__()
        self.id = "iso-42001"
        self.name = "ISO/IEC 42001"
        self.version = "2023"
        self.description = "AI Management System Standard"
        self._init_controls()
    
    def _init_controls(self):
        """Initialize ISO 42001 controls."""
        
        context = ControlCategory(
            id="context",
            name="Context of the Organization",
            description="Understanding the organization and its context",
            controls=[
                Control(
                    id="iso-4.1",
                    name="Understanding Context",
                    description="Determine issues relevant to AI management",
                    category="context",
                    requirements=[
                        "External context analysis",
                        "Internal context analysis",
                        "Stakeholder needs",
                    ],
                    evidence_types=["context_analysis", "stakeholder_register"],
                    pillar_mappings=["governance"],
                ),
            ]
        )
        
        planning = ControlCategory(
            id="planning",
            name="Planning",
            description="Planning for AI management system",
            controls=[
                Control(
                    id="iso-6.1",
                    name="Risk and Opportunity Assessment",
                    description="Address risks and opportunities for AI systems",
                    category="planning",
                    requirements=[
                        "Risk assessment",
                        "Opportunity identification",
                        "Action planning",
                    ],
                    evidence_types=["risk_assessment", "action_plans"],
                    pillar_mappings=["robustness", "security", "governance"],
                ),
            ]
        )
        
        support = ControlCategory(
            id="support",
            name="Support",
            description="Resources and support for AI management",
            controls=[
                Control(
                    id="iso-7.2",
                    name="Competence",
                    description="Ensure AI competence of personnel",
                    category="support",
                    requirements=[
                        "Competence requirements",
                        "Training programs",
                        "Competence records",
                    ],
                    evidence_types=["training_records", "competence_assessments"],
                    pillar_mappings=["governance"],
                ),
            ]
        )
        
        operation = ControlCategory(
            id="operation",
            name="Operation",
            description="Operational planning and control",
            controls=[
                Control(
                    id="iso-8.1",
                    name="Operational Planning",
                    description="Plan, implement and control AI processes",
                    category="operation",
                    requirements=[
                        "Process documentation",
                        "Control implementation",
                        "Change management",
                    ],
                    evidence_types=["process_docs", "change_records"],
                    pillar_mappings=["governance", "trace"],
                ),
                Control(
                    id="iso-8.4",
                    name="AI System Impact Assessment",
                    description="Assess impacts of AI systems",
                    category="operation",
                    requirements=[
                        "Impact assessment",
                        "Risk evaluation",
                        "Mitigation measures",
                    ],
                    evidence_types=["impact_assessments", "evaluation_results"],
                    pillar_mappings=["fairness", "privacy", "robustness"],
                ),
            ]
        )
        
        performance = ControlCategory(
            id="performance",
            name="Performance Evaluation",
            description="Monitoring and measurement",
            controls=[
                Control(
                    id="iso-9.1",
                    name="Monitoring and Measurement",
                    description="Determine monitoring needs for AI systems",
                    category="performance",
                    requirements=[
                        "Performance metrics",
                        "Monitoring methods",
                        "Analysis and evaluation",
                    ],
                    evidence_types=["metrics_dashboards", "evaluation_results"],
                    pillar_mappings=["accuracy", "testing", "robustness"],
                ),
            ]
        )
        
        self.categories = [context, planning, support, operation, performance]
    
    def get_controls(self) -> list[Control]:
        """Get all ISO 42001 controls."""
        controls = []
        for category in self.categories:
            controls.extend(category.controls)
        return controls
    
    def get_control(self, control_id: str) -> Control | None:
        """Get a specific control by ID."""
        for control in self.get_controls():
            if control.id == control_id:
                return control
        return None
    
    def get_pillar_mappings(self, pillar_name: str) -> list[Control]:
        """Get controls that map to a specific evaluation pillar."""
        return [
            c for c in self.get_controls()
            if pillar_name in c.pillar_mappings
        ]


class GDPRFramework(ComplianceFramework):
    """GDPR framework for AI/ML data processing."""
    
    def __init__(self):
        super().__init__()
        self.id = "gdpr"
        self.name = "GDPR"
        self.version = "2018"
        self.description = "General Data Protection Regulation - AI/ML provisions"
        self._init_controls()
    
    def _init_controls(self):
        """Initialize GDPR controls relevant to AI."""
        
        lawfulness = ControlCategory(
            id="lawfulness",
            name="Lawfulness of Processing",
            description="Legal basis for AI data processing",
            controls=[
                Control(
                    id="art6",
                    name="Lawful Basis for Processing",
                    description="Legal basis for AI training data processing",
                    category="lawfulness",
                    requirements=[
                        "Identify legal basis",
                        "Document legitimate interests",
                        "Consent management where required",
                    ],
                    evidence_types=["legal_basis_documentation", "consent_records"],
                    pillar_mappings=["privacy", "governance"],
                ),
            ]
        )
        
        automated_decisions = ControlCategory(
            id="automated-decisions",
            name="Automated Decision-Making",
            description="Article 22 - Rights related to automated decisions",
            controls=[
                Control(
                    id="art22",
                    name="Automated Individual Decisions",
                    description="Safeguards for automated decision-making",
                    category="automated-decisions",
                    requirements=[
                        "Human intervention availability",
                        "Right to explanation",
                        "Contest decision capability",
                    ],
                    evidence_types=["explanation_capabilities", "intervention_procedures"],
                    pillar_mappings=["explain", "governance"],
                ),
            ]
        )
        
        data_protection = ControlCategory(
            id="data-protection",
            name="Data Protection by Design",
            description="Article 25 - Data protection by design and default",
            controls=[
                Control(
                    id="art25",
                    name="Privacy by Design",
                    description="Data protection integrated into AI system design",
                    category="data-protection",
                    requirements=[
                        "Data minimization",
                        "Purpose limitation",
                        "Privacy-preserving techniques",
                    ],
                    evidence_types=["design_documentation", "privacy_assessments"],
                    pillar_mappings=["privacy"],
                ),
            ]
        )
        
        dpia = ControlCategory(
            id="dpia",
            name="Data Protection Impact Assessment",
            description="Article 35 - DPIA for high-risk processing",
            controls=[
                Control(
                    id="art35",
                    name="DPIA for AI Systems",
                    description="Impact assessment for AI processing",
                    category="dpia",
                    requirements=[
                        "Systematic description of processing",
                        "Necessity and proportionality assessment",
                        "Risk assessment",
                        "Mitigation measures",
                    ],
                    evidence_types=["dpia_report", "risk_assessment"],
                    pillar_mappings=["privacy", "fairness", "governance"],
                ),
            ]
        )
        
        self.categories = [lawfulness, automated_decisions, data_protection, dpia]
    
    def get_controls(self) -> list[Control]:
        """Get all GDPR controls."""
        controls = []
        for category in self.categories:
            controls.extend(category.controls)
        return controls
    
    def get_control(self, control_id: str) -> Control | None:
        """Get a specific control by ID."""
        for control in self.get_controls():
            if control.id == control_id:
                return control
        return None
    
    def get_pillar_mappings(self, pillar_name: str) -> list[Control]:
        """Get controls that map to a specific evaluation pillar."""
        return [
            c for c in self.get_controls()
            if pillar_name in c.pillar_mappings
        ]


# Framework registry
FRAMEWORKS: dict[str, type[ComplianceFramework]] = {
    "eu-ai-act": EUAIActFramework,
    "nist-ai-rmf": NISTAIRMFFramework,
    "soc2": SOC2Framework,
    "iso-42001": ISO42001Framework,
    "gdpr": GDPRFramework,
}


def get_framework(framework_id: str) -> ComplianceFramework | None:
    """Get a framework instance by ID."""
    framework_class = FRAMEWORKS.get(framework_id)
    if framework_class:
        return framework_class()
    return None


def list_frameworks() -> list[dict]:
    """List all available frameworks."""
    return [
        {
            "id": fw_id,
            "name": fw_class().name,
            "version": fw_class().version,
            "description": fw_class().description,
        }
        for fw_id, fw_class in FRAMEWORKS.items()
    ]
