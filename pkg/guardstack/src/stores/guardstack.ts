/**
 * GuardStack Main Store
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { DashboardStats, RiskLevel } from '../types';
import { api } from '../api';

export const useGuardStackStore = defineStore('guardstack', () => {
  // State
  const loading = ref(false);
  const error = ref<string | null>(null);
  const stats = ref<DashboardStats | null>(null);
  const lastUpdated = ref<Date | null>(null);

  // Getters
  const isLoading = computed(() => loading.value);
  const hasError = computed(() => error.value !== null);
  
  const riskScore = computed(() => {
    if (!stats.value) return 0;
    const { risk_distribution } = stats.value;
    const total = risk_distribution.low + risk_distribution.medium + 
                  risk_distribution.high + risk_distribution.critical;
    if (total === 0) return 100;
    
    return Math.round(
      ((risk_distribution.low * 100 + risk_distribution.medium * 70 +
        risk_distribution.high * 30 + risk_distribution.critical * 0) / total)
    );
  });

  const overallRiskLevel = computed((): RiskLevel => {
    const score = riskScore.value;
    if (score >= 80) return 'low';
    if (score >= 60) return 'medium';
    if (score >= 30) return 'high';
    return 'critical';
  });

  // Actions
  async function fetchStats() {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await api.dashboard.getStats();
      stats.value = response.data;
      lastUpdated.value = new Date();
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch stats';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function refresh() {
    await fetchStats();
  }

  function clearError() {
    error.value = null;
  }

  return {
    // State
    loading,
    error,
    stats,
    lastUpdated,
    // Getters
    isLoading,
    hasError,
    riskScore,
    overallRiskLevel,
    // Actions
    fetchStats,
    refresh,
    clearError,
  };
});
