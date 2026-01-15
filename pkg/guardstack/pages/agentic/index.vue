<script lang="ts" setup>
/**
 * Agentic AI Dashboard - Agent Monitoring Overview
 * 
 * Monitor and manage autonomous AI agents with real-time
 * activity tracking, tool governance, and risk assessment.
 */
import { ref, onMounted, computed } from 'vue';

interface AgentSession {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_type: 'autonomous' | 'semi-autonomous' | 'supervised';
  status: 'active' | 'paused' | 'terminated';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  total_actions: number;
  tool_calls: number;
  tokens_used: number;
  started_at: string;
  last_activity: string;
}

interface AgentAlert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  agent_id: string;
  acknowledged: boolean;
  created_at: string;
}

const loading = ref(true);
const sessions = ref<AgentSession[]>([]);
const alerts = ref<AgentAlert[]>([]);
const metrics = ref({
  active_sessions: 0,
  total_actions_24h: 0,
  tool_calls_24h: 0,
  tokens_consumed_24h: 0,
  pending_approvals: 0,
  high_risk_sessions: 0,
});

const riskColors: Record<string, string> = {
  low: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const statusColors: Record<string, string> = {
  active: 'bg-green-500',
  paused: 'bg-yellow-500',
  terminated: 'bg-gray-500',
};

const activeSessions = computed(() => sessions.value.filter(s => s.status === 'active'));
const unacknowledgedAlerts = computed(() => alerts.value.filter(a => !a.acknowledged));

async function fetchData() {
  loading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    sessions.value = [
      {
        id: '1',
        agent_id: 'agent-research-001',
        agent_name: 'Research Assistant',
        agent_type: 'semi-autonomous',
        status: 'active',
        risk_level: 'low',
        total_actions: 145,
        tool_calls: 23,
        tokens_used: 45000,
        started_at: new Date(Date.now() - 2 * 3600000).toISOString(),
        last_activity: new Date(Date.now() - 5 * 60000).toISOString(),
      },
      {
        id: '2',
        agent_id: 'agent-code-002',
        agent_name: 'Code Assistant',
        agent_type: 'supervised',
        status: 'active',
        risk_level: 'medium',
        total_actions: 89,
        tool_calls: 56,
        tokens_used: 120000,
        started_at: new Date(Date.now() - 1 * 3600000).toISOString(),
        last_activity: new Date(Date.now() - 1 * 60000).toISOString(),
      },
      {
        id: '3',
        agent_id: 'agent-deploy-003',
        agent_name: 'Deployment Agent',
        agent_type: 'autonomous',
        status: 'paused',
        risk_level: 'high',
        total_actions: 234,
        tool_calls: 89,
        tokens_used: 87000,
        started_at: new Date(Date.now() - 4 * 3600000).toISOString(),
        last_activity: new Date(Date.now() - 30 * 60000).toISOString(),
      },
    ];

    alerts.value = [
      {
        id: '1',
        severity: 'critical',
        title: 'Agent attempting unauthorized resource access',
        description: 'Agent agent-deploy-003 attempted to access production secrets',
        agent_id: 'agent-deploy-003',
        acknowledged: false,
        created_at: new Date(Date.now() - 5 * 60000).toISOString(),
      },
      {
        id: '2',
        severity: 'high',
        title: 'Unusual tool invocation pattern',
        description: 'Agent agent-code-002 made 50+ code_execute calls in 5 minutes',
        agent_id: 'agent-code-002',
        acknowledged: false,
        created_at: new Date(Date.now() - 15 * 60000).toISOString(),
      },
    ];

    metrics.value = {
      active_sessions: 3,
      total_actions_24h: 1247,
      tool_calls_24h: 456,
      tokens_consumed_24h: 2500000,
      pending_approvals: 2,
      high_risk_sessions: 1,
    };
  } finally {
    loading.value = false;
  }
}

async function pauseAgent(sessionId: string) {
  const session = sessions.value.find(s => s.id === sessionId);
  if (session) {
    session.status = 'paused';
  }
}

async function terminateAgent(sessionId: string) {
  if (confirm('Are you sure you want to terminate this agent session?')) {
    const session = sessions.value.find(s => s.id === sessionId);
    if (session) {
      session.status = 'terminated';
    }
  }
}

async function acknowledgeAlert(alertId: string) {
  const alert = alerts.value.find(a => a.id === alertId);
  if (alert) {
    alert.acknowledged = true;
  }
}

function formatDuration(startTime: string): string {
  const start = new Date(startTime).getTime();
  const now = Date.now();
  const diff = Math.floor((now - start) / 1000);
  
  if (diff < 60) return `${diff}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

onMounted(() => {
  fetchData();
  // Poll for updates every 30 seconds
  setInterval(fetchData, 30000);
});
</script>

<template>
  <div class="agentic-dashboard p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Agentic AI Security
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Monitor and govern autonomous AI agents
        </p>
      </div>
      <div class="flex gap-3">
        <button
          class="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          @click="fetchData"
        >
          🔄 Refresh
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <template v-else>
      <!-- Alerts Banner -->
      <div
        v-if="unacknowledgedAlerts.length > 0"
        class="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="text-2xl">⚠️</span>
            <div>
              <div class="font-medium text-red-800 dark:text-red-200">
                {{ unacknowledgedAlerts.length }} Active Alert{{ unacknowledgedAlerts.length > 1 ? 's' : '' }}
              </div>
              <div class="text-sm text-red-600 dark:text-red-300">
                {{ unacknowledgedAlerts[0].title }}
              </div>
            </div>
          </div>
          <button
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            @click="acknowledgeAlert(unacknowledgedAlerts[0].id)"
          >
            Acknowledge
          </button>
        </div>
      </div>

      <!-- Metrics Cards -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ metrics.active_sessions }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Active Sessions</div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ formatNumber(metrics.total_actions_24h) }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Actions (24h)</div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ formatNumber(metrics.tool_calls_24h) }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Tool Calls (24h)</div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ formatNumber(metrics.tokens_consumed_24h) }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Tokens (24h)</div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div class="text-2xl font-bold text-orange-500">
            {{ metrics.pending_approvals }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">Pending Approvals</div>
        </div>
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div class="text-2xl font-bold text-red-500">
            {{ metrics.high_risk_sessions }}
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">High Risk</div>
        </div>
      </div>

      <!-- Active Sessions -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Active Agent Sessions
        </h2>
        <div class="space-y-4">
          <div
            v-for="session in activeSessions"
            :key="session.id"
            class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="relative">
                  <div class="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-xl">
                    🤖
                  </div>
                  <div
                    :class="['absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white dark:border-gray-800', statusColors[session.status]]"
                  ></div>
                </div>
                <div>
                  <div class="font-medium text-gray-900 dark:text-white">
                    {{ session.agent_name }}
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {{ session.agent_id }} • {{ session.agent_type }}
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-6">
                <div class="text-center">
                  <div class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ session.total_actions }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Actions</div>
                </div>
                <div class="text-center">
                  <div class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ session.tool_calls }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Tool Calls</div>
                </div>
                <div class="text-center">
                  <div class="text-lg font-semibold text-gray-900 dark:text-white">
                    {{ formatDuration(session.started_at) }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Duration</div>
                </div>
                <span :class="['px-3 py-1 text-xs font-medium rounded-full', riskColors[session.risk_level]]">
                  {{ session.risk_level.toUpperCase() }}
                </span>
                <div class="flex gap-2">
                  <button
                    class="p-2 text-gray-400 hover:text-yellow-500"
                    title="Pause"
                    @click="pauseAgent(session.id)"
                  >
                    ⏸️
                  </button>
                  <button
                    class="p-2 text-gray-400 hover:text-red-500"
                    title="Terminate"
                    @click="terminateAgent(session.id)"
                  >
                    ⏹️
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          href="/agentic/tools"
          class="bg-white dark:bg-gray-800 rounded-xl shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">🔧</span>
            <div>
              <div class="font-medium text-gray-900 dark:text-white">Tool Governance</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                Manage agent tool permissions
              </div>
            </div>
          </div>
        </a>

        <a
          href="/agentic/sessions"
          class="bg-white dark:bg-gray-800 rounded-xl shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">📋</span>
            <div>
              <div class="font-medium text-gray-900 dark:text-white">Session History</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                Review past agent sessions
              </div>
            </div>
          </div>
        </a>

        <a
          href="/settings/policies"
          class="bg-white dark:bg-gray-800 rounded-xl shadow p-6 hover:shadow-lg transition-shadow"
        >
          <div class="flex items-center gap-3">
            <span class="text-2xl">⚙️</span>
            <div>
              <div class="font-medium text-gray-900 dark:text-white">Agent Policies</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">
                Configure agent constraints
              </div>
            </div>
          </div>
        </a>
      </div>
    </template>
  </div>
</template>

<style scoped>
.agentic-dashboard {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .agentic-dashboard {
    background-color: #111827;
  }
}
</style>
