/**
 * API Service for GuardStack
 * 
 * Provides HTTP client methods for interacting with the GuardStack backend.
 */

import type {
  Model,
  Evaluation,
  EvaluationResult,
  Connector,
  Guardrail,
  ComplianceReport,
  DashboardMetrics,
  CreateModelRequest,
  CreateEvaluationRequest,
  CreateConnectorRequest,
  CreateGuardrailRequest,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

class ApiError extends Error {
  status: number;
  data?: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  // Add auth token if available
  const token = localStorage.getItem('guardstack_token');
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { message: response.statusText };
    }
    
    throw new ApiError(
      errorData.message || 'An error occurred',
      response.status,
      errorData
    );
  }
  
  // Handle no-content responses
  if (response.status === 204) {
    return {} as T;
  }
  
  return response.json();
}

// Models API
export const modelsApi = {
  list: (params?: { page?: number; page_size?: number; type?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.type) searchParams.set('type', params.type);
    
    const query = searchParams.toString();
    return request<PaginatedResponse<Model>>(`/models${query ? `?${query}` : ''}`);
  },
  
  get: (id: string) => request<Model>(`/models/${id}`),
  
  create: (data: CreateModelRequest) =>
    request<Model>('/models', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: Partial<CreateModelRequest>) =>
    request<Model>(`/models/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  
  delete: (id: string) =>
    request<void>(`/models/${id}`, { method: 'DELETE' }),
  
  getEvaluations: (id: string) =>
    request<Evaluation[]>(`/models/${id}/evaluations`),
  
  getLatestResults: (id: string) =>
    request<EvaluationResult>(`/models/${id}/results/latest`),
};

// Evaluations API
export const evaluationsApi = {
  list: (params?: {
    page?: number;
    page_size?: number;
    model_id?: string;
    status?: string;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.model_id) searchParams.set('model_id', params.model_id);
    if (params?.status) searchParams.set('status', params.status);
    
    const query = searchParams.toString();
    return request<PaginatedResponse<Evaluation>>(`/evaluations${query ? `?${query}` : ''}`);
  },
  
  get: (id: string) => request<Evaluation>(`/evaluations/${id}`),
  
  create: (data: CreateEvaluationRequest) =>
    request<Evaluation>('/evaluations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  start: (id: string) =>
    request<Evaluation>(`/evaluations/${id}/start`, { method: 'POST' }),
  
  cancel: (id: string) =>
    request<Evaluation>(`/evaluations/${id}/cancel`, { method: 'POST' }),
  
  getResults: (id: string) =>
    request<EvaluationResult>(`/evaluations/${id}/results`),
  
  getPillarResults: (id: string, pillar: string) =>
    request<any>(`/evaluations/${id}/results/${pillar}`),
  
  delete: (id: string) =>
    request<void>(`/evaluations/${id}`, { method: 'DELETE' }),
};

// Dashboard API
export const dashboardApi = {
  getMetrics: () => request<DashboardMetrics>('/dashboard/metrics'),
  
  getRecentEvaluations: (limit?: number) =>
    request<Evaluation[]>(`/dashboard/recent-evaluations${limit ? `?limit=${limit}` : ''}`),
  
  getTrends: (period?: string) =>
    request<any>(`/dashboard/trends${period ? `?period=${period}` : ''}`),
  
  getAlerts: () => request<any[]>('/dashboard/alerts'),
};

// Compliance API
export const complianceApi = {
  getStatus: (modelId?: string) => {
    const query = modelId ? `?model_id=${modelId}` : '';
    return request<any>(`/compliance/status${query}`);
  },
  
  getEuAiActStatus: (modelId: string) =>
    request<any>(`/compliance/eu-ai-act/${modelId}`),
  
  generateReport: (data: { model_id: string; framework: string; format?: string }) =>
    request<ComplianceReport>('/compliance/reports', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  listReports: (params?: { model_id?: string; framework?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.model_id) searchParams.set('model_id', params.model_id);
    if (params?.framework) searchParams.set('framework', params.framework);
    
    const query = searchParams.toString();
    return request<ComplianceReport[]>(`/compliance/reports${query ? `?${query}` : ''}`);
  },
  
  getReport: (id: string) => request<ComplianceReport>(`/compliance/reports/${id}`),
  
  downloadReport: (id: string, format: string = 'pdf') =>
    `${BASE_URL}/compliance/reports/${id}/download?format=${format}`,
};

// Connectors API
export const connectorsApi = {
  list: () => request<Connector[]>('/connectors'),
  
  get: (id: string) => request<Connector>(`/connectors/${id}`),
  
  create: (data: CreateConnectorRequest) =>
    request<Connector>('/connectors', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: Partial<CreateConnectorRequest>) =>
    request<Connector>(`/connectors/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  
  delete: (id: string) =>
    request<void>(`/connectors/${id}`, { method: 'DELETE' }),
  
  test: (id: string) =>
    request<{ success: boolean; message?: string }>(`/connectors/${id}/test`, {
      method: 'POST',
    }),
  
  getProviders: () => request<string[]>('/connectors/providers'),
};

// Guardrails API
export const guardrailsApi = {
  list: () => request<Guardrail[]>('/guardrails'),
  
  get: (id: string) => request<Guardrail>(`/guardrails/${id}`),
  
  create: (data: CreateGuardrailRequest) =>
    request<Guardrail>('/guardrails', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  update: (id: string, data: Partial<CreateGuardrailRequest>) =>
    request<Guardrail>(`/guardrails/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  
  delete: (id: string) =>
    request<void>(`/guardrails/${id}`, { method: 'DELETE' }),
  
  test: (id: string, input: string) =>
    request<{ passed: boolean; output?: string; reason?: string }>(
      `/guardrails/${id}/test`,
      {
        method: 'POST',
        body: JSON.stringify({ input }),
      }
    ),
  
  getTemplates: () => request<any[]>('/guardrails/templates'),
};

// Export all APIs
export const api = {
  models: modelsApi,
  evaluations: evaluationsApi,
  dashboard: dashboardApi,
  compliance: complianceApi,
  connectors: connectorsApi,
  guardrails: guardrailsApi,
};

export { ApiError };
export default api;
