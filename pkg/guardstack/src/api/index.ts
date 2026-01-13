/**
 * GuardStack API Client
 */

import type {
  ApiResponse,
  RegisteredModel,
  Evaluation,
  EvaluationConfig,
  DashboardStats,
  ComplianceAssessment,
  Guardrail,
  PaginationParams,
  FilterParams,
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = `${API_BASE}${path}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

function buildQueryString(params: Record<string, unknown>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : '';
}

// Dashboard API
const dashboard = {
  getStats: () => request<DashboardStats>('/dashboard/stats'),
};

// Models API
const models = {
  list: (params?: PaginationParams & FilterParams) =>
    request<RegisteredModel[]>(`/models${buildQueryString(params ?? {})}`),
  
  get: (id: string) =>
    request<RegisteredModel>(`/models/${id}`),
  
  register: (data: Partial<RegisteredModel>) =>
    request<RegisteredModel>('/models', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: Partial<RegisteredModel>) =>
    request<RegisteredModel>(`/models/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  delete: (id: string) =>
    request<void>(`/models/${id}`, { method: 'DELETE' }),
};

// Evaluations API
const evaluations = {
  list: (params?: PaginationParams & FilterParams) =>
    request<Evaluation[]>(`/evaluations${buildQueryString(params ?? {})}`),
  
  get: (id: string) =>
    request<Evaluation>(`/evaluations/${id}`),
  
  start: (modelId: string, config: EvaluationConfig) =>
    request<Evaluation>('/evaluations', {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId, config }),
    }),
  
  cancel: (id: string) =>
    request<void>(`/evaluations/${id}/cancel`, { method: 'POST' }),
  
  delete: (id: string) =>
    request<void>(`/evaluations/${id}`, { method: 'DELETE' }),
  
  getReport: (id: string, format: 'html' | 'json' | 'pdf' = 'json') =>
    request<unknown>(`/evaluations/${id}/report?format=${format}`),
};

// Compliance API
const compliance = {
  listFrameworks: () =>
    request<{ id: string; name: string; version: string }[]>('/compliance/frameworks'),
  
  getFramework: (id: string) =>
    request<unknown>(`/compliance/frameworks/${id}`),
  
  assess: (modelId: string, frameworkId: string) =>
    request<ComplianceAssessment>('/compliance/assess', {
      method: 'POST',
      body: JSON.stringify({ model_id: modelId, framework_id: frameworkId }),
    }),
  
  getAssessment: (id: string) =>
    request<ComplianceAssessment>(`/compliance/assessments/${id}`),
  
  listAssessments: (modelId?: string) =>
    request<ComplianceAssessment[]>(
      `/compliance/assessments${modelId ? `?model_id=${modelId}` : ''}`
    ),
};

// Guardrails API
const guardrails = {
  list: () =>
    request<Guardrail[]>('/guardrails'),
  
  get: (id: string) =>
    request<Guardrail>(`/guardrails/${id}`),
  
  create: (data: Partial<Guardrail>) =>
    request<Guardrail>('/guardrails', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: Partial<Guardrail>) =>
    request<Guardrail>(`/guardrails/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  delete: (id: string) =>
    request<void>(`/guardrails/${id}`, { method: 'DELETE' }),
  
  toggle: (id: string, enabled: boolean) =>
    request<Guardrail>(`/guardrails/${id}/toggle`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),
};

// Connectors API
const connectors = {
  list: () =>
    request<{ id: string; name: string; type: string; status: string }[]>('/connectors'),
  
  get: (id: string) =>
    request<unknown>(`/connectors/${id}`),
  
  test: (id: string) =>
    request<{ success: boolean; latency_ms: number }>(`/connectors/${id}/test`, {
      method: 'POST',
    }),
  
  configure: (id: string, config: Record<string, unknown>) =>
    request<unknown>(`/connectors/${id}/configure`, {
      method: 'POST',
      body: JSON.stringify(config),
    }),
};

export const api = {
  dashboard,
  models,
  evaluations,
  compliance,
  guardrails,
  connectors,
};

export default api;
