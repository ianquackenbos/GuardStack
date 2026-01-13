<template>
  <div class="guardstack-dashboard">
    <header class="dashboard-header">
      <h1>GuardStack Dashboard</h1>
      <div class="header-actions">
        <button class="btn btn-primary" @click="refresh">
          <i class="icon icon-refresh" :class="{ 'icon-spin': isLoading }" />
          Refresh
        </button>
      </div>
    </header>

    <div v-if="error" class="alert alert-error">
      {{ error }}
      <button class="btn btn-sm" @click="clearError">Dismiss</button>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">
          <i class="icon icon-cube" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats?.total_models ?? 0 }}</div>
          <div class="stat-label">Registered Models</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <i class="icon icon-clipboard-check" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats?.total_evaluations ?? 0 }}</div>
          <div class="stat-label">Total Evaluations</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">
          <i class="icon icon-shield" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats?.compliance_score ?? 0 }}%</div>
          <div class="stat-label">Compliance Score</div>
        </div>
      </div>

      <div class="stat-card" :class="`risk-${overallRiskLevel}`">
        <div class="stat-icon">
          <i class="icon icon-warning" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ riskScore }}%</div>
          <div class="stat-label">Risk Score</div>
        </div>
      </div>
    </div>

    <!-- Risk Distribution -->
    <div class="section">
      <h2>Risk Distribution</h2>
      <div class="risk-distribution">
        <div class="risk-bar">
          <div
            v-for="level in riskLevels"
            :key="level.name"
            class="risk-segment"
            :class="`risk-${level.name}`"
            :style="{ width: `${getRiskPercentage(level.name)}%` }"
            :title="`${level.label}: ${getRiskCount(level.name)}`"
          />
        </div>
        <div class="risk-legend">
          <div v-for="level in riskLevels" :key="level.name" class="legend-item">
            <span class="legend-color" :class="`risk-${level.name}`" />
            <span class="legend-label">{{ level.label }}</span>
            <span class="legend-count">{{ getRiskCount(level.name) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Evaluations -->
    <div class="section">
      <h2>Recent Evaluations</h2>
      <table class="table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Type</th>
            <th>Status</th>
            <th>Score</th>
            <th>Risk</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="evaluation in recentEvaluations" :key="evaluation.id">
            <td>{{ evaluation.model_id }}</td>
            <td>
              <span class="badge" :class="`badge-${evaluation.evaluation_type}`">
                {{ evaluation.evaluation_type }}
              </span>
            </td>
            <td>
              <span class="status" :class="`status-${evaluation.status}`">
                {{ evaluation.status }}
              </span>
            </td>
            <td>{{ evaluation.overall_score }}%</td>
            <td>
              <span class="risk-badge" :class="`risk-${evaluation.risk_level}`">
                {{ evaluation.risk_level }}
              </span>
            </td>
            <td>{{ formatDate(evaluation.started_at) }}</td>
          </tr>
          <tr v-if="!recentEvaluations.length">
            <td colspan="6" class="text-center">No evaluations yet</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Top Issues -->
    <div class="section">
      <h2>Top Issues</h2>
      <div class="issues-list">
        <div
          v-for="issue in topIssues"
          :key="issue.id"
          class="issue-card"
          :class="`severity-${issue.severity}`"
        >
          <div class="issue-header">
            <span class="issue-type">{{ issue.type }}</span>
            <span class="issue-severity" :class="`severity-${issue.severity}`">
              {{ issue.severity }}
            </span>
          </div>
          <div class="issue-title">{{ issue.title }}</div>
          <div class="issue-description">{{ issue.description }}</div>
          <div class="issue-recommendation">
            <strong>Recommendation:</strong> {{ issue.recommendation }}
          </div>
        </div>
        <div v-if="!topIssues.length" class="no-issues">
          <i class="icon icon-check-circle" />
          <span>No critical issues found</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useGuardStackStore } from '../stores/guardstack';
import type { RiskLevel } from '../types';

const store = useGuardStackStore();

const isLoading = computed(() => store.isLoading);
const error = computed(() => store.error);
const stats = computed(() => store.stats);
const riskScore = computed(() => store.riskScore);
const overallRiskLevel = computed(() => store.overallRiskLevel);

const recentEvaluations = computed(() => stats.value?.recent_evaluations ?? []);
const topIssues = computed(() => stats.value?.top_issues ?? []);

const riskLevels = [
  { name: 'low' as RiskLevel, label: 'Low' },
  { name: 'medium' as RiskLevel, label: 'Medium' },
  { name: 'high' as RiskLevel, label: 'High' },
  { name: 'critical' as RiskLevel, label: 'Critical' },
];

function getRiskCount(level: RiskLevel): number {
  return stats.value?.risk_distribution[level] ?? 0;
}

function getRiskPercentage(level: RiskLevel): number {
  if (!stats.value) return 0;
  const distribution = stats.value.risk_distribution;
  const total = distribution.low + distribution.medium + distribution.high + distribution.critical;
  if (total === 0) return 0;
  return (distribution[level] / total) * 100;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function refresh() {
  store.refresh();
}

function clearError() {
  store.clearError();
}

onMounted(() => {
  store.fetchStats();
});
</script>

<style lang="scss" scoped>
.guardstack-dashboard {
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  h1 {
    margin: 0;
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  .stat-icon {
    font-size: 32px;
    margin-right: 16px;
    color: var(--primary);
  }

  .stat-value {
    font-size: 28px;
    font-weight: bold;
  }

  .stat-label {
    color: var(--text-muted);
    font-size: 14px;
  }

  &.risk-low { border-left: 4px solid #22c55e; }
  &.risk-medium { border-left: 4px solid #f59e0b; }
  &.risk-high { border-left: 4px solid #ef4444; }
  &.risk-critical { border-left: 4px solid #991b1b; }
}

.section {
  margin-bottom: 30px;

  h2 {
    margin-bottom: 16px;
    font-size: 18px;
  }
}

.risk-distribution {
  background: var(--card-bg, #fff);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.risk-bar {
  display: flex;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  background: #e5e7eb;
  margin-bottom: 16px;
}

.risk-segment {
  transition: width 0.3s ease;

  &.risk-low { background: #22c55e; }
  &.risk-medium { background: #f59e0b; }
  &.risk-high { background: #ef4444; }
  &.risk-critical { background: #991b1b; }
}

.risk-legend {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;

  &.risk-low { background: #22c55e; }
  &.risk-medium { background: #f59e0b; }
  &.risk-high { background: #ef4444; }
  &.risk-critical { background: #991b1b; }
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  th, td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }

  th {
    background: var(--header-bg, #f9fafb);
    font-weight: 600;
  }

  tr:last-child td {
    border-bottom: none;
  }
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;

  &.badge-predictive { background: #dbeafe; color: #1d4ed8; }
  &.badge-genai { background: #dcfce7; color: #166534; }
  &.badge-agentic { background: #fef3c7; color: #92400e; }
}

.status {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;

  &.status-pending { background: #fef3c7; color: #92400e; }
  &.status-running { background: #dbeafe; color: #1d4ed8; }
  &.status-completed { background: #dcfce7; color: #166534; }
  &.status-failed { background: #fee2e2; color: #991b1b; }
  &.status-cancelled { background: #e5e7eb; color: #374151; }
}

.risk-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;

  &.risk-low { background: #dcfce7; color: #166534; }
  &.risk-medium { background: #fef3c7; color: #92400e; }
  &.risk-high { background: #fee2e2; color: #991b1b; }
  &.risk-critical { background: #991b1b; color: #fff; }
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.issue-card {
  padding: 16px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  border-left: 4px solid;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  &.severity-low { border-color: #22c55e; }
  &.severity-medium { border-color: #f59e0b; }
  &.severity-high { border-color: #ef4444; }
  &.severity-critical { border-color: #991b1b; }

  .issue-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .issue-type {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
  }

  .issue-severity {
    font-size: 12px;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 500;

    &.severity-low { background: #dcfce7; color: #166534; }
    &.severity-medium { background: #fef3c7; color: #92400e; }
    &.severity-high { background: #fee2e2; color: #991b1b; }
    &.severity-critical { background: #991b1b; color: #fff; }
  }

  .issue-title {
    font-weight: 600;
    margin-bottom: 8px;
  }

  .issue-description {
    color: var(--text-muted);
    margin-bottom: 12px;
  }

  .issue-recommendation {
    font-size: 14px;
    padding: 8px;
    background: var(--bg-muted, #f9fafb);
    border-radius: 4px;
  }
}

.no-issues {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  color: #22c55e;
  font-weight: 500;

  .icon {
    font-size: 24px;
  }
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;

  &.btn-primary {
    background: var(--primary);
    color: #fff;

    &:hover {
      background: var(--primary-hover);
    }
  }
}

.icon-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.alert {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 4px;
  margin-bottom: 20px;

  &.alert-error {
    background: #fee2e2;
    color: #991b1b;
  }
}
</style>
