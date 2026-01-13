/**
 * Evaluations Store
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Evaluation, EvaluationConfig, EvaluationStatus, PaginationParams, FilterParams } from '../types';
import { api } from '../api';

export const useEvaluationsStore = defineStore('evaluations', () => {
  // State
  const evaluations = ref<Evaluation[]>([]);
  const currentEvaluation = ref<Evaluation | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const total = ref(0);
  const page = ref(1);
  const perPage = ref(20);

  // Polling state
  const pollingInterval = ref<number | null>(null);
  const pollingIds = ref<Set<string>>(new Set());

  // Getters
  const isLoading = computed(() => loading.value);
  const hasError = computed(() => error.value !== null);
  
  const evaluationsByStatus = computed(() => {
    const grouped: Record<EvaluationStatus, Evaluation[]> = {
      pending: [],
      running: [],
      completed: [],
      failed: [],
      cancelled: [],
    };
    evaluations.value.forEach(evaluation => {
      grouped[evaluation.status].push(evaluation);
    });
    return grouped;
  });

  const runningEvaluations = computed(() => 
    evaluations.value.filter(e => e.status === 'running' || e.status === 'pending')
  );

  const totalPages = computed(() => Math.ceil(total.value / perPage.value));

  // Actions
  async function fetchEvaluations(filters?: FilterParams, pagination?: PaginationParams) {
    loading.value = true;
    error.value = null;
    
    try {
      const params = {
        page: pagination?.page ?? page.value,
        per_page: pagination?.per_page ?? perPage.value,
        ...filters,
      };
      
      const response = await api.evaluations.list(params);
      evaluations.value = response.data;
      
      if (response.meta) {
        total.value = response.meta.total;
        page.value = response.meta.page;
        perPage.value = response.meta.per_page;
      }

      // Start polling for running evaluations
      const runningIds = evaluations.value
        .filter(e => e.status === 'running' || e.status === 'pending')
        .map(e => e.id);
      
      if (runningIds.length > 0) {
        startPolling(runningIds);
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch evaluations';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchEvaluation(id: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await api.evaluations.get(id);
      currentEvaluation.value = response.data;
      
      // Update in list if exists
      const index = evaluations.value.findIndex(e => e.id === id);
      if (index >= 0) {
        evaluations.value[index] = response.data;
      }
      
      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch evaluation';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function startEvaluation(modelId: string, config: EvaluationConfig) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await api.evaluations.start(modelId, config);
      evaluations.value.unshift(response.data);
      
      // Start polling for this evaluation
      startPolling([response.data.id]);
      
      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start evaluation';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function cancelEvaluation(id: string) {
    loading.value = true;
    error.value = null;
    
    try {
      await api.evaluations.cancel(id);
      
      // Update status locally
      const index = evaluations.value.findIndex(e => e.id === id);
      if (index >= 0) {
        evaluations.value[index].status = 'cancelled';
      }
      if (currentEvaluation.value?.id === id) {
        currentEvaluation.value.status = 'cancelled';
      }
      
      // Stop polling for this evaluation
      pollingIds.value.delete(id);
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to cancel evaluation';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function deleteEvaluation(id: string) {
    loading.value = true;
    error.value = null;
    
    try {
      await api.evaluations.delete(id);
      evaluations.value = evaluations.value.filter(e => e.id !== id);
      if (currentEvaluation.value?.id === id) {
        currentEvaluation.value = null;
      }
      pollingIds.value.delete(id);
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete evaluation';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  // Polling for running evaluations
  function startPolling(ids: string[]) {
    ids.forEach(id => pollingIds.value.add(id));
    
    if (pollingInterval.value === null && pollingIds.value.size > 0) {
      pollingInterval.value = window.setInterval(async () => {
        for (const id of pollingIds.value) {
          try {
            const response = await api.evaluations.get(id);
            const evaluation = response.data;
            
            // Update in list
            const index = evaluations.value.findIndex(e => e.id === id);
            if (index >= 0) {
              evaluations.value[index] = evaluation;
            }
            
            // Update current if viewing
            if (currentEvaluation.value?.id === id) {
              currentEvaluation.value = evaluation;
            }
            
            // Stop polling if completed
            if (['completed', 'failed', 'cancelled'].includes(evaluation.status)) {
              pollingIds.value.delete(id);
            }
          } catch (e) {
            console.error(`Failed to poll evaluation ${id}:`, e);
          }
        }
        
        // Stop polling interval if no more running evaluations
        if (pollingIds.value.size === 0 && pollingInterval.value !== null) {
          window.clearInterval(pollingInterval.value);
          pollingInterval.value = null;
        }
      }, 5000); // Poll every 5 seconds
    }
  }

  function stopPolling() {
    if (pollingInterval.value !== null) {
      window.clearInterval(pollingInterval.value);
      pollingInterval.value = null;
    }
    pollingIds.value.clear();
  }

  function clearError() {
    error.value = null;
  }

  function setPage(newPage: number) {
    page.value = newPage;
  }

  return {
    // State
    evaluations,
    currentEvaluation,
    loading,
    error,
    total,
    page,
    perPage,
    // Getters
    isLoading,
    hasError,
    evaluationsByStatus,
    runningEvaluations,
    totalPages,
    // Actions
    fetchEvaluations,
    fetchEvaluation,
    startEvaluation,
    cancelEvaluation,
    deleteEvaluation,
    startPolling,
    stopPolling,
    clearError,
    setPage,
  };
});
