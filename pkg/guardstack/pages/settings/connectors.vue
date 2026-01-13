<script lang="ts" setup>
/**
 * Settings - Connectors Page
 * Configure model registry and data source connections
 */
import { ref, onMounted } from 'vue';
import StatusBadge from '../../components/StatusBadge.vue';

interface Connector {
  id: string;
  name: string;
  type: 'mlflow' | 'kubeflow' | 's3' | 'huggingface' | 'custom';
  status: 'connected' | 'disconnected' | 'error';
  endpoint?: string;
  lastSync?: string;
  modelsCount?: number;
  config: Record<string, unknown>;
}

const loading = ref(true);
const connectors = ref<Connector[]>([]);
const showAddModal = ref(false);
const showEditModal = ref(false);
const selectedConnector = ref<Connector | null>(null);

const connectorTypes = [
  {
    id: 'mlflow',
    name: 'MLflow',
    icon: '📊',
    description: 'Connect to MLflow Model Registry',
    configFields: ['endpoint', 'token'],
  },
  {
    id: 'kubeflow',
    name: 'Kubeflow',
    icon: '☸️',
    description: 'Connect to Kubeflow Pipelines',
    configFields: ['endpoint', 'namespace', 'token'],
  },
  {
    id: 's3',
    name: 'S3 Bucket',
    icon: '🪣',
    description: 'Connect to S3-compatible storage',
    configFields: ['endpoint', 'bucket', 'accessKey', 'secretKey'],
  },
  {
    id: 'huggingface',
    name: 'Hugging Face',
    icon: '🤗',
    description: 'Connect to Hugging Face Hub',
    configFields: ['token', 'organization'],
  },
];

const newConnector = ref({
  name: '',
  type: 'mlflow' as const,
  endpoint: '',
  token: '',
  bucket: '',
  accessKey: '',
  secretKey: '',
  namespace: '',
  organization: '',
});

async function addConnector() {
  const connector: Connector = {
    id: `connector-${Date.now()}`,
    name: newConnector.value.name,
    type: newConnector.value.type,
    status: 'disconnected',
    endpoint: newConnector.value.endpoint,
    config: { ...newConnector.value },
  };
  
  connectors.value.push(connector);
  showAddModal.value = false;
  
  // Simulate connection
  setTimeout(() => {
    const index = connectors.value.findIndex(c => c.id === connector.id);
    if (index !== -1) {
      connectors.value[index].status = 'connected';
      connectors.value[index].lastSync = new Date().toISOString();
    }
  }, 2000);
  
  // Reset form
  newConnector.value = {
    name: '',
    type: 'mlflow',
    endpoint: '',
    token: '',
    bucket: '',
    accessKey: '',
    secretKey: '',
    namespace: '',
    organization: '',
  };
}

function editConnector(connector: Connector) {
  selectedConnector.value = connector;
  showEditModal.value = true;
}

async function syncConnector(connector: Connector) {
  const index = connectors.value.findIndex(c => c.id === connector.id);
  if (index !== -1) {
    connectors.value[index].status = 'disconnected';
    
    setTimeout(() => {
      connectors.value[index].status = 'connected';
      connectors.value[index].lastSync = new Date().toISOString();
    }, 1500);
  }
}

async function deleteConnector(connector: Connector) {
  if (confirm(`Are you sure you want to delete "${connector.name}"?`)) {
    connectors.value = connectors.value.filter(c => c.id !== connector.id);
  }
}

onMounted(() => {
  connectors.value = [
    {
      id: 'connector-1',
      name: 'Production MLflow',
      type: 'mlflow',
      status: 'connected',
      endpoint: 'https://mlflow.example.com',
      lastSync: '2024-06-01T10:30:00Z',
      modelsCount: 24,
      config: {},
    },
    {
      id: 'connector-2',
      name: 'Model Artifacts',
      type: 's3',
      status: 'connected',
      endpoint: 's3://guardstack-models',
      lastSync: '2024-06-01T09:00:00Z',
      modelsCount: 156,
      config: {},
    },
  ];
  loading.value = false;
});
</script>

<template>
  <div class="settings-connectors p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Connectors
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Configure model registry and data source connections
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="showAddModal = true"
      >
        Add Connector
      </button>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <template v-else>
      <!-- Connectors grid -->
      <div v-if="connectors.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="connector in connectors"
          :key="connector.id"
          class="bg-white dark:bg-gray-800 rounded-lg border p-4"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="flex items-center gap-3">
              <span class="text-2xl">
                {{ connectorTypes.find(t => t.id === connector.type)?.icon || '🔌' }}
              </span>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-gray-100">
                  {{ connector.name }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {{ connector.type }}
                </p>
              </div>
            </div>
            <StatusBadge
              :status="connector.status === 'connected' ? 'pass' : 
                       connector.status === 'error' ? 'fail' : 'warn'"
              :label="connector.status"
            />
          </div>
          
          <dl class="text-sm space-y-2 mb-4">
            <div v-if="connector.endpoint" class="flex justify-between">
              <dt class="text-gray-500">Endpoint</dt>
              <dd class="text-gray-700 dark:text-gray-300 truncate ml-4" :title="connector.endpoint">
                {{ connector.endpoint }}
              </dd>
            </div>
            <div v-if="connector.modelsCount !== undefined" class="flex justify-between">
              <dt class="text-gray-500">Models</dt>
              <dd class="text-gray-700 dark:text-gray-300">{{ connector.modelsCount }}</dd>
            </div>
            <div v-if="connector.lastSync" class="flex justify-between">
              <dt class="text-gray-500">Last Sync</dt>
              <dd class="text-gray-700 dark:text-gray-300">
                {{ new Date(connector.lastSync).toLocaleString() }}
              </dd>
            </div>
          </dl>
          
          <div class="flex items-center gap-2 pt-3 border-t">
            <button
              class="text-sm text-blue-600 hover:underline"
              @click="syncConnector(connector)"
            >
              Sync
            </button>
            <button
              class="text-sm text-gray-600 hover:underline"
              @click="editConnector(connector)"
            >
              Edit
            </button>
            <button
              class="text-sm text-red-600 hover:underline ml-auto"
              @click="deleteConnector(connector)"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-else class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
        <span class="text-4xl">🔌</span>
        <h3 class="mt-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
          No connectors configured
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mt-2">
          Add a connector to import models from external sources
        </p>
        <button
          class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          @click="showAddModal = true"
        >
          Add Connector
        </button>
      </div>
    </template>
    
    <!-- Add modal -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showAddModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div class="flex items-start justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Add Connector
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="showAddModal = false"
          >
            ✕
          </button>
        </div>
        
        <form @submit.prevent="addConnector" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name
            </label>
            <input
              v-model="newConnector.name"
              type="text"
              required
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="My Connector"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Type
            </label>
            <select
              v-model="newConnector.type"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
            >
              <option v-for="type in connectorTypes" :key="type.id" :value="type.id">
                {{ type.icon }} {{ type.name }}
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Endpoint
            </label>
            <input
              v-model="newConnector.endpoint"
              type="text"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="https://..."
            />
          </div>
          
          <div v-if="newConnector.type !== 's3'">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Token
            </label>
            <input
              v-model="newConnector.token"
              type="password"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="••••••••"
            />
          </div>
          
          <template v-if="newConnector.type === 's3'">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Bucket
              </label>
              <input
                v-model="newConnector.bucket"
                type="text"
                class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
                placeholder="my-bucket"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Access Key
              </label>
              <input
                v-model="newConnector.accessKey"
                type="text"
                class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Secret Key
              </label>
              <input
                v-model="newConnector.secretKey"
                type="password"
                class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              />
            </div>
          </template>
          
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
              Add Connector
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
