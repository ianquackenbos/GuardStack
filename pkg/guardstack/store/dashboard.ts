/**
 * GuardStack Dashboard Store
 * Pinia state management for dashboard data
 */
import { defineStore } from 'pinia';
import type {
  DashboardStats,
  RiskDistribution,
  TrendDataPoint,
  Evaluation,
  Model,
  RiskLevel,
} from '../types';

interface DashboardState {
  stats: DashboardStats | null;
  recentModels: Model[];
  recentEvaluations: Evaluation[];
  trendData: TrendDataPoint[];
  alerts: DashboardAlert[];
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

interface DashboardAlert {
  id: string;
  type: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  modelId?: string;
  evaluationId?: string;
  createdAt: string;
  read: boolean;
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): DashboardState => ({
    stats: null,
    recentModels: [],
    recentEvaluations: [],
    trendData: [],
    alerts: [],
    loading: false,
    error: null,
    lastUpdated: null,
  }),

  getters: {
    riskSummary(state): { pass: number; warn: number; fail: number } {
      if (!state.stats) {
        return { pass: 0, warn: 0, fail: 0 };
      }

      const { riskDistribution } = state.stats;
      return {
        pass: riskDistribution.minimal + riskDistribution.low,
        warn: riskDistribution.medium,
        fail: riskDistribution.high + riskDistribution.critical,
      };
    },

    averageScore(state): number {
      return state.stats?.averageScore ?? 0;
    },

    modelsAtRisk(state): number {
      return state.stats?.modelsAtRisk ?? 0;
    },

    unreadAlerts(state): DashboardAlert[] {
      return state.alerts.filter((a) => !a.read);
    },

    criticalAlerts(state): DashboardAlert[] {
      return state.alerts.filter((a) => a.type === 'critical');
    },

    hasData(state): boolean {
      return state.stats !== null;
    },

    scoreChange(state): number {
      if (state.trendData.length < 2) return 0;

      const latest = state.trendData[state.trendData.length - 1];
      const previous = state.trendData[state.trendData.length - 2];

      return latest.averageScore - previous.averageScore;
    },

    chartData(state) {
      return {
        labels: state.trendData.map((d) =>
          new Date(d.date).toLocaleDateString()
        ),
        datasets: [
          {
            label: 'Average Score',
            data: state.trendData.map((d) => d.averageScore * 100),
            borderColor: '#10b981',
            fill: false,
          },
        ],
      };
    },

    riskChartData(state) {
      if (!state.stats) return null;

      const { riskDistribution } = state.stats;
      return {
        labels: ['Critical', 'High', 'Medium', 'Low', 'Minimal'],
        datasets: [
          {
            data: [
              riskDistribution.critical,
              riskDistribution.high,
              riskDistribution.medium,
              riskDistribution.low,
              riskDistribution.minimal,
            ],
            backgroundColor: [
              '#ef4444',
              '#f97316',
              '#eab308',
              '#22c55e',
              '#10b981',
            ],
          },
        ],
      };
    },
  },

  actions: {
    async fetchDashboard() {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch('/api/v1/dashboard');
        if (!response.ok) throw new Error('Failed to fetch dashboard data');

        const data = await response.json();

        this.stats = {
          totalModels: data.total_models,
          totalEvaluations: data.total_evaluations,
          modelsAtRisk: data.models_at_risk,
          averageScore: data.average_score,
          riskDistribution: data.risk_distribution,
          recentEvaluations: data.recent_evaluations,
          trendData: data.trend_data,
        };

        this.recentModels = data.recent_models || [];
        this.recentEvaluations = data.recent_evaluations || [];
        this.trendData = data.trend_data || [];
        this.lastUpdated = new Date().toISOString();
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        console.error('Failed to fetch dashboard:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchTrendData(days = 30) {
      try {
        const response = await fetch(`/api/v1/dashboard/trends?days=${days}`);
        if (!response.ok) throw new Error('Failed to fetch trend data');

        this.trendData = await response.json();
      } catch (error) {
        console.error('Failed to fetch trend data:', error);
      }
    },

    async fetchAlerts() {
      try {
        const response = await fetch('/api/v1/dashboard/alerts');
        if (!response.ok) throw new Error('Failed to fetch alerts');

        this.alerts = await response.json();
      } catch (error) {
        console.error('Failed to fetch alerts:', error);
      }
    },

    async markAlertRead(alertId: string) {
      const alert = this.alerts.find((a) => a.id === alertId);
      if (alert) {
        alert.read = true;

        try {
          await fetch(`/api/v1/dashboard/alerts/${alertId}/read`, {
            method: 'POST',
          });
        } catch (error) {
          console.error('Failed to mark alert read:', error);
        }
      }
    },

    async markAllAlertsRead() {
      this.alerts.forEach((a) => (a.read = true));

      try {
        await fetch('/api/v1/dashboard/alerts/read-all', {
          method: 'POST',
        });
      } catch (error) {
        console.error('Failed to mark all alerts read:', error);
      }
    },

    addAlert(alert: Omit<DashboardAlert, 'id' | 'createdAt' | 'read'>) {
      this.alerts.unshift({
        ...alert,
        id: crypto.randomUUID(),
        createdAt: new Date().toISOString(),
        read: false,
      });
    },

    clearError() {
      this.error = null;
    },
  },
});
