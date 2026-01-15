<script lang="ts" setup>
/**
 * SPM Inventory - AI Asset Inventory Management
 * 
 * Displays and manages the inventory of AI models, datasets,
 * pipelines, and other AI assets across the organization.
 */
import { ref, onMounted, computed } from 'vue';

interface Asset {
  id: string;
  name: string;
  asset_type: 'model' | 'dataset' | 'pipeline' | 'agent';
  provider: string;
  location: string;
  classification: string;
  owner: string;
  risk_score: number;
  status: string;
  last_scanned: string | null;
  tags: Record<string, string>;
}

const loading = ref(true);
const assets = ref<Asset[]>([]);
const selectedType = ref<string>('all');
const searchQuery = ref('');
const showRegisterModal = ref(false);

const assetTypes = ['all', 'model', 'dataset', 'pipeline', 'agent'];

const typeIcons: Record<string, string> = {
  model: '🤖',
  dataset: '📊',
  pipeline: '🔄',
  agent: '🕵️',
};

const filteredAssets = computed(() => {
  return assets.value.filter(asset => {
    const matchesType = selectedType.value === 'all' || asset.asset_type === selectedType.value;
    const matchesSearch = !searchQuery.value || 
      asset.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      asset.provider.toLowerCase().includes(searchQuery.value.toLowerCase());
    return matchesType && matchesSearch;
  });
});

const assetStats = computed(() => {
  const stats = {
    total: assets.value.length,
    model: 0,
    dataset: 0,
    pipeline: 0,
    agent: 0,
  };
  assets.value.forEach(a => {
    if (a.asset_type in stats) {
      stats[a.asset_type]++;
    }
  });
  return stats;
});

function getRiskClass(score: number): string {
  if (score >= 75) return 'text-red-600 bg-red-100 dark:bg-red-900/30';
  if (score >= 50) return 'text-orange-600 bg-orange-100 dark:bg-orange-900/30';
  if (score >= 25) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
  return 'text-green-600 bg-green-100 dark:bg-green-900/30';
}

async function fetchAssets() {
  loading.value = true;
  try {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    assets.value = [
      {
        id: '1',
        name: 'GPT-4-Production',
        asset_type: 'model',
        provider: 'OpenAI',
        location: 'us-east-1',
        classification: 'confidential',
        owner: 'ml-team',
        risk_score: 23.5,
        status: 'active',
        last_scanned: new Date(Date.now() - 2 * 3600000).toISOString(),
        tags: { environment: 'production', cost_center: 'ml-ops' },
      },
      {
        id: '2',
        name: 'Customer-Dataset-v2',
        asset_type: 'dataset',
        provider: 'Internal',
        location: 's3://data-lake',
        classification: 'pii',
        owner: 'data-team',
        risk_score: 67.2,
        status: 'active',
        last_scanned: new Date(Date.now() - 6 * 3600000).toISOString(),
        tags: { contains_pii: 'true' },
      },
      {
        id: '3',
        name: 'RAG-Pipeline-Prod',
        asset_type: 'pipeline',
        provider: 'LangChain',
        location: 'k8s-cluster-prod',
        classification: 'internal',
        owner: 'platform-team',
        risk_score: 45.8,
        status: 'active',
        last_scanned: new Date(Date.now() - 1 * 3600000).toISOString(),
        tags: { has_vector_store: 'true' },
      },
      {
        id: '4',
        name: 'Research-Assistant',
        asset_type: 'agent',
        provider: 'Internal',
        location: 'k8s-cluster-dev',
        classification: 'internal',
        owner: 'research-team',
        risk_score: 35.0,
        status: 'active',
        last_scanned: new Date(Date.now() - 12 * 3600000).toISOString(),
        tags: { autonomous: 'false' },
      },
      {
        id: '5',
        name: 'Claude-3-Sonnet',
        asset_type: 'model',
        provider: 'Anthropic',
        location: 'us-west-2',
        classification: 'confidential',
        owner: 'ml-team',
        risk_score: 18.2,
        status: 'active',
        last_scanned: new Date(Date.now() - 3 * 3600000).toISOString(),
        tags: { environment: 'production' },
      },
    ];
  } finally {
    loading.value = false;
  }
}

async function triggerDiscovery() {
  alert('Asset discovery initiated. New assets will appear in the pending review queue.');
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Never';
  return new Date(dateStr).toLocaleString();
}

onMounted(() => {
  fetchAssets();
});
</script>

<template>
  <div class="inventory-page p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
          AI Asset Inventory
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Comprehensive inventory of AI models, datasets, pipelines, and agents
        </p>
      </div>
      <div class="flex gap-3">
        <button
          class="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          @click="triggerDiscovery"
        >
          🔍 Discover Assets
        </button>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          @click="showRegisterModal = true"
        >
          ➕ Register Asset
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-5 gap-4 mb-6">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="text-2xl font-bold text-gray-900 dark:text-white">
          {{ assetStats.total }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Total Assets</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="flex items-center gap-2">
          <span class="text-xl">🤖</span>
          <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ assetStats.model }}</span>
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Models</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="flex items-center gap-2">
          <span class="text-xl">📊</span>
          <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ assetStats.dataset }}</span>
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Datasets</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="flex items-center gap-2">
          <span class="text-xl">🔄</span>
          <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ assetStats.pipeline }}</span>
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Pipelines</div>
      </div>
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div class="flex items-center gap-2">
          <span class="text-xl">🕵️</span>
          <span class="text-2xl font-bold text-gray-900 dark:text-white">{{ assetStats.agent }}</span>
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">Agents</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
      <div class="flex flex-wrap gap-4 items-center">
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search assets..."
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
        </div>
        <div class="flex gap-2">
          <button
            v-for="type in assetTypes"
            :key="type"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              selectedType === type
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            ]"
            @click="selectedType = type"
          >
            {{ type === 'all' ? 'All' : typeIcons[type] + ' ' + type.charAt(0).toUpperCase() + type.slice(1) }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Assets Table -->
    <div v-else class="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead class="bg-gray-50 dark:bg-gray-900">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Asset
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Provider
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Classification
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Owner
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Risk Score
            </th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Last Scanned
            </th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          <tr v-for="asset in filteredAssets" :key="asset.id" class="hover:bg-gray-50 dark:hover:bg-gray-700">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center">
                <span class="text-xl mr-3">{{ typeIcons[asset.asset_type] }}</span>
                <div>
                  <div class="text-sm font-medium text-gray-900 dark:text-white">
                    {{ asset.name }}
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {{ asset.location }}
                  </div>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
              {{ asset.provider }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                {{ asset.classification.toUpperCase() }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
              {{ asset.owner }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="['px-2 py-1 text-sm font-medium rounded', getRiskClass(asset.risk_score)]">
                {{ asset.risk_score.toFixed(1) }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
              {{ formatDate(asset.last_scanned) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button class="text-blue-600 hover:text-blue-900 dark:text-blue-400 mr-3">
                View
              </button>
              <button class="text-gray-600 hover:text-gray-900 dark:text-gray-400">
                Scan
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div
        v-if="filteredAssets.length === 0"
        class="text-center py-12 text-gray-500 dark:text-gray-400"
      >
        No assets match your filters.
      </div>
    </div>
  </div>
</template>

<style scoped>
.inventory-page {
  min-height: 100vh;
  background-color: #f3f4f6;
}

@media (prefers-color-scheme: dark) {
  .inventory-page {
    background-color: #111827;
  }
}
</style>
