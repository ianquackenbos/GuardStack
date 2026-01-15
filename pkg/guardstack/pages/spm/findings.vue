<script lang="ts" setup>
/**
 * SPM Findings - Security Findings Management
 * 
 * Lists and manages security findings across AI assets
 * with filtering, severity categorization, and remediation tracking.
 */
import { ref, onMounted, computed } from 'vue';

interface Finding {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: string;
  asset_name: string;
  status: 'open' | 'in_progress' | 'resolved' | 'ignored';
  remediation: string;
  detected_at: string;
}

const loading = ref(true);
const findings = ref<Finding[]>([]);
const selectedSeverity = ref<string>('all');
const selectedStatus = ref<string>('all');
const searchQuery = ref('');

const severityOptions = ['all', 'critical', 'high', 'medium', 'low', 'info'];
const statusOptions = ['all', 'open', 'in_progress', 'resolved', 'ignored'];

const severityColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  low: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  info: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
};

const statusColors: Record<string, string> = {
  open: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  in_progress: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  resolved: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  ignored: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
};

const filteredFindings = computed(() => {
  return findings.value.filter(finding => {
    const matchesSeverity = selectedSeverity.value === 'all' || finding.severity === selectedSeverity.value;
    const matchesStatus = selectedStatus.value === 'all' || finding.status === selectedStatus.value;
    const matchesSearch = !searchQuery.value || 
      finding.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      finding.description.toLowerCase().includes(searchQuery.value.toLowerCase());
    return matchesSeverity && matchesStatus && matchesSearch;
  });
});

const findingStats = computed(() => {
  const stats = {
    total: findings.value.length,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };
  findings.value.forEach(f => {
    if (f.severity in stats) {
      stats[f.severity as keyof typeof stats]++;
    }
  });
  return stats;
});

async function fetchFindings() {
  loading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    findings.value = [
      {
        id: '1',
        title: 'Model API Key Exposed in Logs',
        description: 'API key for production model found in application logs accessible to unauthorized users.',
        severity: 'critical',
        category: 'exposure',
        asset_name: 'GPT-4-Production',
        status: 'open',
        remediation: 'Rotate API key immediately and configure log scrubbing.',
        detected_at: new Date(Date.now() - 4 * 3600000).toISOString(),
      },
      {
        id: '2',
        title: 'Missing Input Validation on RAG Pipeline',
        description: 'RAG pipeline accepts user input without proper sanitization, potential prompt injection risk.',
        severity: 'high',
        category: 'vulnerability',
        asset_name: 'RAG-Pipeline-Prod',
        status: 'in_progress',
        remediation: 'Implement input validation and sanitization before processing.',
        detected_at: new Date(Date.now() - 48 * 3600000).toISOString(),
      },
      {
        id: '3',
        title: 'Dataset Missing Encryption at Rest',
        description: 'Customer dataset stored without encryption, violating data protection policies.',
        severity: 'high',
        category: 'misconfiguration',
        asset_name: 'Customer-Dataset-v2',
        status: 'open',
        remediation: 'Enable S3 server-side encryption with customer-managed keys.',
        detected_at: new Date(Date.now() - 24 * 3600000).toISOString(),
      },
      {
        id: '4',
        title: 'Outdated Model Version with Known Vulnerabilities',
        description: 'Model version has known bias issues that were fixed in newer versions.',
        severity: 'medium',
        category: 'vulnerability',
        asset_name: 'Embedding-Model-v1',
        status: 'open',
        remediation: 'Upgrade to latest model version with bias mitigations.',
        detected_at: new Date(Date.now() - 72 * 3600000).toISOString(),
      },
      {
        id: '5',
        title: 'Insufficient Audit Logging',
        description: 'Model inference requests not being logged for compliance audit trail.',
        severity: 'medium',
        category: 'compliance',
        asset_name: 'Claude-3-Endpoint',
        status: 'resolved',
        remediation: 'Enable comprehensive request/response logging.',
        detected_at: new Date(Date.now() - 168 * 3600000).toISOString(),
      },
    ];
  } finally {
    loading.value = false;
  }
}

async function updateFindingStatus(findingId: string, newStatus: string) {
  const finding = findings.value.find(f => f.id === findingId);
  if (finding) {
    finding.status = newStatus as Finding['status'];
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

onMounted(() => {
  fetchFindings();
});
</script>

<template>
  <div class="findings-page p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Security Findings
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Review and remediate security issues across your AI assets
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="fetchFindings"
      >
        🔄 Refresh
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-5 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ findingStats.total }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Total Findings</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-2xl font-bold text-red-600">{{ findingStats.critical }}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Critical</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-2xl font-bold text-orange-600">{{ findingStats.high }}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">High</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-2xl font-bold text-yellow-600">{{ findingStats.medium }}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Medium</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-2xl font-bold text-green-600">{{ findingStats.low }}</div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Low</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-center">
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search findings..."
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div>
          <select
            v-model="selectedSeverity"
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option v-for="opt in severityOptions" :key="opt" :value="opt">
              {{ opt === 'all' ? 'All Severities' : opt.charAt(0).toUpperCase() + opt.slice(1) }}
            </option>
          </select>
        </div>
        <div>
          <select
            v-model="selectedStatus"
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option v-for="opt in statusOptions" :key="opt" :value="opt">
              {{ opt === 'all' ? 'All Statuses' : opt.replace('_', ' ').charAt(0).toUpperCase() + opt.replace('_', ' ').slice(1) }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Findings List -->
    <div v-else class="space-y-4">
      <div
        v-for="finding in filteredFindings"
        :key="finding.id"
        class="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <span
                :class="['px-2 py-1 text-xs font-medium rounded-full', severityColors[finding.severity]]"
              >
                {{ finding.severity.toUpperCase() }}
              </span>
              <span
                :class="['px-2 py-1 text-xs font-medium rounded-full', statusColors[finding.status]]"
              >
                {{ finding.status.replace('_', ' ').toUpperCase() }}
              </span>
              <span class="text-sm text-gray-500 dark:text-gray-400">
                {{ finding.category }}
              </span>
            </div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
              {{ finding.title }}
            </h3>
            <p class="text-gray-600 dark:text-gray-300 mb-3">
              {{ finding.description }}
            </p>
            <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span>📦 {{ finding.asset_name }}</span>
              <span>🕐 {{ formatDate(finding.detected_at) }}</span>
            </div>
          </div>
          <div class="ml-4">
            <select
              :value="finding.status"
              class="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              @change="updateFindingStatus(finding.id, ($event.target as HTMLSelectElement).value)"
            >
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
              <option value="ignored">Ignored</option>
            </select>
          </div>
        </div>
        <div v-if="finding.remediation" class="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
            💡 Remediation
          </div>
          <div class="text-sm text-blue-700 dark:text-blue-300">
            {{ finding.remediation }}
          </div>
        </div>
      </div>

      <div
        v-if="filteredFindings.length === 0"
        class="text-center py-12 text-gray-500 dark:text-gray-400"
      >
        No findings match your filters.
      </div>
    </div>
  </div>
</template>

<style scoped>
.findings-page {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .findings-page {
    background-color: #111827;
  }
}
</style>
