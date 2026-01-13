/**
 * GuardStack Evaluations Store
 * Pinia state management for evaluation data
 */
import { defineStore } from 'pinia';
import type {
  Evaluation,
  EvaluationStatus,
  EvaluationResult,
  EvaluationProgress,
  PaginatedResponse,
} from '../types';

interface EvaluationsState {
  evaluations: Evaluation[];
  currentEvaluation: Evaluation | null;
  results: EvaluationResult[];
  progress: EvaluationProgress | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  filters: {
    status: EvaluationStatus | null;
    modelId: string | null;
    dateRange: { start: string; end: string } | null;
  };
  wsConnection: WebSocket | null;
}

export const useEvaluationsStore = defineStore('evaluations', {
  state: (): EvaluationsState => ({
    evaluations: [],
    currentEvaluation: null,
    results: [],
    progress: null,
    loading: false,
    error: null,
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0,
    },
    filters: {
      status: null,
      modelId: null,
      dateRange: null,
    },
    wsConnection: null,
  }),

  getters: {
    runningEvaluations(state): Evaluation[] {
      return state.evaluations.filter(
        (e) => e.status === EvaluationStatus.RUNNING
      );
    },

    completedEvaluations(state): Evaluation[] {
      return state.evaluations.filter(
        (e) => e.status === EvaluationStatus.COMPLETED
      );
    },

    failedEvaluations(state): Evaluation[] {
      return state.evaluations.filter(
        (e) => e.status === EvaluationStatus.FAILED
      );
    },

    evaluationsByModel(state): Record<string, Evaluation[]> {
      return state.evaluations.reduce(
        (acc, evaluation) => {
          const modelId = evaluation.modelId;
          if (!acc[modelId]) {
            acc[modelId] = [];
          }
          acc[modelId].push(evaluation);
          return acc;
        },
        {} as Record<string, Evaluation[]>
      );
    },

    currentResults(state): EvaluationResult[] {
      return state.results;
    },

    resultsByPillar(state): Record<string, EvaluationResult> {
      return state.results.reduce(
        (acc, result) => {
          acc[result.pillar] = result;
          return acc;
        },
        {} as Record<string, EvaluationResult>
      );
    },

    overallScore(state): number | null {
      if (state.results.length === 0) return null;

      const sum = state.results.reduce((acc, r) => acc + r.score, 0);
      return sum / state.results.length;
    },

    isEvaluationRunning(state): boolean {
      return state.currentEvaluation?.status === EvaluationStatus.RUNNING;
    },
  },

  actions: {
    async fetchEvaluations(page = 1, pageSize = 20) {
      this.loading = true;
      this.error = null;

      try {
        const params = new URLSearchParams({
          page: page.toString(),
          page_size: pageSize.toString(),
        });

        if (this.filters.status) {
          params.append('status', this.filters.status);
        }
        if (this.filters.modelId) {
          params.append('model_id', this.filters.modelId);
        }

        const response = await fetch(`/api/v1/evaluations?${params}`);
        if (!response.ok) throw new Error('Failed to fetch evaluations');

        const data: PaginatedResponse<Evaluation> = await response.json();

        this.evaluations = data.items;
        this.pagination = {
          page: data.page,
          pageSize: data.pageSize,
          total: data.total,
        };
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        console.error('Failed to fetch evaluations:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchEvaluation(id: string) {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch(`/api/v1/evaluations/${id}`);
        if (!response.ok) throw new Error('Failed to fetch evaluation');

        this.currentEvaluation = await response.json();

        // Fetch results if completed
        if (this.currentEvaluation?.status === EvaluationStatus.COMPLETED) {
          await this.fetchResults(id);
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        console.error('Failed to fetch evaluation:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchResults(evaluationId: string) {
      try {
        const response = await fetch(
          `/api/v1/evaluations/${evaluationId}/results`
        );
        if (!response.ok) throw new Error('Failed to fetch results');

        this.results = await response.json();
      } catch (error) {
        console.error('Failed to fetch results:', error);
      }
    },

    async createEvaluation(evaluation: {
      modelId: string;
      name: string;
      pillars: string[];
      config?: Record<string, any>;
    }) {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch('/api/v1/evaluations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(evaluation),
        });

        if (!response.ok) throw new Error('Failed to create evaluation');

        const newEvaluation: Evaluation = await response.json();
        this.evaluations.unshift(newEvaluation);
        return newEvaluation;
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async startEvaluation(id: string) {
      try {
        const response = await fetch(`/api/v1/evaluations/${id}/start`, {
          method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to start evaluation');

        const updated: Evaluation = await response.json();

        const index = this.evaluations.findIndex((e) => e.id === id);
        if (index !== -1) {
          this.evaluations[index] = updated;
        }

        if (this.currentEvaluation?.id === id) {
          this.currentEvaluation = updated;
        }

        // Connect to WebSocket for progress updates
        this.connectToProgress(id);

        return updated;
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        throw error;
      }
    },

    async cancelEvaluation(id: string) {
      try {
        const response = await fetch(`/api/v1/evaluations/${id}/cancel`, {
          method: 'POST',
        });

        if (!response.ok) throw new Error('Failed to cancel evaluation');

        const updated: Evaluation = await response.json();

        const index = this.evaluations.findIndex((e) => e.id === id);
        if (index !== -1) {
          this.evaluations[index] = updated;
        }

        if (this.currentEvaluation?.id === id) {
          this.currentEvaluation = updated;
        }

        this.disconnectFromProgress();

        return updated;
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        throw error;
      }
    },

    connectToProgress(evaluationId: string) {
      // Close existing connection
      this.disconnectFromProgress();

      const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/evaluations/${evaluationId}/progress`;

      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'progress') {
            this.progress = data.progress;
          } else if (data.type === 'result') {
            this.results.push(data.result);
          } else if (data.type === 'completed') {
            if (this.currentEvaluation) {
              this.currentEvaluation.status = EvaluationStatus.COMPLETED;
              this.currentEvaluation.completedAt = data.completedAt;
            }
            this.disconnectFromProgress();
          } else if (data.type === 'error') {
            this.error = data.message;
            if (this.currentEvaluation) {
              this.currentEvaluation.status = EvaluationStatus.FAILED;
              this.currentEvaluation.errorMessage = data.message;
            }
            this.disconnectFromProgress();
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.wsConnection.onclose = () => {
        this.wsConnection = null;
      };
    },

    disconnectFromProgress() {
      if (this.wsConnection) {
        this.wsConnection.close();
        this.wsConnection = null;
      }
      this.progress = null;
    },

    setFilters(filters: Partial<EvaluationsState['filters']>) {
      this.filters = { ...this.filters, ...filters };
    },

    clearFilters() {
      this.filters = {
        status: null,
        modelId: null,
        dateRange: null,
      };
    },

    clearCurrentEvaluation() {
      this.currentEvaluation = null;
      this.results = [];
      this.progress = null;
      this.disconnectFromProgress();
    },
  },
});
