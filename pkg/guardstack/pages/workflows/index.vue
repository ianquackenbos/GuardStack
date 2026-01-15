<script lang="ts" setup>
/**
 * Workflows Page - Argo Workflow Management
 * 
 * Monitor and manage Argo workflows for model evaluations.
 */
import { ref, onMounted, computed } from 'vue';

interface Workflow {
  id: string;
  name: string;
  type: 'evaluation' | 'compliance' | 'discovery' | 'custom';
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'error';
  progress: number;
  started_at: string | null;
  finished_at: string | null;
  duration: number | null;
  triggered_by: string;
  model_id?: string;
  model_name?: string;
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  type: string;
  estimated_duration: number;
  inputs: { name: string; type: string; required: boolean }[];
}

const loading = ref(true);
const workflows = ref<Workflow[]>([]);
const templates = ref<WorkflowTemplate[]>([]);
const activeTab = ref<'active' | 'history' | 'templates'>('active');
const filterStatus = ref<string>('all');
const showLaunchModal = ref(false);
const selectedTemplate = ref<WorkflowTemplate | null>(null);

const statusColors: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  running: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  succeeded: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  error: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
};

const typeIcons: Record<string, string> = {
  evaluation: '🧪',
  compliance: '📋',
  discovery: '🔍',
  custom: '⚙️',
};

const activeWorkflows = computed(() => 
  workflows.value.filter(w => ['pending', 'running'].includes(w.status))
);

const historyWorkflows = computed(() => {
  let result = workflows.value.filter(w => ['succeeded', 'failed', 'error'].includes(w.status));
  if (filterStatus.value !== 'all') {
    result = result.filter(w => w.status === filterStatus.value);
  }
  return result;
});

async function fetchData() {
  loading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    workflows.value = [
      {
        id: 'wf-001',
        name: 'GPT-4 Security Evaluation',
        type: 'evaluation',
        status: 'running',
        progress: 65,
        started_at: new Date(Date.now() - 25 * 60000).toISOString(),
        finished_at: null,
        duration: null,
        triggered_by: 'scheduled',
        model_id: 'model-001',
        model_name: 'GPT-4 Production',
      },
      {
        id: 'wf-002',
        name: 'Weekly Compliance Check',
        type: 'compliance',
        status: 'running',
        progress: 32,
        started_at: new Date(Date.now() - 10 * 60000).toISOString(),
        finished_at: null,
        duration: null,
        triggered_by: 'scheduled',
      },
      {
        id: 'wf-003',
        name: 'Model Discovery Scan',
        type: 'discovery',
        status: 'pending',
        progress: 0,
        started_at: null,
        finished_at: null,
        duration: null,
        triggered_by: 'admin',
      },
      {
        id: 'wf-004',
        name: 'Claude-3 Jailbreak Testing',
        type: 'evaluation',
        status: 'succeeded',
        progress: 100,
        started_at: new Date(Date.now() - 3 * 3600000).toISOString(),
        finished_at: new Date(Date.now() - 2.5 * 3600000).toISOString(),
        duration: 1800,
        triggered_by: 'security-team',
        model_id: 'model-002',
        model_name: 'Claude-3 Opus',
      },
      {
        id: 'wf-005',
        name: 'PII Detection Evaluation',
        type: 'evaluation',
        status: 'failed',
        progress: 78,
        started_at: new Date(Date.now() - 5 * 3600000).toISOString(),
        finished_at: new Date(Date.now() - 4.5 * 3600000).toISOString(),
        duration: 1400,
        triggered_by: 'admin',
        model_id: 'model-003',
        model_name: 'Internal LLM v2',
      },
      {
        id: 'wf-006',
        name: 'EU AI Act Compliance',
        type: 'compliance',
        status: 'succeeded',
        progress: 100,
        started_at: new Date(Date.now() - 24 * 3600000).toISOString(),
        finished_at: new Date(Date.now() - 23 * 3600000).toISOString(),
        duration: 3600,
        triggered_by: 'scheduled',
      },
    ];

    templates.value = [
      {
        id: 'eval-standard',
        name: 'Standard Evaluation Pipeline',
        description: 'Complete security evaluation including jailbreak, toxicity, and PII testing',
        type: 'evaluation',
        estimated_duration: 2400,
        inputs: [
          { name: 'model_id', type: 'string', required: true },
          { name: 'test_categories', type: 'array', required: false },
        ],
      },
      {
        id: 'eval-quick',
        name: 'Quick Security Scan',
        description: 'Fast security assessment for common vulnerabilities',
        type: 'evaluation',
        estimated_duration: 600,
        inputs: [
          { name: 'model_id', type: 'string', required: true },
        ],
      },
      {
        id: 'compliance-check',
        name: 'Compliance Assessment',
        description: 'Evaluate model against compliance framework requirements',
        type: 'compliance',
        estimated_duration: 1800,
        inputs: [
          { name: 'framework', type: 'string', required: true },
          { name: 'model_ids', type: 'array', required: false },
        ],
      },
      {
        id: 'discovery-scan',
        name: 'Model Discovery Scan',
        description: 'Scan infrastructure to discover AI models and endpoints',
        type: 'discovery',
        estimated_duration: 900,
        inputs: [
          { name: 'namespaces', type: 'array', required: false },
          { name: 'scan_external', type: 'boolean', required: false },
        ],
      },
    ];
  } finally {
    loading.value = false;
  }
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '-';
  if (seconds >= 3600) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  if (seconds >= 60) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  return `${seconds}s`;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString();
}

function cancelWorkflow(workflowId: string) {
  if (confirm('Are you sure you want to cancel this workflow?')) {
    const workflow = workflows.value.find(w => w.id === workflowId);
    if (workflow) {
      workflow.status = 'error';
      workflow.finished_at = new Date().toISOString();
    }
  }
}

function retryWorkflow(workflowId: string) {
  const original = workflows.value.find(w => w.id === workflowId);
  if (original) {
    const newWorkflow: Workflow = {
      id: `wf-${Date.now()}`,
      name: `${original.name} (Retry)`,
      type: original.type,
      status: 'pending',
      progress: 0,
      started_at: null,
      finished_at: null,
      duration: null,
      triggered_by: 'manual-retry',
      model_id: original.model_id,
      model_name: original.model_name,
    };
    workflows.value.unshift(newWorkflow);
    activeTab.value = 'active';
  }
}

function viewLogs(workflowId: string) {
  alert(`Opening logs for workflow ${workflowId}...`);
}

function openLaunchModal(template: WorkflowTemplate) {
  selectedTemplate.value = template;
  showLaunchModal.value = true;
}

function launchWorkflow() {
  if (!selectedTemplate.value) return;
  
  const newWorkflow: Workflow = {
    id: `wf-${Date.now()}`,
    name: `${selectedTemplate.value.name} - ${new Date().toLocaleDateString()}`,
    type: selectedTemplate.value.type as Workflow['type'],
    status: 'pending',
    progress: 0,
    started_at: null,
    finished_at: null,
    duration: null,
    triggered_by: 'manual',
  };
  
  workflows.value.unshift(newWorkflow);
  showLaunchModal.value = false;
  activeTab.value = 'active';
  
  // Simulate workflow starting
  setTimeout(() => {
    newWorkflow.status = 'running';
    newWorkflow.started_at = new Date().toISOString();
  }, 2000);
}

onMounted(() => {
  fetchData();
  
  // Simulate progress updates
  setInterval(() => {
    workflows.value.forEach(w => {
      if (w.status === 'running' && w.progress < 100) {
        w.progress = Math.min(100, w.progress + Math.random() * 5);
        if (w.progress >= 100) {
          w.status = 'succeeded';
          w.finished_at = new Date().toISOString();
          w.duration = Math.floor((new Date().getTime() - new Date(w.started_at!).getTime()) / 1000);
        }
      }
    });
  }, 3000);
});
</script>

<template>
  <div class="workflows-page p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Workflows
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Manage and monitor Argo workflow executions
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="activeTab = 'templates'"
      >
        🚀 Launch Workflow
      </button>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
      <nav class="flex gap-8">
        <button
          :class="[
            'pb-4 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'active'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
          @click="activeTab = 'active'"
        >
          ▶️ Active ({{ activeWorkflows.length }})
        </button>
        <button
          :class="[
            'pb-4 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'history'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
          @click="activeTab = 'history'"
        >
          📜 History
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
          📋 Templates
        </button>
      </nav>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <template v-else>
      <!-- Active Workflows -->
      <div v-if="activeTab === 'active'" class="space-y-4">
        <div
          v-for="workflow in activeWorkflows"
          :key="workflow.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <span class="text-2xl">{{ typeIcons[workflow.type] }}</span>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">
                  {{ workflow.name }}
                </h3>
                <div class="flex items-center gap-3 mt-1">
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', statusColors[workflow.status]]">
                    {{ workflow.status }}
                  </span>
                  <span class="text-sm text-gray-500 dark:text-gray-400">
                    {{ workflow.model_name || 'System-wide' }}
                  </span>
                </div>
              </div>
            </div>
            <button
              class="px-3 py-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
              @click="cancelWorkflow(workflow.id)"
            >
              Cancel
            </button>
          </div>

          <!-- Progress Bar -->
          <div class="mb-3">
            <div class="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
              <span>Progress</span>
              <span>{{ Math.floor(workflow.progress) }}%</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
              <div
                class="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                :style="{ width: `${workflow.progress}%` }"
              ></div>
            </div>
          </div>

          <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
            <span>Started: {{ formatDate(workflow.started_at) }}</span>
            <span>Triggered by: {{ workflow.triggered_by }}</span>
          </div>
        </div>

        <div
          v-if="activeWorkflows.length === 0"
          class="text-center py-12 text-gray-500 dark:text-gray-400"
        >
          No active workflows. Launch one from the Templates tab.
        </div>
      </div>

      <!-- History -->
      <div v-if="activeTab === 'history'">
        <!-- Filters -->
        <div class="mb-4 flex gap-2">
          <button
            v-for="status in ['all', 'succeeded', 'failed', 'error']"
            :key="status"
            :class="[
              'px-3 py-1 text-sm rounded-full transition-colors',
              filterStatus === status
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            ]"
            @click="filterStatus = status"
          >
            {{ status.charAt(0).toUpperCase() + status.slice(1) }}
          </button>
        </div>

        <div class="space-y-4">
          <div
            v-for="workflow in historyWorkflows"
            :key="workflow.id"
            class="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <span class="text-2xl">{{ typeIcons[workflow.type] }}</span>
                <div>
                  <h3 class="font-semibold text-gray-900 dark:text-white">
                    {{ workflow.name }}
                  </h3>
                  <div class="flex items-center gap-3 mt-1">
                    <span :class="['px-2 py-1 text-xs font-medium rounded-full', statusColors[workflow.status]]">
                      {{ workflow.status }}
                    </span>
                    <span class="text-sm text-gray-500 dark:text-gray-400">
                      Duration: {{ formatDuration(workflow.duration) }}
                    </span>
                  </div>
                </div>
              </div>
              <div class="flex gap-2">
                <button
                  class="px-3 py-1 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                  @click="viewLogs(workflow.id)"
                >
                  📜 Logs
                </button>
                <button
                  v-if="workflow.status === 'failed'"
                  class="px-3 py-1 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
                  @click="retryWorkflow(workflow.id)"
                >
                  🔄 Retry
                </button>
              </div>
            </div>
            <div class="mt-3 text-sm text-gray-500 dark:text-gray-400">
              Finished: {{ formatDate(workflow.finished_at) }} · Triggered by: {{ workflow.triggered_by }}
            </div>
          </div>
        </div>
      </div>

      <!-- Templates -->
      <div v-if="activeTab === 'templates'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="template in templates"
          :key="template.id"
          class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer"
          @click="openLaunchModal(template)"
        >
          <div class="flex items-start gap-3 mb-3">
            <span class="text-2xl">{{ typeIcons[template.type] }}</span>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ template.name }}
              </h3>
              <span class="text-xs text-gray-500 dark:text-gray-400">
                Est. {{ formatDuration(template.estimated_duration) }}
              </span>
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">
            {{ template.description }}
          </p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="input in template.inputs"
              :key="input.name"
              :class="[
                'px-2 py-1 text-xs rounded',
                input.required
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
              ]"
            >
              {{ input.name }}{{ input.required ? '*' : '' }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- Launch Modal -->
    <div
      v-if="showLaunchModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showLaunchModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Launch Workflow
        </h2>
        <div v-if="selectedTemplate" class="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div class="font-medium text-gray-900 dark:text-white">
            {{ selectedTemplate.name }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            {{ selectedTemplate.description }}
          </div>
          <div class="text-xs text-gray-400 mt-2">
            Estimated duration: {{ formatDuration(selectedTemplate.estimated_duration) }}
          </div>
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-300 mb-4">
          This will start a new workflow execution. You can monitor its progress in the Active tab.
        </div>
        <div class="flex justify-end gap-3">
          <button
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            @click="showLaunchModal = false"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            @click="launchWorkflow"
          >
            🚀 Launch
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workflows-page {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .workflows-page {
    background-color: #111827;
  }
}
</style>
