/**
 * GuardStack TypeScript Type Definitions
 */

// Enums
export enum ModelType {
  PREDICTIVE = 'predictive',
  GENERATIVE = 'generative',
  AGENTIC = 'agentic',
}

export enum EvaluationStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum RiskLevel {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  MINIMAL = 'minimal',
}

export enum ConnectorType {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  AZURE_OPENAI = 'azure_openai',
  BEDROCK = 'bedrock',
  VERTEX = 'vertex',
  HUGGINGFACE = 'huggingface',
  OLLAMA = 'ollama',
  CUSTOM = 'custom',
}

// Predictive AI Pillars
export type PredictivePillar =
  | 'explain'
  | 'actions'
  | 'fairness'
  | 'robustness'
  | 'trace'
  | 'testing'
  | 'imitation'
  | 'privacy';

// GenAI Pillars
export type GenAIPillar = 'privacy' | 'toxicity' | 'fairness' | 'security';

// Model Types
export interface Model {
  id: string;
  name: string;
  version: string;
  type: ModelType;
  description?: string;
  framework?: string;
  taskType?: string;
  metadata: Record<string, any>;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  latestEvaluation?: EvaluationSummary;
  riskLevel?: RiskLevel;
  overallScore?: number;
}

export interface EvaluationSummary {
  id: string;
  status: EvaluationStatus;
  overallScore?: number;
  riskLevel?: RiskLevel;
  completedAt?: string;
}

// Evaluation Types
export interface Evaluation {
  id: string;
  modelId: string;
  model?: Model;
  name: string;
  status: EvaluationStatus;
  pillars: string[];
  config: EvaluationConfig;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string;
  createdAt: string;
  createdBy?: string;
  results?: EvaluationResult[];
  progress?: EvaluationProgress;
}

export interface EvaluationConfig {
  datasetPath?: string;
  sampleSize?: number;
  thresholds?: Record<string, number>;
  options?: Record<string, any>;
}

export interface EvaluationResult {
  id: string;
  evaluationId: string;
  pillar: string;
  score: number;
  confidence: number;
  riskLevel: RiskLevel;
  metrics: Record<string, any>;
  details: Record<string, any>;
  recommendations: string[];
  createdAt: string;
}

export interface EvaluationProgress {
  currentPillar?: string;
  completedPillars: string[];
  totalPillars: number;
  percentComplete: number;
  currentStep?: string;
  estimatedTimeRemaining?: number;
}

// Pillar Score for display
export interface PillarScore {
  pillar: string;
  score: number;
  riskLevel: RiskLevel;
  confidence: number;
  trend?: 'up' | 'down' | 'stable';
  previousScore?: number;
}

// Dashboard Types
export interface DashboardStats {
  totalModels: number;
  totalEvaluations: number;
  modelsAtRisk: number;
  averageScore: number;
  riskDistribution: RiskDistribution;
  recentEvaluations: Evaluation[];
  trendData: TrendDataPoint[];
}

export interface RiskDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
  minimal: number;
}

export interface TrendDataPoint {
  date: string;
  averageScore: number;
  evaluationCount: number;
  riskBreakdown: RiskDistribution;
}

// Connector Types
export interface Connector {
  id: string;
  name: string;
  type: ConnectorType;
  config: Record<string, any>;
  isActive: boolean;
  lastHealthCheck?: string;
  healthStatus?: 'healthy' | 'unhealthy' | 'unknown';
  createdAt: string;
  updatedAt: string;
}

// Guardrail Types
export interface GuardrailPolicy {
  id: string;
  name: string;
  description?: string;
  version: string;
  rules: GuardrailRule[];
  isActive: boolean;
  priority: number;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
}

export interface GuardrailRule {
  name: string;
  conditions: GuardrailCondition[];
  action: 'allow' | 'block' | 'modify' | 'warn' | 'audit';
  message?: string;
  priority: number;
  enabled: boolean;
}

export interface GuardrailCondition {
  field: string;
  operator: string;
  value: any;
  caseSensitive?: boolean;
}

export interface GuardrailEvent {
  id: string;
  policyId?: string;
  connectorId?: string;
  action: string;
  triggeredRules: string[];
  reasons: string[];
  metadata: Record<string, any>;
  createdAt: string;
}

// Compliance Types
export interface ComplianceReport {
  id: string;
  modelId: string;
  framework: string;
  overallScore?: number;
  status: 'compliant' | 'partial' | 'non_compliant' | 'not_assessed';
  controlsAssessed: number;
  controlsPassed: number;
  controlsFailed: number;
  findings: ComplianceFinding[];
  recommendations: string[];
  generatedAt: string;
  generatedBy?: string;
}

export interface ComplianceFinding {
  controlId: string;
  controlName: string;
  status: 'passed' | 'failed' | 'partial' | 'not_applicable';
  evidence: string[];
  gaps: string[];
  severity: RiskLevel;
}

export interface ComplianceFramework {
  id: string;
  name: string;
  description: string;
  version: string;
  controls: ComplianceControl[];
}

export interface ComplianceControl {
  id: string;
  name: string;
  description: string;
  category: string;
  requirements: string[];
}

// SPM Types
export interface SPMInventoryItem {
  id: string;
  name: string;
  modelType?: string;
  source?: string;
  license?: string;
  riskScore?: number;
  vulnerabilities: SPMVulnerability[];
  dependencies: SPMDependency[];
  lastScannedAt?: string;
  createdAt: string;
}

export interface SPMVulnerability {
  id: string;
  severity: RiskLevel;
  title: string;
  description: string;
  remediation?: string;
  cveId?: string;
}

export interface SPMDependency {
  name: string;
  version: string;
  license?: string;
  riskLevel?: RiskLevel;
}

// Agentic Types
export interface AgentTool {
  id: string;
  name: string;
  description?: string;
  category: string;
  schema: Record<string, any>;
  riskLevel: RiskLevel;
  requiresApproval: boolean;
  isActive: boolean;
}

export interface AgentSession {
  id: string;
  modelId?: string;
  connectorId?: string;
  sessionType: string;
  status: string;
  totalSteps: number;
  totalToolCalls: number;
  errorCount: number;
  startedAt: string;
  endedAt?: string;
}

export interface AgentToolCall {
  id: string;
  sessionId: string;
  toolName: string;
  stepNumber: number;
  inputParameters: Record<string, any>;
  outputResult?: Record<string, any>;
  wasBlocked: boolean;
  blockReason?: string;
  executionTimeMs?: number;
  createdAt: string;
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// Chart Data Types
export interface RadarChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
  }[];
}

export interface LineChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    borderColor?: string;
    fill?: boolean;
  }[];
}

export interface BarChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
  }[];
}
