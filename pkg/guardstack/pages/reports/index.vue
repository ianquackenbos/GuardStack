<script lang="ts" setup>
/**
 * Reports Page - Report Generation & Management
 * 
 * Generate, schedule, and download compliance and security reports.
 */
import { ref, onMounted, computed } from 'vue';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  supported_formats: string[];
}

interface Report {
  id: string;
  title: string;
  template_id: string;
  format: string;
  status: 'queued' | 'generating' | 'completed' | 'failed';
  file_size: number | null;
  created_by: string;
  created_at: string;
  completed_at: string | null;
}

interface ScheduledReport {
  id: string;
  title: string;
  template_id: string;
  format: string;
  schedule: string;
  enabled: boolean;
  last_run: string | null;
  next_run: string | null;
}

const loading = ref(true);
const templates = ref<ReportTemplate[]>([]);
const reports = ref<Report[]>([]);
const scheduledReports = ref<ScheduledReport[]>([]);
const activeTab = ref<'reports' | 'templates' | 'scheduled'>('reports');
const showGenerateModal = ref(false);
const selectedTemplate = ref<ReportTemplate | null>(null);

const newReport = ref({
  title: '',
  template_id: '',
  format: 'pdf',
});

const statusColors: Record<string, string> = {
  queued: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  generating: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const categoryIcons: Record<string, string> = {
  compliance: '📋',
  security: '🔒',
  executive: '📊',
  audit: '🔍',
};

async function fetchData() {
  loading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    templates.value = [
      {
        id: 'compliance-summary',
        name: 'Compliance Summary Report',
        description: 'Overview of compliance status across all frameworks',
        category: 'compliance',
        supported_formats: ['pdf', 'html', 'json'],
      },
      {
        id: 'security-posture',
        name: 'AI Security Posture Report',
        description: 'Comprehensive security posture analysis with risk scores',
        category: 'security',
        supported_formats: ['pdf', 'html'],
      },
      {
        id: 'executive-dashboard',
        name: 'Executive Dashboard Report',
        description: 'High-level metrics and KPIs for leadership',
        category: 'executive',
        supported_formats: ['pdf', 'html'],
      },
      {
        id: 'model-inventory',
        name: 'AI Model Inventory Report',
        description: 'Complete inventory of AI models and their security status',
        category: 'audit',
        supported_formats: ['pdf', 'html', 'csv', 'json'],
      },
      {
        id: 'evaluation-results',
        name: 'Model Evaluation Results',
        description: 'Detailed evaluation results with benchmark comparisons',
        category: 'security',
        supported_formats: ['pdf', 'html', 'json'],
      },
    ];

    reports.value = [
      {
        id: '1',
        title: 'Q4 2024 Compliance Summary',
        template_id: 'compliance-summary',
        format: 'pdf',
        status: 'completed',
        file_size: 2456789,
        created_by: 'admin',
        created_at: new Date(Date.now() - 2 * 3600000).toISOString(),
        completed_at: new Date(Date.now() - 1.75 * 3600000).toISOString(),
      },
      {
        id: '2',
        title: 'Weekly Security Posture',
        template_id: 'security-posture',
        format: 'pdf',
        status: 'completed',
        file_size: 1234567,
        created_by: 'security-team',
        created_at: new Date(Date.now() - 24 * 3600000).toISOString(),
        completed_at: new Date(Date.now() - 23.5 * 3600000).toISOString(),
      },
      {
        id: '3',
        title: 'Model Inventory Export',
        template_id: 'model-inventory',
        format: 'json',
        status: 'generating',
        file_size: null,
        created_by: 'admin',
        created_at: new Date(Date.now() - 5 * 60000).toISOString(),
        completed_at: null,
      },
    ];

    scheduledReports.value = [
      {
        id: '1',
        title: 'Weekly Compliance Summary',
        template_id: 'compliance-summary',
        format: 'pdf',
        schedule: 'Every Monday at 8 AM',
        enabled: true,
        last_run: new Date(Date.now() - 3 * 86400000).toISOString(),
        next_run: new Date(Date.now() + 4 * 86400000).toISOString(),
      },
      {
        id: '2',
        title: 'Daily Security Posture',
        template_id: 'security-posture',
        format: 'html',
        schedule: 'Every day at 6 AM',
        enabled: true,
        last_run: new Date(Date.now() - 18 * 3600000).toISOString(),
        next_run: new Date(Date.now() + 6 * 3600000).toISOString(),
      },
    ];
  } finally {
    loading.value = false;
  }
}

function openGenerateModal(template: ReportTemplate) {
  selectedTemplate.value = template;
  newReport.value = {
    title: `${template.name} - ${new Date().toLocaleDateString()}`,
    template_id: template.id,
    format: template.supported_formats[0],
  };
  showGenerateModal.value = true;
}

async function generateReport() {
  if (!newReport.value.title || !newReport.value.template_id) return;
  
  const report: Report = {
    id: String(Date.now()),
    title: newReport.value.title,
    template_id: newReport.value.template_id,
    format: newReport.value.format,
    status: 'queued',
    file_size: null,
    created_by: 'current-user',
    created_at: new Date().toISOString(),
    completed_at: null,
  };
  
  reports.value.unshift(report);
  showGenerateModal.value = false;
  activeTab.value = 'reports';
  
  // Simulate generation
  setTimeout(() => {
    report.status = 'generating';
    setTimeout(() => {
      report.status = 'completed';
      report.file_size = Math.floor(Math.random() * 5000000) + 500000;
      report.completed_at = new Date().toISOString();
    }, 5000);
  }, 1000);
}

function downloadReport(reportId: string) {
  alert(`Downloading report ${reportId}...`);
}

function toggleSchedule(scheduleId: string) {
  const schedule = scheduledReports.value.find(s => s.id === scheduleId);
  if (schedule) {
    schedule.enabled = !schedule.enabled;
  }
}

function formatFileSize(bytes: number | null): string {
  if (!bytes) return '-';
  if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`;
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${bytes} B`;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString();
}

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="reports-page p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Reports
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Generate and manage compliance and security reports
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="activeTab = 'templates'"
      >
        ➕ New Report
      </button>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
      <nav class="flex gap-8">
        <button
          :class="[
            'pb-4 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'reports'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
          @click="activeTab = 'reports'"
        >
          📄 Generated Reports
        </button>
        <button
          :class="[
            'pb-4 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'templates'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
          @click="activeTab = 'templates'"
        >
          📝 Templates
        </button>
        <button
          :class="[
            'pb-4 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'scheduled'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
          @click="activeTab = 'scheduled'"
        >
          ⏰ Scheduled
        </button>
      </nav>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <template v-else>
      <!-- Generated Reports -->
      <div v-if="activeTab === 'reports'" class="space-y-4">
        <div
          v-for="report in reports"
          :key="report.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
        >
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-3 mb-2">
                <h3 class="font-semibold text-gray-900 dark:text-white">
                  {{ report.title }}
                </h3>
                <span :class="['px-2 py-1 text-xs font-medium rounded-full', statusColors[report.status]]">
                  {{ report.status }}
                </span>
                <span class="px-2 py-1 text-xs font-medium rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 uppercase">
                  {{ report.format }}
                </span>
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                <span>Created: {{ formatDate(report.created_at) }}</span>
                <span v-if="report.file_size">Size: {{ formatFileSize(report.file_size) }}</span>
                <span>By: {{ report.created_by }}</span>
              </div>
            </div>
            <div>
              <button
                v-if="report.status === 'completed'"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                @click="downloadReport(report.id)"
              >
                ⬇️ Download
              </button>
              <div
                v-else-if="report.status === 'generating'"
                class="flex items-center gap-2 text-blue-600"
              >
                <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                Generating...
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="reports.length === 0"
          class="text-center py-12 text-gray-500 dark:text-gray-400"
        >
          No reports generated yet. Create one from the Templates tab.
        </div>
      </div>

      <!-- Templates -->
      <div v-if="activeTab === 'templates'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="template in templates"
          :key="template.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer"
          @click="openGenerateModal(template)"
        >
          <div class="flex items-start gap-3 mb-3">
            <span class="text-2xl">{{ categoryIcons[template.category] || '📄' }}</span>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ template.name }}
              </h3>
              <span class="text-xs text-gray-500 dark:text-gray-400 uppercase">
                {{ template.category }}
              </span>
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">
            {{ template.description }}
          </p>
          <div class="flex gap-2">
            <span
              v-for="format in template.supported_formats"
              :key="format"
              class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded uppercase"
            >
              {{ format }}
            </span>
          </div>
        </div>
      </div>

      <!-- Scheduled Reports -->
      <div v-if="activeTab === 'scheduled'" class="space-y-4">
        <div
          v-for="schedule in scheduledReports"
          :key="schedule.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
        >
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white mb-1">
                {{ schedule.title }}
              </h3>
              <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                <span>⏰ {{ schedule.schedule }}</span>
                <span>📁 {{ schedule.format.toUpperCase() }}</span>
              </div>
              <div class="flex items-center gap-4 mt-2 text-xs text-gray-400 dark:text-gray-500">
                <span>Last run: {{ formatDate(schedule.last_run) }}</span>
                <span>Next run: {{ formatDate(schedule.next_run) }}</span>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <span
                :class="[
                  'px-3 py-1 text-sm rounded-full',
                  schedule.enabled
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                ]"
              >
                {{ schedule.enabled ? 'Active' : 'Paused' }}
              </span>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  :checked="schedule.enabled"
                  class="sr-only peer"
                  @change="toggleSchedule(schedule.id)"
                />
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        <button class="w-full p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 hover:border-blue-500 hover:text-blue-500 transition-colors">
          ➕ Create New Schedule
        </button>
      </div>
    </template>

    <!-- Generate Modal -->
    <div
      v-if="showGenerateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showGenerateModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Generate Report
        </h2>
        <div v-if="selectedTemplate" class="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div class="font-medium text-gray-900 dark:text-white">
            {{ selectedTemplate.name }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{ selectedTemplate.description }}
          </div>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Report Title
            </label>
            <input
              v-model="newReport.title"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Format
            </label>
            <select
              v-model="newReport.format"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option
                v-for="format in selectedTemplate?.supported_formats || []"
                :key="format"
                :value="format"
              >
                {{ format.toUpperCase() }}
              </option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            @click="showGenerateModal = false"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            @click="generateReport"
          >
            Generate
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reports-page {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .reports-page {
    background-color: #111827;
  }
}
</style>
