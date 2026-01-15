<script lang="ts" setup>
/**
 * Agentic Tools - MCP Tool Security Management
 * 
 * Manage and govern tools/capabilities available to AI agents,
 * including approval workflows and risk assessment.
 */
import { ref, onMounted, computed } from 'vue';

interface Tool {
  id: string;
  name: string;
  description: string;
  category: 'filesystem' | 'network' | 'code_execution' | 'external_api' | 'database';
  risk_level: 'critical' | 'high' | 'medium' | 'low';
  requires_approval: boolean;
  allowed_agents: string[] | null;
  usage_count_24h: number;
  last_used: string | null;
  enabled: boolean;
}

interface PendingApproval {
  id: string;
  tool_name: string;
  agent_name: string;
  agent_id: string;
  justification: string;
  requested_at: string;
}

const loading = ref(true);
const tools = ref<Tool[]>([]);
const pendingApprovals = ref<PendingApproval[]>([]);
const selectedCategory = ref<string>('all');
const searchQuery = ref('');

const categories = ['all', 'filesystem', 'network', 'code_execution', 'external_api', 'database'];

const categoryIcons: Record<string, string> = {
  filesystem: '📁',
  network: '🌐',
  code_execution: '⚡',
  external_api: '🔌',
  database: '🗄️',
};

const riskColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  low: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
};

const filteredTools = computed(() => {
  return tools.value.filter(tool => {
    const matchesCategory = selectedCategory.value === 'all' || tool.category === selectedCategory.value;
    const matchesSearch = !searchQuery.value || 
      tool.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.value.toLowerCase());
    return matchesCategory && matchesSearch;
  });
});

async function fetchData() {
  loading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    tools.value = [
      {
        id: '1',
        name: 'file_read',
        description: 'Read contents of a file from the filesystem',
        category: 'filesystem',
        risk_level: 'medium',
        requires_approval: false,
        allowed_agents: null,
        usage_count_24h: 234,
        last_used: new Date(Date.now() - 5 * 60000).toISOString(),
        enabled: true,
      },
      {
        id: '2',
        name: 'file_write',
        description: 'Write or modify files on the filesystem',
        category: 'filesystem',
        risk_level: 'high',
        requires_approval: true,
        allowed_agents: ['agent-code-002'],
        usage_count_24h: 56,
        last_used: new Date(Date.now() - 15 * 60000).toISOString(),
        enabled: true,
      },
      {
        id: '3',
        name: 'code_execute',
        description: 'Execute arbitrary code in a sandboxed environment',
        category: 'code_execution',
        risk_level: 'critical',
        requires_approval: true,
        allowed_agents: ['agent-code-002'],
        usage_count_24h: 89,
        last_used: new Date(Date.now() - 2 * 60000).toISOString(),
        enabled: true,
      },
      {
        id: '4',
        name: 'http_request',
        description: 'Make HTTP requests to external APIs',
        category: 'network',
        risk_level: 'high',
        requires_approval: false,
        allowed_agents: null,
        usage_count_24h: 456,
        last_used: new Date(Date.now() - 1 * 60000).toISOString(),
        enabled: true,
      },
      {
        id: '5',
        name: 'database_query',
        description: 'Execute read-only database queries',
        category: 'database',
        risk_level: 'medium',
        requires_approval: false,
        allowed_agents: null,
        usage_count_24h: 123,
        last_used: new Date(Date.now() - 30 * 60000).toISOString(),
        enabled: true,
      },
      {
        id: '6',
        name: 'shell_execute',
        description: 'Execute shell commands on the host system',
        category: 'code_execution',
        risk_level: 'critical',
        requires_approval: true,
        allowed_agents: [],
        usage_count_24h: 0,
        last_used: null,
        enabled: false,
      },
    ];

    pendingApprovals.value = [
      {
        id: '1',
        tool_name: 'code_execute',
        agent_name: 'Deployment Agent',
        agent_id: 'agent-deploy-003',
        justification: 'Need to run deployment verification script',
        requested_at: new Date(Date.now() - 10 * 60000).toISOString(),
      },
      {
        id: '2',
        tool_name: 'file_write',
        agent_name: 'Research Assistant',
        agent_id: 'agent-research-001',
        justification: 'Save research findings to output file',
        requested_at: new Date(Date.now() - 25 * 60000).toISOString(),
      },
    ];
  } finally {
    loading.value = false;
  }
}

async function toggleTool(toolId: string) {
  const tool = tools.value.find(t => t.id === toolId);
  if (tool) {
    tool.enabled = !tool.enabled;
  }
}

async function approveRequest(approvalId: string) {
  pendingApprovals.value = pendingApprovals.value.filter(a => a.id !== approvalId);
  alert('Tool usage approved');
}

async function denyRequest(approvalId: string) {
  pendingApprovals.value = pendingApprovals.value.filter(a => a.id !== approvalId);
  alert('Tool usage denied');
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Never';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return date.toLocaleDateString();
}

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="tools-page p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Tool Governance
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Manage MCP tools and capabilities available to AI agents
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="fetchData"
      >
        🔄 Refresh
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <template v-else>
      <!-- Pending Approvals -->
      <div
        v-if="pendingApprovals.length > 0"
        class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6"
      >
        <h3 class="font-medium text-yellow-800 dark:text-yellow-200 mb-3">
          ⏳ Pending Approval Requests ({{ pendingApprovals.length }})
        </h3>
        <div class="space-y-3">
          <div
            v-for="approval in pendingApprovals"
            :key="approval.id"
            class="bg-white dark:bg-gray-800 rounded-lg p-4 flex items-center justify-between"
          >
            <div>
              <div class="font-medium text-gray-900 dark:text-white">
                {{ approval.agent_name }} wants to use <code class="px-1 bg-gray-100 dark:bg-gray-700 rounded">{{ approval.tool_name }}</code>
              </div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {{ approval.justification }}
              </div>
              <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">
                Requested {{ formatDate(approval.requested_at) }}
              </div>
            </div>
            <div class="flex gap-2">
              <button
                class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                @click="approveRequest(approval.id)"
              >
                ✓ Approve
              </button>
              <button
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                @click="denyRequest(approval.id)"
              >
                ✕ Deny
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
        <div class="flex flex-wrap gap-4 items-center">
          <div class="flex-1 min-w-[200px]">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search tools..."
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <div class="flex gap-2">
            <button
              v-for="cat in categories"
              :key="cat"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                selectedCategory === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              ]"
              @click="selectedCategory = cat"
            >
              {{ cat === 'all' ? 'All' : (categoryIcons[cat] || '') + ' ' + cat.replace('_', ' ') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Tools Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="tool in filteredTools"
          :key="tool.id"
          :class="[
            'bg-white dark:bg-gray-800 rounded-lg shadow p-6',
            !tool.enabled && 'opacity-60'
          ]"
        >
          <div class="flex items-start justify-between mb-4">
            <div class="flex items-center gap-3">
              <span class="text-2xl">{{ categoryIcons[tool.category] || '🔧' }}</span>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">
                  {{ tool.name }}
                </h3>
                <span :class="['text-xs px-2 py-0.5 rounded-full', riskColors[tool.risk_level]]">
                  {{ tool.risk_level }}
                </span>
              </div>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="tool.enabled"
                class="sr-only peer"
                @change="toggleTool(tool.id)"
              />
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">
            {{ tool.description }}
          </p>

          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-4">
              <span class="text-gray-500 dark:text-gray-400">
                📊 {{ tool.usage_count_24h }} uses (24h)
              </span>
            </div>
            <span v-if="tool.requires_approval" class="text-orange-500">
              🔒 Requires approval
            </span>
          </div>

          <div class="mt-3 text-xs text-gray-400 dark:text-gray-500">
            Last used: {{ formatDate(tool.last_used) }}
          </div>

          <div v-if="tool.allowed_agents && tool.allowed_agents.length > 0" class="mt-3">
            <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">Allowed agents:</div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="agent in tool.allowed_agents"
                :key="agent"
                class="px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded"
              >
                {{ agent }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.tools-page {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .tools-page {
    background-color: #111827;
  }
}
</style>
