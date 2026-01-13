<script lang="ts" setup>
/**
 * Settings - Guardrails Page
 * Configure runtime guardrails and content filters
 */
import { ref, onMounted } from 'vue';
import StatusBadge from '../../components/StatusBadge.vue';

interface Guardrail {
  id: string;
  name: string;
  type: 'pii' | 'toxicity' | 'jailbreak' | 'topic' | 'custom';
  enabled: boolean;
  mode: 'block' | 'warn' | 'log';
  threshold?: number;
  config: Record<string, unknown>;
  stats?: {
    triggered: number;
    blocked: number;
    lastTriggered?: string;
  };
}

const loading = ref(true);
const guardrails = ref<Guardrail[]>([]);
const showAddModal = ref(false);
const showEditModal = ref(false);
const selectedGuardrail = ref<Guardrail | null>(null);

const guardrailTypes = [
  {
    id: 'pii',
    name: 'PII Detection',
    icon: '🔐',
    description: 'Detect and redact personally identifiable information',
    hasThreshold: true,
  },
  {
    id: 'toxicity',
    name: 'Toxicity Filter',
    icon: '⚠️',
    description: 'Detect toxic, harmful, or offensive content',
    hasThreshold: true,
  },
  {
    id: 'jailbreak',
    name: 'Jailbreak Detection',
    icon: '🛡️',
    description: 'Detect prompt injection and jailbreak attempts',
    hasThreshold: true,
  },
  {
    id: 'topic',
    name: 'Topic Filter',
    icon: '📋',
    description: 'Restrict conversation to specific topics',
    hasThreshold: false,
  },
];

const newGuardrail = ref({
  name: '',
  type: 'pii' as const,
  mode: 'block' as const,
  threshold: 0.8,
  topics: '',
});

function toggleGuardrail(guardrail: Guardrail) {
  guardrail.enabled = !guardrail.enabled;
}

function updateMode(guardrail: Guardrail, mode: 'block' | 'warn' | 'log') {
  guardrail.mode = mode;
}

async function addGuardrail() {
  const guardrail: Guardrail = {
    id: `guardrail-${Date.now()}`,
    name: newGuardrail.value.name,
    type: newGuardrail.value.type,
    enabled: true,
    mode: newGuardrail.value.mode,
    threshold: guardrailTypes.find(t => t.id === newGuardrail.value.type)?.hasThreshold 
      ? newGuardrail.value.threshold 
      : undefined,
    config: newGuardrail.value.type === 'topic' 
      ? { topics: newGuardrail.value.topics.split(',').map(t => t.trim()) }
      : {},
    stats: {
      triggered: 0,
      blocked: 0,
    },
  };
  
  guardrails.value.push(guardrail);
  showAddModal.value = false;
  
  // Reset form
  newGuardrail.value = {
    name: '',
    type: 'pii',
    mode: 'block',
    threshold: 0.8,
    topics: '',
  };
}

function editGuardrail(guardrail: Guardrail) {
  selectedGuardrail.value = guardrail;
  showEditModal.value = true;
}

function deleteGuardrail(guardrail: Guardrail) {
  if (confirm(`Are you sure you want to delete "${guardrail.name}"?`)) {
    guardrails.value = guardrails.value.filter(g => g.id !== guardrail.id);
  }
}

onMounted(() => {
  guardrails.value = [
    {
      id: 'guardrail-1',
      name: 'PII Redaction',
      type: 'pii',
      enabled: true,
      mode: 'block',
      threshold: 0.9,
      config: {},
      stats: {
        triggered: 1247,
        blocked: 1189,
        lastTriggered: '2024-06-01T10:15:00Z',
      },
    },
    {
      id: 'guardrail-2',
      name: 'Toxicity Check',
      type: 'toxicity',
      enabled: true,
      mode: 'warn',
      threshold: 0.7,
      config: {},
      stats: {
        triggered: 89,
        blocked: 45,
        lastTriggered: '2024-06-01T09:30:00Z',
      },
    },
    {
      id: 'guardrail-3',
      name: 'Jailbreak Protection',
      type: 'jailbreak',
      enabled: true,
      mode: 'block',
      threshold: 0.85,
      config: {},
      stats: {
        triggered: 23,
        blocked: 23,
        lastTriggered: '2024-05-31T22:45:00Z',
      },
    },
  ];
  loading.value = false;
});
</script>

<template>
  <div class="settings-guardrails p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Guardrails
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Configure runtime guardrails and content filters
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="showAddModal = true"
      >
        Add Guardrail
      </button>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <template v-else>
      <!-- Guardrails list -->
      <div v-if="guardrails.length > 0" class="space-y-4">
        <div
          v-for="guardrail in guardrails"
          :key="guardrail.id"
          :class="[
            'bg-white dark:bg-gray-800 rounded-lg border p-4',
            !guardrail.enabled && 'opacity-60',
          ]"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="text-2xl">
                {{ guardrailTypes.find(t => t.id === guardrail.type)?.icon || '🛡️' }}
              </span>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-gray-100">
                  {{ guardrail.name }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ guardrailTypes.find(t => t.id === guardrail.type)?.description }}
                </p>
              </div>
            </div>
            
            <!-- Toggle -->
            <button
              :class="[
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                guardrail.enabled ? 'bg-blue-600' : 'bg-gray-300',
              ]"
              @click="toggleGuardrail(guardrail)"
            >
              <span
                :class="[
                  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                  guardrail.enabled ? 'translate-x-6' : 'translate-x-1',
                ]"
              />
            </button>
          </div>
          
          <!-- Config row -->
          <div class="flex items-center gap-6 mb-3">
            <!-- Mode selector -->
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">Mode:</span>
              <div class="flex border rounded-lg overflow-hidden">
                <button
                  v-for="mode in ['block', 'warn', 'log']"
                  :key="mode"
                  :class="[
                    'px-3 py-1 text-sm capitalize',
                    guardrail.mode === mode 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white dark:bg-gray-800 hover:bg-gray-50',
                  ]"
                  @click="updateMode(guardrail, mode as 'block' | 'warn' | 'log')"
                >
                  {{ mode }}
                </button>
              </div>
            </div>
            
            <!-- Threshold -->
            <div v-if="guardrail.threshold !== undefined" class="flex items-center gap-2">
              <span class="text-sm text-gray-500">Threshold:</span>
              <input
                v-model.number="guardrail.threshold"
                type="range"
                min="0"
                max="1"
                step="0.05"
                class="w-24"
              />
              <span class="text-sm font-medium">{{ Math.round(guardrail.threshold * 100) }}%</span>
            </div>
          </div>
          
          <!-- Stats -->
          <div class="flex items-center justify-between pt-3 border-t">
            <div class="flex items-center gap-6 text-sm">
              <span class="text-gray-500">
                Triggered: <span class="font-medium text-gray-700 dark:text-gray-300">{{ guardrail.stats?.triggered || 0 }}</span>
              </span>
              <span class="text-gray-500">
                Blocked: <span class="font-medium text-gray-700 dark:text-gray-300">{{ guardrail.stats?.blocked || 0 }}</span>
              </span>
              <span v-if="guardrail.stats?.lastTriggered" class="text-gray-500">
                Last: {{ new Date(guardrail.stats.lastTriggered).toLocaleString() }}
              </span>
            </div>
            
            <div class="flex items-center gap-2">
              <button
                class="text-sm text-gray-600 hover:underline"
                @click="editGuardrail(guardrail)"
              >
                Configure
              </button>
              <button
                class="text-sm text-red-600 hover:underline"
                @click="deleteGuardrail(guardrail)"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-else class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
        <span class="text-4xl">🛡️</span>
        <h3 class="mt-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
          No guardrails configured
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mt-2">
          Add guardrails to protect your AI applications
        </p>
        <button
          class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          @click="showAddModal = true"
        >
          Add Guardrail
        </button>
      </div>
    </template>
    
    <!-- Add modal -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showAddModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
        <div class="flex items-start justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Add Guardrail
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="showAddModal = false"
          >
            ✕
          </button>
        </div>
        
        <form @submit.prevent="addGuardrail" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name
            </label>
            <input
              v-model="newGuardrail.name"
              type="text"
              required
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="My Guardrail"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Type
            </label>
            <select
              v-model="newGuardrail.type"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
            >
              <option v-for="type in guardrailTypes" :key="type.id" :value="type.id">
                {{ type.icon }} {{ type.name }}
              </option>
            </select>
            <p class="mt-1 text-sm text-gray-500">
              {{ guardrailTypes.find(t => t.id === newGuardrail.type)?.description }}
            </p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Mode
            </label>
            <select
              v-model="newGuardrail.mode"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
            >
              <option value="block">Block - Prevent the action</option>
              <option value="warn">Warn - Show warning but allow</option>
              <option value="log">Log - Log only, no action</option>
            </select>
          </div>
          
          <div v-if="guardrailTypes.find(t => t.id === newGuardrail.type)?.hasThreshold">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Threshold: {{ Math.round(newGuardrail.threshold * 100) }}%
            </label>
            <input
              v-model.number="newGuardrail.threshold"
              type="range"
              min="0"
              max="1"
              step="0.05"
              class="w-full"
            />
            <p class="mt-1 text-sm text-gray-500">
              Content scoring above this threshold will trigger the guardrail
            </p>
          </div>
          
          <div v-if="newGuardrail.type === 'topic'">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Allowed Topics
            </label>
            <textarea
              v-model="newGuardrail.topics"
              rows="3"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="technology, business, support (comma-separated)"
            />
          </div>
          
          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              class="px-4 py-2 border rounded-lg hover:bg-gray-50"
              @click="showAddModal = false"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add Guardrail
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
