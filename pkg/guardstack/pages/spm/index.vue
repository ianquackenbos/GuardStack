<script lang="ts" setup>
/**
 * SPM Dashboard - AI Security Posture Management Overview
 * 
 * Displays security posture scores, risk metrics, and trending data
 * for AI assets across the organization.
 */
import { ref, onMounted, computed } from 'vue';

interface PostureScore {
  overall_score: number;
  model_security: number;
  data_protection: number;
  access_control: number;
  compliance: number;
  monitoring: number;
}

interface PostureData {
  score: PostureScore;
  total_assets: number;
  assets_by_risk: Record<string, number>;
  open_findings: number;
  critical_findings: number;
  trend: string;
  last_scan: string | null;
}

const loading = ref(true);
const postureData = ref<PostureData | null>(null);
const postureHistory = ref<Array<{ date: string; overall_score: number }>>([]);

// Risk level colors
const riskColors: Record<string, string> = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#ca8a04',
  low: '#16a34a',
};

// Score category labels
const scoreCategories = [
  { key: 'model_security', label: 'Model Security', icon: '🔐' },
  { key: 'data_protection', label: 'Data Protection', icon: '🛡️' },
  { key: 'access_control', label: 'Access Control', icon: '🔑' },
  { key: 'compliance', label: 'Compliance', icon: '✅' },
  { key: 'monitoring', label: 'Monitoring', icon: '📊' },
];

const overallScoreClass = computed(() => {
  if (!postureData.value) return 'text-gray-400';
  const score = postureData.value.score.overall_score;
  if (score >= 80) return 'text-green-500';
  if (score >= 60) return 'text-yellow-500';
  return 'text-red-500';
});

const trendIcon = computed(() => {
  if (!postureData.value) return '➡️';
  switch (postureData.value.trend) {
    case 'improving': return '📈';
    case 'declining': return '📉';
    default: return '➡️';
  }
});

async function fetchPostureData() {
  loading.value = true;
  try {
    // Mock API call - replace with actual API
    await new Promise(resolve => setTimeout(resolve, 500));
    
    postureData.value = {
      score: {
        overall_score: 72.5,
        model_security: 78.0,
        data_protection: 65.0,
        access_control: 82.0,
        compliance: 70.0,
        monitoring: 67.5,
      },
      total_assets: 47,
      assets_by_risk: {
        critical: 2,
        high: 8,
        medium: 15,
        low: 22,
      },
      open_findings: 23,
      critical_findings: 3,
      trend: 'improving',
      last_scan: new Date().toISOString(),
    };

    // Generate mock history
    postureHistory.value = Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 86400000).toISOString(),
      overall_score: 65 + Math.random() * 15,
    }));
  } finally {
    loading.value = false;
  }
}

async function triggerScan() {
  // Trigger a new security scan
  alert('Security scan initiated. This may take several minutes.');
}

function navigateTo(path: string) {
  // Navigation logic
  window.location.href = path;
}

onMounted(() => {
  fetchPostureData();
});
</script>

<template>
  <div class="spm-dashboard p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          AI Security Posture Management
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Monitor and manage security posture across your AI assets
        </p>
      </div>
      <div class="flex gap-3">
        <button
          class="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          @click="fetchPostureData"
        >
          🔄 Refresh
        </button>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          @click="triggerScan"
        >
          🔍 Run Scan
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <template v-else-if="postureData">
      <!-- Overall Score Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Overall Score -->
          <div class="text-center">
            <h3 class="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
              Overall Security Score
            </h3>
            <div :class="['text-6xl font-bold', overallScoreClass]">
              {{ postureData.score.overall_score.toFixed(1) }}
            </div>
            <div class="text-gray-500 dark:text-gray-400 mt-2 flex items-center justify-center gap-2">
              <span>{{ trendIcon }}</span>
              <span class="capitalize">{{ postureData.trend }}</span>
            </div>
          </div>

          <!-- Quick Stats -->
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <div class="text-3xl font-bold text-gray-900 dark:text-white">
                {{ postureData.total_assets }}
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Total Assets</div>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <div class="text-3xl font-bold text-orange-500">
                {{ postureData.open_findings }}
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Open Findings</div>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <div class="text-3xl font-bold text-red-500">
                {{ postureData.critical_findings }}
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Critical</div>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <div class="text-sm text-gray-500 dark:text-gray-400">Last Scan</div>
              <div class="text-sm font-medium text-gray-900 dark:text-white">
                {{ postureData.last_scan ? new Date(postureData.last_scan).toLocaleString() : 'Never' }}
              </div>
            </div>
          </div>

          <!-- Risk Distribution -->
          <div>
            <h4 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">
              Assets by Risk Level
            </h4>
            <div class="space-y-3">
              <div
                v-for="(count, level) in postureData.assets_by_risk"
                :key="level"
                class="flex items-center gap-3"
              >
                <div class="w-20 text-sm capitalize text-gray-600 dark:text-gray-400">
                  {{ level }}
                </div>
                <div class="flex-1 h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-500"
                    :style="{
                      width: `${(count / postureData.total_assets) * 100}%`,
                      backgroundColor: riskColors[level as string],
                    }"
                  ></div>
                </div>
                <div class="w-8 text-sm font-medium text-gray-900 dark:text-white">
                  {{ count }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Score Categories -->
      <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div
          v-for="category in scoreCategories"
          :key="category.key"
          class="bg-white dark:bg-gray-800 rounded-xl shadow p-4"
        >
          <div class="flex items-center gap-2 mb-2">
            <span class="text-xl">{{ category.icon }}</span>
            <span class="text-sm font-medium text-gray-600 dark:text-gray-400">
              {{ category.label }}
            </span>
          </div>
          <div class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ postureData.score[category.key as keyof PostureScore].toFixed(1) }}%
          </div>
          <div class="mt-2 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              class="h-full bg-blue-500 rounded-full transition-all duration-500"
              :style="{ width: `${postureData.score[category.key as keyof PostureScore]}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          class="bg-white dark:bg-gray-800 rounded-xl shadow p-6 hover:shadow-lg transition-shadow text-left"
          @click="navigateTo('/spm/findings')"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">🔍</span>
            <div>
              <div class="font-medium text-gray-900 dark:text-white">View Findings</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                {{ postureData.open_findings }} open issues to review
              </div>
            </div>
          </div>
        </button>

        <button
          class="bg-white dark:bg-gray-800 rounded-xl shadow p-6 hover:shadow-lg transition-shadow text-left"
          @click="navigateTo('/spm/inventory')"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">📦</span>
            <div>
              <div class="font-medium text-gray-900 dark:text-white">Asset Inventory</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                {{ postureData.total_assets }} AI assets tracked
              </div>
            </div>
          </div>
        </button>

        <button
          class="bg-white dark:bg-gray-800 rounded-xl shadow p-6 hover:shadow-lg transition-shadow text-left"
          @click="navigateTo('/reports')"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">📄</span>
            <div>
              <div class="font-medium text-gray-900 dark:text-white">Generate Report</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                Create security posture report
              </div>
            </div>
          </div>
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.spm-dashboard {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .spm-dashboard {
    background-color: #111827;
  }
}
</style>
