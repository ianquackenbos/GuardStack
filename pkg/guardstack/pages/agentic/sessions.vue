<script lang="ts" setup>
/**
 * Agentic Sessions - Agent Session Management
 * 
 * View and manage agent sessions with detailed action logs,
 * timeline visualization, and session controls.
 */
import { ref, onMounted, computed } from 'vue';

interface AgentSession {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: string;
  model_id: string;
  status: 'active' | 'paused' | 'terminated';
  risk_level: string;
  total_actions: number;
  tool_calls: number;
  tokens_used: number;
  started_at: string;
  last_activity: string;
  terminated_at: string | null;
}

interface ActionLog {
  id: string;
  action_type: 'tool_call' | 'decision' | 'api_request' | 'output';
  tool_name: string | null;
  input_summary: string;
  output_summary: string;
  risk_flags: string[];
  tokens_used: number;
  latency_ms: number;
  status: string;
  timestamp: string;
}

const loading = ref(true);
const sessions = ref<AgentSession[]>([]);
const selectedSession = ref<AgentSession | null>(null);
const actionLogs = ref<ActionLog[]>([]);
const statusFilter = ref<string>('all');

const statusOptions = ['all', 'active', 'paused', 'terminated'];

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  paused: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  terminated: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
};

const actionTypeIcons: Record<string, string> = {
  tool_call: '🔧',
  decision: '🤔',
  api_request: '🌐',
  output: '📤',
};

const filteredSessions = computed(() => {
  return sessions.value.filter(session => {
    return statusFilter.value === 'all' || session.status === statusFilter.value;
  });
});

async function fetchSessions() {
  loading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    sessions.value = [
      {
        id: '1',
        agent_id: 'agent-research-001',
        agent_name: 'Research Assistant',
        agent_type: 'semi-autonomous',
        model_id: 'gpt-4-turbo',
        status: 'active',
        risk_level: 'low',
        total_actions: 145,
        tool_calls: 23,
        tokens_used: 45000,
        started_at: new Date(Date.now() - 2 * 3600000).toISOString(),
        last_activity: new Date(Date.now() - 5 * 60000).toISOString(),
        terminated_at: null,
      },
      {
        id: '2',
        agent_id: 'agent-code-002',
        agent_name: 'Code Assistant',
        agent_type: 'supervised',
        model_id: 'claude-3-opus',
        status: 'active',
        risk_level: 'medium',
        total_actions: 89,
        tool_calls: 56,
        tokens_used: 120000,
        started_at: new Date(Date.now() - 1 * 3600000).toISOString(),
        last_activity: new Date(Date.now() - 1 * 60000).toISOString(),
        terminated_at: null,
      },
      {
        id: '3',
        agent_id: 'agent-deploy-003',
        agent_name: 'Deployment Agent',
        agent_type: 'autonomous',
        model_id: 'gpt-4',
        status: 'paused',
        risk_level: 'high',
        total_actions: 234,
        tool_calls: 89,
        tokens_used: 87000,
        started_at: new Date(Date.now() - 4 * 3600000).toISOString(),
        last_activity: new Date(Date.now() - 30 * 60000).toISOString(),
        terminated_at: null,
      },
      {
        id: '4',
        agent_id: 'agent-analysis-004',
        agent_name: 'Data Analyst',
        agent_type: 'supervised',
        model_id: 'gpt-4',
        status: 'terminated',
        risk_level: 'low',
        total_actions: 567,
        tool_calls: 123,
        tokens_used: 250000,
        started_at: new Date(Date.now() - 24 * 3600000).toISOString(),
        last_activity: new Date(Date.now() - 20 * 3600000).toISOString(),
        terminated_at: new Date(Date.now() - 20 * 3600000).toISOString(),
      },
    ];
  } finally {
    loading.value = false;
  }
}

async function fetchActionLogs(sessionId: string) {
  await new Promise(resolve => setTimeout(resolve, 300));
  
  actionLogs.value = [
    {
      id: '1',
      action_type: 'tool_call',
      tool_name: 'file_read',
      input_summary: 'Read config.yaml from /app/config/',
      output_summary: 'Successfully read 245 bytes',
      risk_flags: [],
      tokens_used: 150,
      latency_ms: 45,
      status: 'completed',
      timestamp: new Date(Date.now() - 10 * 60000).toISOString(),
    },
    {
      id: '2',
      action_type: 'decision',
      tool_name: null,
      input_summary: 'Analyzing configuration options',
      output_summary: 'Decided to update database connection settings',
      risk_flags: ['configuration_change'],
      tokens_used: 500,
      latency_ms: 120,
      status: 'completed',
      timestamp: new Date(Date.now() - 8 * 60000).toISOString(),
    },
    {
      id: '3',
      action_type: 'api_request',
      tool_name: 'http_request',
      input_summary: 'GET https://api.internal/health',
      output_summary: '200 OK - Service healthy',
      risk_flags: [],
      tokens_used: 100,
      latency_ms: 230,
      status: 'completed',
      timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    },
    {
      id: '4',
      action_type: 'tool_call',
      tool_name: 'code_execute',
      input_summary: 'Running validation script',
      output_summary: 'Script executed successfully, 3 tests passed',
      risk_flags: ['code_execution'],
      tokens_used: 300,
      latency_ms: 1500,
      status: 'completed',
      timestamp: new Date(Date.now() - 3 * 60000).toISOString(),
    },
    {
      id: '5',
      action_type: 'output',
      tool_name: null,
      input_summary: 'Generating summary report',
      output_summary: 'Report generated with 5 findings',
      risk_flags: [],
      tokens_used: 200,
      latency_ms: 80,
      status: 'completed',
      timestamp: new Date(Date.now() - 1 * 60000).toISOString(),
    },
  ];
}

async function selectSession(session: AgentSession) {
  selectedSession.value = session;
  await fetchActionLogs(session.id);
}

async function terminateSession(sessionId: string) {
  if (confirm('Are you sure you want to terminate this session?')) {
    const session = sessions.value.find(s => s.id === sessionId);
    if (session) {
      session.status = 'terminated';
      session.terminated_at = new Date().toISOString();
    }
  }
}

async function pauseSession(sessionId: string) {
  const session = sessions.value.find(s => s.id === sessionId);
  if (session) {
    session.status = 'paused';
  }
}

async function resumeSession(sessionId: string) {
  const session = sessions.value.find(s => s.id === sessionId);
  if (session) {
    session.status = 'active';
  }
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

function formatDuration(startTime: string, endTime?: string | null): string {
  const start = new Date(startTime).getTime();
  const end = endTime ? new Date(endTime).getTime() : Date.now();
  const diff = Math.floor((end - start) / 1000);
  
  const hours = Math.floor(diff / 3600);
  const minutes = Math.floor((diff % 3600) / 60);
  const seconds = diff % 60;
  
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

function formatTokens(tokens: number): string {
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`;
  return tokens.toString();
}

onMounted(() => {
  fetchSessions();
});
</script>

<template>
  <div class="sessions-page p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Agent Sessions
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Monitor and manage agent session history and activity logs
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="fetchSessions"
      >
        🔄 Refresh
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <template v-else>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Sessions List -->
        <div class="lg:col-span-1">
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow">
            <!-- Filter -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
              <select
                v-model="statusFilter"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option v-for="opt in statusOptions" :key="opt" :value="opt">
                  {{ opt === 'all' ? 'All Sessions' : opt.charAt(0).toUpperCase() + opt.slice(1) }}
                </option>
              </select>
            </div>

            <!-- Session List -->
            <div class="divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
              <button
                v-for="session in filteredSessions"
                :key="session.id"
                :class="[
                  'w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors',
                  selectedSession?.id === session.id && 'bg-blue-50 dark:bg-blue-900/20'
                ]"
                @click="selectSession(session)"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="font-medium text-gray-900 dark:text-white">
                    {{ session.agent_name }}
                  </span>
                  <span :class="['px-2 py-0.5 text-xs rounded-full', statusColors[session.status]]">
                    {{ session.status }}
                  </span>
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">
                  {{ session.agent_id }}
                </div>
                <div class="flex items-center gap-4 mt-2 text-xs text-gray-400 dark:text-gray-500">
                  <span>{{ session.total_actions }} actions</span>
                  <span>{{ formatTokens(session.tokens_used) }} tokens</span>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- Session Detail -->
        <div class="lg:col-span-2">
          <div v-if="selectedSession" class="space-y-6">
            <!-- Session Info -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div class="flex items-start justify-between mb-4">
                <div>
                  <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                    {{ selectedSession.agent_name }}
                  </h2>
                  <p class="text-gray-500 dark:text-gray-400">
                    {{ selectedSession.agent_id }} • {{ selectedSession.agent_type }}
                  </p>
                </div>
                <div class="flex gap-2">
                  <button
                    v-if="selectedSession.status === 'active'"
                    class="px-3 py-1 text-sm bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded-lg hover:bg-yellow-200 dark:hover:bg-yellow-800"
                    @click="pauseSession(selectedSession.id)"
                  >
                    ⏸️ Pause
                  </button>
                  <button
                    v-if="selectedSession.status === 'paused'"
                    class="px-3 py-1 text-sm bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded-lg hover:bg-green-200 dark:hover:bg-green-800"
                    @click="resumeSession(selectedSession.id)"
                  >
                    ▶️ Resume
                  </button>
                  <button
                    v-if="selectedSession.status !== 'terminated'"
                    class="px-3 py-1 text-sm bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 rounded-lg hover:bg-red-200 dark:hover:bg-red-800"
                    @click="terminateSession(selectedSession.id)"
                  >
                    ⏹️ Terminate
                  </button>
                </div>
              </div>

              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <div class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ selectedSession.total_actions }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Total Actions</div>
                </div>
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <div class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ selectedSession.tool_calls }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Tool Calls</div>
                </div>
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <div class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ formatTokens(selectedSession.tokens_used) }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Tokens Used</div>
                </div>
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                  <div class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ formatDuration(selectedSession.started_at, selectedSession.terminated_at) }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Duration</div>
                </div>
              </div>

              <div class="mt-4 text-sm text-gray-500 dark:text-gray-400">
                <div>Started: {{ formatDate(selectedSession.started_at) }}</div>
                <div>Last Activity: {{ formatDate(selectedSession.last_activity) }}</div>
                <div v-if="selectedSession.terminated_at">
                  Terminated: {{ formatDate(selectedSession.terminated_at) }}
                </div>
              </div>
            </div>

            <!-- Action Timeline -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Action Timeline
              </h3>
              <div class="space-y-4">
                <div
                  v-for="action in actionLogs"
                  :key="action.id"
                  class="flex gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div class="text-2xl">
                    {{ actionTypeIcons[action.action_type] }}
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center justify-between mb-1">
                      <span class="font-medium text-gray-900 dark:text-white">
                        {{ action.action_type.replace('_', ' ').toUpperCase() }}
                        <span v-if="action.tool_name" class="text-gray-500 dark:text-gray-400">
                          - {{ action.tool_name }}
                        </span>
                      </span>
                      <span class="text-xs text-gray-400 dark:text-gray-500">
                        {{ formatDate(action.timestamp) }}
                      </span>
                    </div>
                    <div class="text-sm text-gray-600 dark:text-gray-300 mb-1">
                      {{ action.input_summary }}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                      → {{ action.output_summary }}
                    </div>
                    <div class="flex items-center gap-4 mt-2 text-xs text-gray-400 dark:text-gray-500">
                      <span>{{ action.tokens_used }} tokens</span>
                      <span>{{ action.latency_ms }}ms</span>
                      <span
                        v-for="flag in action.risk_flags"
                        :key="flag"
                        class="px-2 py-0.5 bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200 rounded"
                      >
                        ⚠️ {{ flag }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div
            v-else
            class="bg-white dark:bg-gray-800 rounded-lg shadow p-12 text-center"
          >
            <div class="text-4xl mb-4">📋</div>
            <div class="text-gray-500 dark:text-gray-400">
              Select a session to view details
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.sessions-page {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .sessions-page {
    background-color: #111827;
  }
}
</style>
