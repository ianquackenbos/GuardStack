<script lang="ts" setup>
/**
 * Settings - Policies Page
 * 
 * Manage organizational security policies and guardrail configurations.
 */
import { ref, onMounted, computed } from 'vue';

interface Policy {
  id: string;
  name: string;
  description: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  scope: string[];
  rules: PolicyRule[];
  created_at: string;
  updated_at: string;
}

interface PolicyRule {
  id: string;
  condition: string;
  action: 'block' | 'warn' | 'log' | 'allow';
  threshold?: number;
}

const loading = ref(true);
const policies = ref<Policy[]>([]);
const searchQuery = ref('');
const filterCategory = ref<string>('all');
const filterEnabled = ref<string>('all');
const showCreateModal = ref(false);
const showEditModal = ref(false);
const selectedPolicy = ref<Policy | null>(null);

const categories = ['content-safety', 'data-protection', 'compliance', 'access-control', 'resource-limits'];

const severityColors: Record<string, string> = {
  low: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  high: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  critical: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
};

const categoryIcons: Record<string, string> = {
  'content-safety': '🛡️',
  'data-protection': '🔐',
  'compliance': '📋',
  'access-control': '🔑',
  'resource-limits': '📊',
};

const newPolicy = ref({
  name: '',
  description: '',
  category: 'content-safety',
  severity: 'medium' as Policy['severity'],
  scope: [] as string[],
});

const filteredPolicies = computed(() => {
  return policies.value.filter(policy => {
    const matchesSearch = policy.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                          policy.description.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesCategory = filterCategory.value === 'all' || policy.category === filterCategory.value;
    const matchesEnabled = filterEnabled.value === 'all' || 
                          (filterEnabled.value === 'enabled' && policy.enabled) ||
                          (filterEnabled.value === 'disabled' && !policy.enabled);
    return matchesSearch && matchesCategory && matchesEnabled;
  });
});

const policyStats = computed(() => ({
  total: policies.value.length,
  enabled: policies.value.filter(p => p.enabled).length,
  critical: policies.value.filter(p => p.severity === 'critical').length,
  high: policies.value.filter(p => p.severity === 'high').length,
}));

async function fetchData() {
  loading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    policies.value = [
      {
        id: '1',
        name: 'Block Harmful Content',
        description: 'Block generation of harmful, violent, or illegal content',
        category: 'content-safety',
        severity: 'critical',
        enabled: true,
        scope: ['all-models'],
        rules: [
          { id: 'r1', condition: 'toxicity_score > 0.8', action: 'block' },
          { id: 'r2', condition: 'violence_detected == true', action: 'block' },
        ],
        created_at: new Date(Date.now() - 30 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 2 * 86400000).toISOString(),
      },
      {
        id: '2',
        name: 'PII Protection',
        description: 'Detect and redact personally identifiable information',
        category: 'data-protection',
        severity: 'high',
        enabled: true,
        scope: ['all-models'],
        rules: [
          { id: 'r1', condition: 'pii_type in [SSN, CREDIT_CARD]', action: 'block' },
          { id: 'r2', condition: 'pii_type in [EMAIL, PHONE]', action: 'warn' },
        ],
        created_at: new Date(Date.now() - 25 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 5 * 86400000).toISOString(),
      },
      {
        id: '3',
        name: 'Jailbreak Prevention',
        description: 'Detect and block jailbreak attempts',
        category: 'content-safety',
        severity: 'critical',
        enabled: true,
        scope: ['production-models'],
        rules: [
          { id: 'r1', condition: 'jailbreak_score > 0.7', action: 'block' },
          { id: 'r2', condition: 'injection_detected == true', action: 'block' },
        ],
        created_at: new Date(Date.now() - 20 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 1 * 86400000).toISOString(),
      },
      {
        id: '4',
        name: 'EU AI Act Compliance',
        description: 'Enforce EU AI Act requirements for high-risk systems',
        category: 'compliance',
        severity: 'high',
        enabled: true,
        scope: ['eu-deployed-models'],
        rules: [
          { id: 'r1', condition: 'risk_level == high', action: 'log' },
          { id: 'r2', condition: 'human_oversight_required == true', action: 'warn' },
        ],
        created_at: new Date(Date.now() - 15 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 3 * 86400000).toISOString(),
      },
      {
        id: '5',
        name: 'Rate Limiting',
        description: 'Limit API requests per user/organization',
        category: 'resource-limits',
        severity: 'medium',
        enabled: true,
        scope: ['all-endpoints'],
        rules: [
          { id: 'r1', condition: 'requests_per_minute > 60', action: 'block', threshold: 60 },
          { id: 'r2', condition: 'tokens_per_day > 100000', action: 'warn', threshold: 100000 },
        ],
        created_at: new Date(Date.now() - 10 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 7 * 86400000).toISOString(),
      },
      {
        id: '6',
        name: 'RBAC Enforcement',
        description: 'Enforce role-based access control policies',
        category: 'access-control',
        severity: 'high',
        enabled: true,
        scope: ['all-resources'],
        rules: [
          { id: 'r1', condition: 'user_role not in allowed_roles', action: 'block' },
          { id: 'r2', condition: 'access_level < required_level', action: 'block' },
        ],
        created_at: new Date(Date.now() - 28 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 10 * 86400000).toISOString(),
      },
      {
        id: '7',
        name: 'Bias Detection Alert',
        description: 'Alert on detected bias in model outputs',
        category: 'compliance',
        severity: 'medium',
        enabled: false,
        scope: ['hr-models', 'finance-models'],
        rules: [
          { id: 'r1', condition: 'bias_score > 0.5', action: 'warn' },
          { id: 'r2', condition: 'demographic_parity_diff > 0.1', action: 'log' },
        ],
        created_at: new Date(Date.now() - 5 * 86400000).toISOString(),
        updated_at: new Date(Date.now() - 4 * 86400000).toISOString(),
      },
    ];
  } finally {
    loading.value = false;
  }
}

function togglePolicy(policyId: string) {
  const policy = policies.value.find(p => p.id === policyId);
  if (policy) {
    policy.enabled = !policy.enabled;
    policy.updated_at = new Date().toISOString();
  }
}

function editPolicy(policy: Policy) {
  selectedPolicy.value = { ...policy, rules: [...policy.rules] };
  showEditModal.value = true;
}

function savePolicy() {
  if (selectedPolicy.value) {
    const index = policies.value.findIndex(p => p.id === selectedPolicy.value!.id);
    if (index !== -1) {
      policies.value[index] = { ...selectedPolicy.value, updated_at: new Date().toISOString() };
    }
  }
  showEditModal.value = false;
  selectedPolicy.value = null;
}

function deletePolicy(policyId: string) {
  if (confirm('Are you sure you want to delete this policy?')) {
    policies.value = policies.value.filter(p => p.id !== policyId);
  }
}

function createPolicy() {
  if (!newPolicy.value.name) return;
  
  const policy: Policy = {
    id: String(Date.now()),
    name: newPolicy.value.name,
    description: newPolicy.value.description,
    category: newPolicy.value.category,
    severity: newPolicy.value.severity,
    enabled: false,
    scope: newPolicy.value.scope,
    rules: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  
  policies.value.unshift(policy);
  showCreateModal.value = false;
  newPolicy.value = {
    name: '',
    description: '',
    category: 'content-safety',
    severity: 'medium',
    scope: [],
  };
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString();
}

onMounted(() => {
  fetchData();
});
</script>

<template>
  <div class="policies-page p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          Security Policies
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Configure and manage organizational security policies
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="showCreateModal = true"
      >
        ➕ Create Policy
      </button>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-sm text-gray-500 dark:text-gray-400">Total Policies</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white">{{ policyStats.total }}</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-sm text-gray-500 dark:text-gray-400">Active</div>
        <div class="text-2xl font-bold text-green-600">{{ policyStats.enabled }}</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-sm text-gray-500 dark:text-gray-400">Critical</div>
        <div class="text-2xl font-bold text-red-600">{{ policyStats.critical }}</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-sm text-gray-500 dark:text-gray-400">High Severity</div>
        <div class="text-2xl font-bold text-orange-600">{{ policyStats.high }}</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
      <div class="flex flex-wrap gap-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search policies..."
          class="flex-1 min-w-64 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />
        <select
          v-model="filterCategory"
          class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="all">All Categories</option>
          <option v-for="cat in categories" :key="cat" :value="cat">
            {{ categoryIcons[cat] }} {{ cat.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') }}
          </option>
        </select>
        <select
          v-model="filterEnabled"
          class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="all">All Status</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Policy List -->
    <div v-else class="space-y-4">
      <div
        v-for="policy in filteredPolicies"
        :key="policy.id"
        class="bg-white dark:bg-gray-800 rounded-lg shadow"
      >
        <div class="p-6">
          <div class="flex items-start justify-between">
            <div class="flex items-start gap-4">
              <span class="text-2xl mt-1">{{ categoryIcons[policy.category] || '📋' }}</span>
              <div>
                <div class="flex items-center gap-3 mb-1">
                  <h3 class="font-semibold text-gray-900 dark:text-white">
                    {{ policy.name }}
                  </h3>
                  <span :class="['px-2 py-1 text-xs font-medium rounded-full', severityColors[policy.severity]]">
                    {{ policy.severity }}
                  </span>
                  <span
                    :class="[
                      'px-2 py-1 text-xs font-medium rounded-full',
                      policy.enabled
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                    ]"
                  >
                    {{ policy.enabled ? 'Active' : 'Disabled' }}
                  </span>
                </div>
                <p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
                  {{ policy.description }}
                </p>
                <div class="flex flex-wrap gap-2 mb-2">
                  <span
                    v-for="scope in policy.scope"
                    :key="scope"
                    class="px-2 py-1 text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded"
                  >
                    {{ scope }}
                  </span>
                </div>
                <div class="text-xs text-gray-400 dark:text-gray-500">
                  {{ policy.rules.length }} rules · Updated {{ formatDate(policy.updated_at) }}
                </div>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  :checked="policy.enabled"
                  class="sr-only peer"
                  @change="togglePolicy(policy.id)"
                />
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
              <button
                class="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                @click="editPolicy(policy)"
              >
                ✏️
              </button>
              <button
                class="p-2 text-red-500 hover:text-red-700"
                @click="deletePolicy(policy.id)"
              >
                🗑️
              </button>
            </div>
          </div>

          <!-- Rules Preview -->
          <div v-if="policy.rules.length > 0" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Rules</div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div
                v-for="rule in policy.rules.slice(0, 4)"
                :key="rule.id"
                class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400"
              >
                <span
                  :class="[
                    'px-2 py-0.5 text-xs rounded',
                    rule.action === 'block' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                    rule.action === 'warn' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
                    rule.action === 'log' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' :
                    'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                  ]"
                >
                  {{ rule.action }}
                </span>
                <code class="text-xs bg-gray-100 dark:bg-gray-700 px-1 rounded">
                  {{ rule.condition }}
                </code>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="filteredPolicies.length === 0"
        class="text-center py-12 text-gray-500 dark:text-gray-400"
      >
        No policies found matching your criteria.
      </div>
    </div>

    <!-- Create Modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showCreateModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-lg">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Create New Policy
        </h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Policy Name *
            </label>
            <input
              v-model="newPolicy.name"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Enter policy name"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              v-model="newPolicy.description"
              rows="3"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Describe the policy purpose"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Category
              </label>
              <select
                v-model="newPolicy.category"
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option v-for="cat in categories" :key="cat" :value="cat">
                  {{ cat.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Severity
              </label>
              <select
                v-model="newPolicy.severity"
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            @click="showCreateModal = false"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            @click="createPolicy"
          >
            Create Policy
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div
      v-if="showEditModal && selectedPolicy"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showEditModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-xl p-6 w-full max-w-lg">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Edit Policy
        </h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Policy Name
            </label>
            <input
              v-model="selectedPolicy.name"
              type="text"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              v-model="selectedPolicy.description"
              rows="3"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Category
              </label>
              <select
                v-model="selectedPolicy.category"
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option v-for="cat in categories" :key="cat" :value="cat">
                  {{ cat.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') }}
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Severity
              </label>
              <select
                v-model="selectedPolicy.severity"
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            @click="showEditModal = false; selectedPolicy = null"
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            @click="savePolicy"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.policies-page {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .policies-page {
    background-color: #111827;
  }
}
</style>
