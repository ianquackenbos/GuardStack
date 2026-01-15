/**
 * Vitest Test Setup
 * Global test configuration and mocks
 */
import { config } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, vi } from 'vitest';

// Create fresh Pinia instance before each test
beforeEach(() => {
  setActivePinia(createPinia());
});

// Mock global fetch
global.fetch = vi.fn();

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Configure Vue Test Utils
config.global.stubs = {
  teleport: true,
  transition: false,
};

// Helper to mock successful API responses
export function mockFetch(data: unknown, ok = true) {
  (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
    ok,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    status: ok ? 200 : 400,
  });
}

// Helper to mock failed API responses
export function mockFetchError(message = 'API Error') {
  (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
    new Error(message)
  );
}

// Helper to create mock model data
export function createMockModel(overrides = {}) {
  return {
    id: 'model-1',
    name: 'Test Model',
    description: 'A test model',
    type: 'llm',
    provider: 'openai',
    version: '1.0',
    riskLevel: 'low',
    tags: ['test', 'demo'],
    scores: {
      overall: 85,
      security: 90,
      fairness: 80,
      privacy: 85,
      robustness: 85,
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

// Helper to create mock evaluation data
export function createMockEvaluation(overrides = {}) {
  return {
    id: 'eval-1',
    modelId: 'model-1',
    status: 'completed',
    type: 'comprehensive',
    scores: {
      overall: 85,
      pillars: {
        security: 90,
        fairness: 80,
        privacy: 85,
        robustness: 85,
      },
    },
    findings: [],
    startedAt: new Date().toISOString(),
    completedAt: new Date().toISOString(),
    ...overrides,
  };
}
