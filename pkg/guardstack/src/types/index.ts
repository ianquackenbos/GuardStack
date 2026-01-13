/**
 * GuardStack TypeScript Type Definitions
 */

// ==================== Core Types ====================

export type ModelType = 'predictive' | 'genai' | 'agentic';
export type ModelFramework = 'sklearn' | 'pytorch' | 'tensorflow' | 'huggingface' | 'openai' | 'anthropic' | 'ollama' | 'custom';
export type EvaluationStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type ComplianceStatus = 'compliant' | 'non_compliant' | 'partial' | 'not_assessed';

// ==================== Model Types ====================

export interface RegisteredModel {
  id: string;
  name: string;
  description: string;
  model_type: ModelType;
  framework: ModelFramework;
  version: string;
  artifact_uri: string;
  metadata: Record<string, unknown>;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ModelVersion {
  id: string;
  model_id: string;
  version: string;
  artifact_uri: string;
  metrics: Record<string, number>;
  created_at: string;
}

// ==================== Evaluation Types ====================

export interface Evaluation {
  id: string;
  model_id: string;
  evaluation_type: ModelType;
  status: EvaluationStatus;
  overall_score: number;
  risk_level: RiskLevel;
  started_at: string;
  completed_at: string | null;
  pillar_results: PillarResult[];
  config: EvaluationConfig;
}

export interface PillarResult {
  id: string;
  evaluation_id: string;
  pillar_name: string;
  score: number;
  passed: boolean;
  findings: Finding[];
  metrics: Record<string, number>;
  execution_time_ms: number;
}

export interface Finding {
  id: string;
  type: string;
  severity: RiskLevel;
  title: string;
  description: string;
  recommendation: string;
  evidence: Record<string, unknown>;
}

export interface EvaluationConfig {
  pillars: string[];
  thresholds: Record<string, number>;
  dataset_uri?: string;
  sample_size?: number;
  timeout?: number;
}

// ==================== Pillar Types ====================

// Gen AI Pillars
export interface GenAIPillars {
  privacy: PrivacyPillarResult;
  toxicity: ToxicityPillarResult;
  fairness: FairnessPillarResult;
  security: SecurityPillarResult;
}

export interface PrivacyPillarResult extends PillarResult {
  pii_detected: PIIEntity[];
  redacted_count: number;
}

export interface PIIEntity {
  type: string;
  confidence: number;
  start: number;
  end: number;
}

export interface ToxicityPillarResult extends PillarResult {
  toxicity_scores: ToxicityScores;
  flagged_samples: number;
}

export interface ToxicityScores {
  toxicity: number;
  severe_toxicity: number;
  obscene: number;
  threat: number;
  insult: number;
  identity_attack: number;
  sexual_explicit: number;
}

export interface FairnessPillarResult extends PillarResult {
  demographic_parity: number;
  equalized_odds: number;
  bias_metrics: Record<string, number>;
}

export interface SecurityPillarResult extends PillarResult {
  vulnerabilities: Vulnerability[];
  attack_success_rate: number;
  jailbreak_detected: boolean;
}

export interface Vulnerability {
  type: string;
  severity: RiskLevel;
  description: string;
  mitigation: string;
}

// Predictive AI Pillars
export interface PredictivePillars {
  explain: ExplainPillarResult;
  actions: ActionsPillarResult;
  fairness: FairnessPillarResult;
  robustness: RobustnessPillarResult;
  trace: TracePillarResult;
  testing: TestingPillarResult;
  imitation: ImitationPillarResult;
  privacy: PrivacyPillarResult;
}

export interface ExplainPillarResult extends PillarResult {
  feature_importance: FeatureImportance[];
  shap_values: number[][];
  explanation_coverage: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
  direction: 'positive' | 'negative';
}

export interface ActionsPillarResult extends PillarResult {
  counterfactuals: Counterfactual[];
  recourse_available: boolean;
}

export interface Counterfactual {
  original: Record<string, unknown>;
  counterfactual: Record<string, unknown>;
  changes_required: string[];
  feasibility_score: number;
}

export interface RobustnessPillarResult extends PillarResult {
  adversarial_accuracy: number;
  perturbation_tolerance: number;
  attack_results: AttackResult[];
}

export interface AttackResult {
  attack_type: string;
  success_rate: number;
  average_perturbation: number;
}

export interface TracePillarResult extends PillarResult {
  lineage_complete: boolean;
  data_sources: DataSource[];
  transformations: Transformation[];
}

export interface DataSource {
  id: string;
  name: string;
  type: string;
  uri: string;
  checksum: string;
}

export interface Transformation {
  id: string;
  name: string;
  type: string;
  parameters: Record<string, unknown>;
  timestamp: string;
}

export interface TestingPillarResult extends PillarResult {
  test_coverage: number;
  metamorphic_tests_passed: number;
  invariant_violations: number;
}

export interface ImitationPillarResult extends PillarResult {
  extraction_detected: boolean;
  watermark_intact: boolean;
  similarity_to_known_attacks: number;
}

// ==================== Compliance Types ====================

export interface ComplianceFramework {
  id: string;
  name: string;
  version: string;
  description: string;
  requirements: ComplianceRequirement[];
}

export interface ComplianceRequirement {
  id: string;
  framework_id: string;
  code: string;
  title: string;
  description: string;
  category: string;
  controls: ComplianceControl[];
}

export interface ComplianceControl {
  id: string;
  requirement_id: string;
  code: string;
  title: string;
  description: string;
  automated: boolean;
  pillar_mapping: string[];
}

export interface ComplianceAssessment {
  id: string;
  model_id: string;
  framework_id: string;
  status: ComplianceStatus;
  score: number;
  assessed_at: string;
  requirement_results: RequirementResult[];
}

export interface RequirementResult {
  requirement_id: string;
  status: ComplianceStatus;
  evidence: string[];
  notes: string;
}

// ==================== Guardrail Types ====================

export interface Guardrail {
  id: string;
  name: string;
  description: string;
  type: GuardrailType;
  config: GuardrailConfig;
  enabled: boolean;
  created_at: string;
}

export type GuardrailType = 
  | 'input_validation'
  | 'output_filtering'
  | 'rate_limiting'
  | 'content_moderation'
  | 'pii_redaction'
  | 'prompt_injection_detection'
  | 'custom';

export interface GuardrailConfig {
  rules: GuardrailRule[];
  thresholds: Record<string, number>;
  actions: GuardrailAction[];
}

export interface GuardrailRule {
  id: string;
  name: string;
  condition: string;
  priority: number;
}

export interface GuardrailAction {
  type: 'block' | 'warn' | 'log' | 'modify' | 'alert';
  config: Record<string, unknown>;
}

// ==================== Dashboard Types ====================

export interface DashboardStats {
  total_models: number;
  total_evaluations: number;
  compliance_score: number;
  risk_distribution: RiskDistribution;
  recent_evaluations: Evaluation[];
  top_issues: Finding[];
}

export interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

// ==================== API Types ====================

export interface ApiResponse<T> {
  data: T;
  meta?: {
    total: number;
    page: number;
    per_page: number;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginationParams {
  page: number;
  per_page: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface FilterParams {
  model_type?: ModelType;
  status?: EvaluationStatus;
  risk_level?: RiskLevel;
  date_from?: string;
  date_to?: string;
  search?: string;
}
