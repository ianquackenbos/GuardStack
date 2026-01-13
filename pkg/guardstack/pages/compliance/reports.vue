<script lang="ts" setup>
/**
 * Compliance Reports Page
 * Generate and manage compliance reports
 */
import { ref, onMounted } from 'vue';
import StatusBadge from '../../components/StatusBadge.vue';

interface Report {
  id: string;
  name: string;
  framework: string;
  status: 'generating' | 'completed' | 'failed';
  createdAt: string;
  size?: string;
  downloadUrl?: string;
}

const loading = ref(true);
const reports = ref<Report[]>([]);
const showGenerateModal = ref(false);

const reportTemplates = [
  {
    id: 'eu-ai-act',
    name: 'EU AI Act Assessment',
    description: 'Comprehensive assessment against EU AI Act requirements',
    icon: '🇪🇺',
  },
  {
    id: 'soc2',
    name: 'SOC 2 Type II',
    description: 'AI-specific controls for SOC 2 certification',
    icon: '🔒',
  },
  {
    id: 'nist-ai-rmf',
    name: 'NIST AI RMF',
    description: 'NIST AI Risk Management Framework assessment',
    icon: '🏛️',
  },
  {
    id: 'iso-42001',
    name: 'ISO/IEC 42001',
    description: 'AI Management System certification readiness',
    icon: '📋',
  },
];

async function generateReport(templateId: string) {
  showGenerateModal.value = false;
  
  const newReport: Report = {
    id: `report-${Date.now()}`,
    name: `${reportTemplates.find(t => t.id === templateId)?.name} - ${new Date().toISOString().split('T')[0]}`,
    framework: templateId,
    status: 'generating',
    createdAt: new Date().toISOString(),
  };
  
  reports.value.unshift(newReport);
  
  // Simulate report generation
  setTimeout(() => {
    const index = reports.value.findIndex(r => r.id === newReport.id);
    if (index !== -1) {
      reports.value[index] = {
        ...reports.value[index],
        status: 'completed',
        size: '2.4 MB',
        downloadUrl: `/api/reports/${newReport.id}/download`,
      };
    }
  }, 3000);
}

function downloadReport(report: Report) {
  if (report.downloadUrl) {
    window.open(report.downloadUrl, '_blank');
  }
}

function deleteReport(report: Report) {
  reports.value = reports.value.filter(r => r.id !== report.id);
}

onMounted(() => {
  // Load existing reports
  reports.value = [
    {
      id: 'report-1',
      name: 'EU AI Act Assessment - 2024-05-15',
      framework: 'eu-ai-act',
      status: 'completed',
      createdAt: '2024-05-15T10:30:00Z',
      size: '2.1 MB',
      downloadUrl: '/api/reports/report-1/download',
    },
    {
      id: 'report-2',
      name: 'NIST AI RMF - 2024-05-10',
      framework: 'nist-ai-rmf',
      status: 'completed',
      createdAt: '2024-05-10T14:20:00Z',
      size: '1.8 MB',
      downloadUrl: '/api/reports/report-2/download',
    },
  ];
  loading.value = false;
});
</script>

<template>
  <div class="compliance-reports p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Compliance Reports
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Generate and manage compliance documentation
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="showGenerateModal = true"
      >
        Generate Report
      </button>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <template v-else>
      <!-- Reports list -->
      <div v-if="reports.length > 0" class="bg-white dark:bg-gray-800 rounded-lg border">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Report</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Framework</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Size</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Created</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="report in reports"
              :key="report.id"
              class="border-t hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <td class="px-4 py-3">
                <div class="font-medium text-gray-900 dark:text-gray-100">
                  {{ report.name }}
                </div>
              </td>
              <td class="px-4 py-3 text-gray-500 dark:text-gray-400 capitalize">
                {{ report.framework.replace(/-/g, ' ') }}
              </td>
              <td class="px-4 py-3">
                <StatusBadge
                  :status="report.status === 'completed' ? 'pass' : 
                           report.status === 'failed' ? 'fail' : 'pending'"
                  :label="report.status"
                />
              </td>
              <td class="px-4 py-3 text-gray-500 dark:text-gray-400">
                {{ report.size || '—' }}
              </td>
              <td class="px-4 py-3 text-gray-500 dark:text-gray-400">
                {{ new Date(report.createdAt).toLocaleDateString() }}
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <button
                    v-if="report.status === 'completed'"
                    class="text-blue-600 hover:underline"
                    @click="downloadReport(report)"
                  >
                    Download
                  </button>
                  <button
                    class="text-red-600 hover:underline"
                    @click="deleteReport(report)"
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Empty state -->
      <div v-else class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
        <span class="text-4xl">📄</span>
        <h3 class="mt-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
          No reports yet
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mt-2">
          Generate your first compliance report
        </p>
        <button
          class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          @click="showGenerateModal = true"
        >
          Generate Report
        </button>
      </div>
    </template>
    
    <!-- Generate modal -->
    <div
      v-if="showGenerateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showGenerateModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
        <div class="flex items-start justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Generate Report
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="showGenerateModal = false"
          >
            ✕
          </button>
        </div>
        
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          Select a compliance framework to generate a report
        </p>
        
        <div class="space-y-3">
          <div
            v-for="template in reportTemplates"
            :key="template.id"
            class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
            @click="generateReport(template.id)"
          >
            <span class="text-2xl">{{ template.icon }}</span>
            <div>
              <h4 class="font-medium text-gray-900 dark:text-gray-100">
                {{ template.name }}
              </h4>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ template.description }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
