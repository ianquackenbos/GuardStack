<script lang="ts" setup>
/**
 * Dashboard Page
 * Main overview with metrics and recent activity
 */
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useDashboardStore } from '../store/dashboard';
import { useModelsStore } from '../store/models';
import { useEvaluationsStore } from '../store/evaluations';
import ScoreGauge from '../components/ScoreGauge.vue';
import RiskSummaryCard from '../components/RiskSummaryCard.vue';
import TrendChart from '../components/TrendChart.vue';
import ModelCard from '../components/ModelCard.vue';
import StatusBadge from '../components/StatusBadge.vue';
import type { Model, Evaluation } from '../types';

const router = useRouter();
const dashboardStore = useDashboardStore();
const modelsStore = useModelsStore();
const evaluationsStore = useEvaluationsStore();

const loading = ref(true);

const stats = computed(() => dashboardStore.stats);
const trend = computed(() => dashboardStore.trend);
const recentModels = computed(() => modelsStore.models.slice(0, 4));
const recentEvaluations = computed(() => evaluationsStore.evaluations.slice(0, 5));

async function loadData() {
  loading.value = true;
  try {
    await Promise.all([
      dashboardStore.fetchStats(),
      dashboardStore.fetchTrend('30d'),
      modelsStore.fetchModels({ limit: 4 }),
      evaluationsStore.fetchEvaluations({ limit: 5 }),
    ]);
  } catch (error) {
    console.error('Failed to load dashboard data:', error);
  } finally {
    loading.value = false;
  }
}

function navigateToModel(model: Model) {
  router.push(`/guardstack/models/${model.id}`);
}

function navigateToEvaluation(evaluation: Evaluation) {
  router.push(`/guardstack/evaluations/${evaluation.id}`);
}

function startNewEvaluation() {
  router.push('/guardstack/evaluations/new');
}

onMounted(loadData);
</script>

<template>
  <div class="dashboard p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Dashboard
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          AI Safety & Governance Overview
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="startNewEvaluation"
      >
        New Evaluation
      </button>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <template v-else>
      <!-- Stats cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <!-- Total models -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 dark:text-gray-400">Total Models</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                {{ stats?.totalModels || 0 }}
              </p>
            </div>
            <div class="text-4xl">📊</div>
          </div>
        </div>
        
        <!-- Active evaluations -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 dark:text-gray-400">Active Evaluations</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">
                {{ stats?.activeEvaluations || 0 }}
              </p>
            </div>
            <div class="text-4xl">🔄</div>
          </div>
        </div>
        
        <!-- Average score -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 dark:text-gray-400">Avg Safety Score</p>
              <p class="text-3xl font-bold mt-1" :class="[
                (stats?.averageScore || 0) >= 80 ? 'text-green-600' :
                (stats?.averageScore || 0) >= 60 ? 'text-yellow-600' : 'text-red-600'
              ]">
                {{ Math.round(stats?.averageScore || 0) }}
              </p>
            </div>
            <ScoreGauge :score="stats?.averageScore || 0" :size="60" />
          </div>
        </div>
        
        <!-- Risk summary -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 dark:text-gray-400">High Risk Models</p>
              <p class="text-3xl font-bold text-red-600 mt-1">
                {{ stats?.highRiskModels || 0 }}
              </p>
            </div>
            <div class="text-4xl">⚠️</div>
          </div>
        </div>
      </div>
      
      <!-- Main content -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <!-- Score trend -->
        <div class="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg border p-6">
          <h3 class="font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Safety Score Trend
          </h3>
          <TrendChart
            v-if="trend.length > 0"
            :data="trend"
            :height="250"
            :thresholds="[{ value: 60, color: '#f59e0b', label: 'Threshold' }]"
          />
          <div v-else class="flex items-center justify-center h-64 text-gray-400">
            No trend data available
          </div>
        </div>
        
        <!-- Risk distribution -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <h3 class="font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Risk Distribution
          </h3>
          <RiskSummaryCard
            :passed="stats?.passedModels || 0"
            :warning="stats?.warningModels || 0"
            :failed="stats?.failedModels || 0"
          />
          
          <div class="mt-4 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">Minimal Risk</span>
              <span class="text-sm font-medium text-green-600">{{ stats?.riskDistribution?.minimal || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">Low Risk</span>
              <span class="text-sm font-medium text-blue-600">{{ stats?.riskDistribution?.low || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">Medium Risk</span>
              <span class="text-sm font-medium text-yellow-600">{{ stats?.riskDistribution?.medium || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">High Risk</span>
              <span class="text-sm font-medium text-orange-600">{{ stats?.riskDistribution?.high || 0 }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500">Critical Risk</span>
              <span class="text-sm font-medium text-red-600">{{ stats?.riskDistribution?.critical || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Recent activity -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Recent models -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-gray-900 dark:text-gray-100">
              Recent Models
            </h3>
            <router-link
              to="/guardstack/models"
              class="text-sm text-blue-600 hover:underline"
            >
              View All →
            </router-link>
          </div>
          
          <div v-if="recentModels.length > 0" class="space-y-3">
            <ModelCard
              v-for="model in recentModels"
              :key="model.id"
              :model="model"
              compact
              @view="navigateToModel"
            />
          </div>
          <div v-else class="text-center py-8 text-gray-400">
            No models yet
          </div>
        </div>
        
        <!-- Recent evaluations -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold text-gray-900 dark:text-gray-100">
              Recent Evaluations
            </h3>
            <router-link
              to="/guardstack/evaluations"
              class="text-sm text-blue-600 hover:underline"
            >
              View All →
            </router-link>
          </div>
          
          <div v-if="recentEvaluations.length > 0" class="space-y-2">
            <div
              v-for="evaluation in recentEvaluations"
              :key="evaluation.id"
              class="flex items-center justify-between p-3 rounded hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
              @click="navigateToEvaluation(evaluation)"
            >
              <div>
                <p class="font-medium text-gray-900 dark:text-gray-100">
                  {{ evaluation.name }}
                </p>
                <p class="text-xs text-gray-500">
                  {{ new Date(evaluation.createdAt).toLocaleDateString() }}
                </p>
              </div>
              <div class="flex items-center gap-3">
                <span
                  v-if="evaluation.overallScore !== undefined"
                  :class="[
                    'font-semibold',
                    evaluation.overallScore >= 80 ? 'text-green-600' :
                    evaluation.overallScore >= 60 ? 'text-yellow-600' : 'text-red-600'
                  ]"
                >
                  {{ Math.round(evaluation.overallScore) }}
                </span>
                <StatusBadge
                  :status="evaluation.status === 'completed' ? 'pass' :
                           evaluation.status === 'failed' ? 'fail' :
                           evaluation.status === 'running' ? 'pending' : 'warn'"
                  size="sm"
                />
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-gray-400">
            No evaluations yet
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
