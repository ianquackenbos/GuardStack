/**
 * Evaluations Store Tests
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useEvaluationsStore } from '../../store/evaluations';
import { mockFetch, createMockEvaluation } from '../setup';

// Mock WebSocket
class MockWebSocket {
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: ((error: unknown) => void) | null = null;
  onclose: (() => void) | null = null;
  
  constructor(public url: string) {}
  
  close() {
    if (this.onclose) this.onclose();
  }
  
  send(data: string) {}
  
  // Helper to simulate message
  simulateMessage(data: unknown) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }
}

// Store original WebSocket
const OriginalWebSocket = global.WebSocket;

describe('useEvaluationsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    // @ts-ignore
    global.WebSocket = MockWebSocket;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    global.WebSocket = OriginalWebSocket;
  });

  describe('initial state', () => {
    it('has empty evaluations array', () => {
      const store = useEvaluationsStore();
      expect(store.evaluations).toEqual([]);
    });

    it('has null currentEvaluation', () => {
      const store = useEvaluationsStore();
      expect(store.currentEvaluation).toBeNull();
    });

    it('has empty results', () => {
      const store = useEvaluationsStore();
      expect(store.results).toEqual([]);
    });

    it('has null progress', () => {
      const store = useEvaluationsStore();
      expect(store.progress).toBeNull();
    });

    it('has null wsConnection', () => {
      const store = useEvaluationsStore();
      expect(store.wsConnection).toBeNull();
    });
  });

  describe('getters', () => {
    it('runningEvaluations filters by running status', () => {
      const store = useEvaluationsStore();
      store.evaluations = [
        createMockEvaluation({ id: '1', status: 'running' }),
        createMockEvaluation({ id: '2', status: 'completed' }),
        createMockEvaluation({ id: '3', status: 'running' }),
      ];

      expect(store.runningEvaluations).toHaveLength(2);
    });

    it('completedEvaluations filters by completed status', () => {
      const store = useEvaluationsStore();
      store.evaluations = [
        createMockEvaluation({ id: '1', status: 'completed' }),
        createMockEvaluation({ id: '2', status: 'running' }),
      ];

      expect(store.completedEvaluations).toHaveLength(1);
      expect(store.completedEvaluations[0].id).toBe('1');
    });

    it('failedEvaluations filters by failed status', () => {
      const store = useEvaluationsStore();
      store.evaluations = [
        createMockEvaluation({ id: '1', status: 'failed' }),
        createMockEvaluation({ id: '2', status: 'completed' }),
      ];

      expect(store.failedEvaluations).toHaveLength(1);
      expect(store.failedEvaluations[0].id).toBe('1');
    });

    it('evaluationsByModel groups evaluations', () => {
      const store = useEvaluationsStore();
      store.evaluations = [
        createMockEvaluation({ id: '1', modelId: 'model-a' }),
        createMockEvaluation({ id: '2', modelId: 'model-b' }),
        createMockEvaluation({ id: '3', modelId: 'model-a' }),
      ];

      expect(store.evaluationsByModel['model-a']).toHaveLength(2);
      expect(store.evaluationsByModel['model-b']).toHaveLength(1);
    });

    it('overallScore calculates average', () => {
      const store = useEvaluationsStore();
      store.results = [
        { pillar: 'security', score: 80 },
        { pillar: 'fairness', score: 90 },
        { pillar: 'privacy', score: 70 },
      ] as any;

      expect(store.overallScore).toBe(80);
    });

    it('overallScore returns null when no results', () => {
      const store = useEvaluationsStore();
      expect(store.overallScore).toBeNull();
    });

    it('isEvaluationRunning checks current evaluation status', () => {
      const store = useEvaluationsStore();
      store.currentEvaluation = createMockEvaluation({ status: 'running' }) as any;

      expect(store.isEvaluationRunning).toBe(true);

      store.currentEvaluation = createMockEvaluation({ status: 'completed' }) as any;
      expect(store.isEvaluationRunning).toBe(false);
    });
  });

  describe('actions', () => {
    it('fetchEvaluations updates evaluations on success', async () => {
      const store = useEvaluationsStore();
      const mockData = {
        items: [createMockEvaluation()],
        page: 1,
        pageSize: 20,
        total: 1,
      };

      mockFetch(mockData);

      await store.fetchEvaluations();

      expect(store.evaluations).toHaveLength(1);
      expect(store.pagination.total).toBe(1);
      expect(store.loading).toBe(false);
    });

    it('fetchEvaluations includes filters in request', async () => {
      const store = useEvaluationsStore();
      store.filters.status = 'running' as any;
      store.filters.modelId = 'model-1';

      const mockData = {
        items: [],
        page: 1,
        pageSize: 20,
        total: 0,
      };

      mockFetch(mockData);

      await store.fetchEvaluations();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('status=running')
      );
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('model_id=model-1')
      );
    });

    it('fetchEvaluation sets currentEvaluation', async () => {
      const store = useEvaluationsStore();
      const mockEval = createMockEvaluation({ id: 'test-id', status: 'running' });

      mockFetch(mockEval);

      await store.fetchEvaluation('test-id');

      expect(store.currentEvaluation).toEqual(mockEval);
    });

    it('fetchEvaluation fetches results when completed', async () => {
      const store = useEvaluationsStore();
      const mockEval = createMockEvaluation({ id: 'test-id', status: 'completed' });
      const mockResults = [{ pillar: 'security', score: 85 }];

      mockFetch(mockEval);
      mockFetch(mockResults);

      await store.fetchEvaluation('test-id');

      expect(global.fetch).toHaveBeenCalledTimes(2);
      expect(store.results).toEqual(mockResults);
    });

    it('createEvaluation adds to list and returns evaluation', async () => {
      const store = useEvaluationsStore();
      const newEval = createMockEvaluation({ id: 'new-id' });

      mockFetch(newEval);

      const result = await store.createEvaluation({
        modelId: 'model-1',
        name: 'Test Eval',
        pillars: ['security'],
      });

      expect(result).toEqual(newEval);
      expect(store.evaluations).toContainEqual(newEval);
    });

    it('startEvaluation updates evaluation and connects to WebSocket', async () => {
      const store = useEvaluationsStore();
      const existingEval = createMockEvaluation({ id: 'test-id', status: 'pending' });
      const updatedEval = createMockEvaluation({ id: 'test-id', status: 'running' });
      store.evaluations = [existingEval as any];

      mockFetch(updatedEval);

      await store.startEvaluation('test-id');

      expect(store.evaluations[0].status).toBe('running');
      expect(store.wsConnection).not.toBeNull();
    });

    it('cancelEvaluation updates evaluation and disconnects WebSocket', async () => {
      const store = useEvaluationsStore();
      const runningEval = createMockEvaluation({ id: 'test-id', status: 'running' });
      const cancelledEval = createMockEvaluation({ id: 'test-id', status: 'cancelled' });
      store.evaluations = [runningEval as any];
      
      // Simulate existing connection
      store.wsConnection = new MockWebSocket('') as any;

      mockFetch(cancelledEval);

      await store.cancelEvaluation('test-id');

      expect(store.evaluations[0].status).toBe('cancelled');
      expect(store.wsConnection).toBeNull();
    });

    it('connectToProgress creates WebSocket and handles messages', () => {
      const store = useEvaluationsStore();
      store.currentEvaluation = createMockEvaluation({ id: 'test-id' }) as any;

      store.connectToProgress('test-id');

      expect(store.wsConnection).not.toBeNull();
      expect((store.wsConnection as MockWebSocket).url).toContain('test-id');

      // Simulate progress message
      (store.wsConnection as MockWebSocket).simulateMessage({
        type: 'progress',
        progress: { percent: 50, currentPillar: 'security' },
      });

      expect(store.progress).toEqual({ percent: 50, currentPillar: 'security' });
    });

    it('connectToProgress handles result messages', () => {
      const store = useEvaluationsStore();
      store.currentEvaluation = createMockEvaluation({ id: 'test-id' }) as any;

      store.connectToProgress('test-id');

      (store.wsConnection as MockWebSocket).simulateMessage({
        type: 'result',
        result: { pillar: 'security', score: 85 },
      });

      expect(store.results).toHaveLength(1);
      expect(store.results[0].score).toBe(85);
    });

    it('connectToProgress handles completed messages', () => {
      const store = useEvaluationsStore();
      store.currentEvaluation = createMockEvaluation({ id: 'test-id', status: 'running' }) as any;

      store.connectToProgress('test-id');

      (store.wsConnection as MockWebSocket).simulateMessage({
        type: 'completed',
        completedAt: '2024-01-01T00:00:00Z',
      });

      expect(store.currentEvaluation?.status).toBe('completed');
      expect(store.wsConnection).toBeNull();
    });

    it('disconnectFromProgress closes connection and clears state', () => {
      const store = useEvaluationsStore();
      const mockWs = new MockWebSocket('');
      const closeSpy = vi.spyOn(mockWs, 'close');
      
      store.wsConnection = mockWs as any;
      store.progress = { percent: 50 } as any;

      store.disconnectFromProgress();

      expect(closeSpy).toHaveBeenCalled();
      expect(store.wsConnection).toBeNull();
      expect(store.progress).toBeNull();
    });

    it('setFilters updates filter values', () => {
      const store = useEvaluationsStore();

      store.setFilters({ modelId: 'model-1', status: 'running' as any });

      expect(store.filters.modelId).toBe('model-1');
      expect(store.filters.status).toBe('running');
    });

    it('clearFilters resets all filters', () => {
      const store = useEvaluationsStore();
      store.filters = {
        status: 'running' as any,
        modelId: 'model-1',
        dateRange: { start: '2024-01-01', end: '2024-12-31' },
      };

      store.clearFilters();

      expect(store.filters).toEqual({
        status: null,
        modelId: null,
        dateRange: null,
      });
    });

    it('clearCurrentEvaluation resets evaluation state', () => {
      const store = useEvaluationsStore();
      store.currentEvaluation = createMockEvaluation() as any;
      store.results = [{ pillar: 'security', score: 85 }] as any;
      store.progress = { percent: 50 } as any;
      store.wsConnection = new MockWebSocket('') as any;

      store.clearCurrentEvaluation();

      expect(store.currentEvaluation).toBeNull();
      expect(store.results).toEqual([]);
      expect(store.progress).toBeNull();
      expect(store.wsConnection).toBeNull();
    });
  });
});
