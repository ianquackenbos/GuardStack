<script lang="ts" setup>
/**
 * Models List Page
 * Displays all registered models with filtering and search
 */
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useModelsStore } from '../../store/models';
import ModelCard from '../../components/ModelCard.vue';
import StatusBadge from '../../components/StatusBadge.vue';
import type { Model, ModelType, RiskLevel } from '../../types';

const router = useRouter();
const modelsStore = useModelsStore();

const loading = ref(true);
const searchQuery = ref('');
const filterType = ref<ModelType | 'all'>('all');
const filterRisk = ref<RiskLevel | 'all'>('all');
const viewMode = ref<'grid' | 'list'>('grid');
const showCreateModal = ref(false);

const newModel = ref({
  name: '',
  modelType: 'predictive' as ModelType,
  version: '1.0.0',
  description: '',
  framework: '',
});

const models = computed(() => modelsStore.models);
const totalCount = computed(() => modelsStore.totalCount);

const filteredModels = computed(() => {
  let result = [...models.value];
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(m => 
      m.name.toLowerCase().includes(query) ||
      m.description?.toLowerCase().includes(query)
    );
  }
  
  if (filterType.value !== 'all') {
    result = result.filter(m => m.modelType === filterType.value);
  }
  
  if (filterRisk.value !== 'all') {
    result = result.filter(m => m.riskLevel === filterRisk.value);
  }
  
  return result;
});

async function loadModels() {
  loading.value = true;
  try {
    await modelsStore.fetchModels({
      modelType: filterType.value !== 'all' ? filterType.value : undefined,
      riskLevel: filterRisk.value !== 'all' ? filterRisk.value : undefined,
    });
  } catch (error) {
    console.error('Failed to load models:', error);
  } finally {
    loading.value = false;
  }
}

async function createModel() {
  try {
    const model = await modelsStore.createModel(newModel.value);
    showCreateModal.value = false;
    router.push(`/guardstack/models/${model.id}`);
  } catch (error) {
    console.error('Failed to create model:', error);
  }
}

function viewModel(model: Model) {
  router.push(`/guardstack/models/${model.id}`);
}

function evaluateModel(model: Model) {
  router.push(`/guardstack/evaluations/new?modelId=${model.id}`);
}

async function deleteModel(model: Model) {
  if (confirm(`Are you sure you want to delete "${model.name}"?`)) {
    await modelsStore.deleteModel(model.id);
  }
}

watch([filterType, filterRisk], loadModels);

onMounted(loadModels);
</script>

<template>
  <div class="models-list p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Models
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Manage AI models and their safety evaluations
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="showCreateModal = true"
      >
        Add Model
      </button>
    </div>
    
    <!-- Filters -->
    <div class="flex items-center gap-4 mb-6">
      <!-- Search -->
      <div class="flex-grow max-w-md">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search models..."
          class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800"
        />
      </div>
      
      <!-- Type filter -->
      <select
        v-model="filterType"
        class="px-3 py-2 border rounded-lg dark:bg-gray-800"
      >
        <option value="all">All Types</option>
        <option value="predictive">Predictive</option>
        <option value="genai">Generative AI</option>
        <option value="spm">Small Private Model</option>
        <option value="agentic">Agentic</option>
      </select>
      
      <!-- Risk filter -->
      <select
        v-model="filterRisk"
        class="px-3 py-2 border rounded-lg dark:bg-gray-800"
      >
        <option value="all">All Risk Levels</option>
        <option value="minimal">Minimal</option>
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
        <option value="critical">Critical</option>
      </select>
      
      <!-- View toggle -->
      <div class="flex border rounded-lg overflow-hidden">
        <button
          :class="[
            'px-3 py-2',
            viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-800',
          ]"
          @click="viewMode = 'grid'"
        >
          ▦
        </button>
        <button
          :class="[
            'px-3 py-2',
            viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-800',
          ]"
          @click="viewMode = 'list'"
        >
          ☰
        </button>
      </div>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <template v-else>
      <!-- Results count -->
      <div class="text-sm text-gray-500 mb-4">
        Showing {{ filteredModels.length }} of {{ totalCount }} models
      </div>
      
      <!-- Grid view -->
      <div v-if="viewMode === 'grid' && filteredModels.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <ModelCard
          v-for="model in filteredModels"
          :key="model.id"
          :model="model"
          :show-actions="true"
          @view="viewModel"
          @evaluate="evaluateModel"
          @delete="deleteModel"
        />
      </div>
      
      <!-- List view -->
      <div v-else-if="viewMode === 'list' && filteredModels.length > 0" class="bg-white dark:bg-gray-800 rounded-lg border">
        <table class="w-full">
          <thead class="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Name</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Type</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Version</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Risk Level</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Score</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Last Evaluated</th>
              <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="model in filteredModels"
              :key="model.id"
              class="border-t hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <td class="px-4 py-3">
                <div class="font-medium text-gray-900 dark:text-gray-100">
                  {{ model.name }}
                </div>
                <div v-if="model.description" class="text-xs text-gray-500 line-clamp-1">
                  {{ model.description }}
                </div>
              </td>
              <td class="px-4 py-3 text-gray-500 capitalize">
                {{ model.modelType }}
              </td>
              <td class="px-4 py-3 text-gray-500">
                v{{ model.version }}
              </td>
              <td class="px-4 py-3">
                <StatusBadge
                  v-if="model.riskLevel"
                  :status="model.riskLevel === 'high' || model.riskLevel === 'critical' ? 'fail' : 
                           model.riskLevel === 'medium' ? 'warn' : 'pass'"
                  :label="model.riskLevel"
                />
                <span v-else class="text-gray-400">—</span>
              </td>
              <td class="px-4 py-3">
                <span
                  v-if="model.lastScore !== undefined"
                  :class="[
                    'font-semibold',
                    model.lastScore >= 80 ? 'text-green-600' :
                    model.lastScore >= 60 ? 'text-yellow-600' : 'text-red-600',
                  ]"
                >
                  {{ Math.round(model.lastScore) }}
                </span>
                <span v-else class="text-gray-400">—</span>
              </td>
              <td class="px-4 py-3 text-gray-500">
                {{ model.lastEvaluatedAt ? new Date(model.lastEvaluatedAt).toLocaleDateString() : 'Never' }}
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <button
                    class="text-blue-600 hover:underline"
                    @click="viewModel(model)"
                  >
                    View
                  </button>
                  <button
                    class="text-green-600 hover:underline"
                    @click="evaluateModel(model)"
                  >
                    Evaluate
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Empty state -->
      <div v-else class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
        <span class="text-4xl">📦</span>
        <h3 class="mt-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
          No models found
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mt-2">
          {{ searchQuery || filterType !== 'all' || filterRisk !== 'all' 
            ? 'Try adjusting your filters' 
            : 'Register your first model to get started' }}
        </p>
        <button
          v-if="!searchQuery && filterType === 'all' && filterRisk === 'all'"
          class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          @click="showCreateModal = true"
        >
          Add Model
        </button>
      </div>
    </template>
    
    <!-- Create modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showCreateModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
        <div class="flex items-start justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Add Model
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="showCreateModal = false"
          >
            ✕
          </button>
        </div>
        
        <form @submit.prevent="createModel" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name *
            </label>
            <input
              v-model="newModel.name"
              type="text"
              required
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="My Model"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Type *
            </label>
            <select
              v-model="newModel.modelType"
              required
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
            >
              <option value="predictive">Predictive</option>
              <option value="genai">Generative AI</option>
              <option value="spm">Small Private Model</option>
              <option value="agentic">Agentic</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Version
            </label>
            <input
              v-model="newModel.version"
              type="text"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="1.0.0"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Framework
            </label>
            <input
              v-model="newModel.framework"
              type="text"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="PyTorch, TensorFlow, etc."
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              v-model="newModel.description"
              rows="3"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="Brief description of the model..."
            />
          </div>
          
          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              class="px-4 py-2 border rounded-lg hover:bg-gray-50"
              @click="showCreateModal = false"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add Model
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
