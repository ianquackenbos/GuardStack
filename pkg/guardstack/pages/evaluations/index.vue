<script lang="ts" setup>
/**
 * Evaluations List Page
 * Displays all evaluations with filtering and search
 */
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useEvaluationsStore } from '../../store/evaluations';
import { useModelsStore } from '../../store/models';
import StatusBadge from '../../components/StatusBadge.vue';
import ProgressTracker from '../../components/ProgressTracker.vue';
import type { Evaluation, EvaluationStatus, PillarType } from '../../types';

const router = useRouter();
const route = useRoute();
const evaluationsStore = useEvaluationsStore();
const modelsStore = useModelsStore();

const loading = ref(true);
const searchQuery = ref('');
const filterStatus = ref<EvaluationStatus | 'all'>('all');
const showCreateModal = ref(false);

const newEvaluation = ref({
  modelId: '',
  name: '',
  pillars: ['explain', 'fairness', 'robustness', 'privacy'] as PillarType[],
});

const evaluations = computed(() => evaluationsStore.evaluations);
const models = computed(() => modelsStore.models);
const totalCount = computed(() => evaluationsStore.totalCount);

const filteredEvaluations = computed(() => {
  let result = [...evaluations.value];
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(e => 
      e.name.toLowerCase().includes(query)
    );
  }
  
  if (filterStatus.value !== 'all') {
    result = result.filter(e => e.status === filterStatus.value);
  }
  
  return result;
});

const availablePillars: { id: PillarType; name: string }[] = [
  { id: 'explain', name: 'Explainability' },
  { id: 'actions', name: 'Adversarial' },
  { id: 'fairness', name: 'Fairness' },
  { id: 'robustness', name: 'Robustness' },
  { id: 'trace', name: 'Data Lineage' },
  { id: 'testing', name: 'Testing' },
  { id: 'imitation', name: 'IP Protection' },
  { id: 'privacy', name: 'Privacy' },
  { id: 'toxicity', name: 'Toxicity' },
  { id: 'security', name: 'Security' },
];

async function loadData() {
  loading.value = true;
  try {
    await Promise.all([
      evaluationsStore.fetchEvaluations({
        status: filterStatus.value !== 'all' ? filterStatus.value : undefined,
      }),
      modelsStore.fetchModels({}),
    ]);
    
    // Pre-select model if passed in URL
    if (route.query.modelId) {
      newEvaluation.value.modelId = route.query.modelId as string;
      showCreateModal.value = true;
    }
  } catch (error) {
    console.error('Failed to load data:', error);
  } finally {
    loading.value = false;
  }
}

async function createEvaluation() {
  try {
    const evaluation = await evaluationsStore.createEvaluation({
      modelId: newEvaluation.value.modelId,
      name: newEvaluation.value.name || `Evaluation - ${new Date().toISOString().split('T')[0]}`,
      pillars: newEvaluation.value.pillars,
    });
    showCreateModal.value = false;
    router.push(`/guardstack/evaluations/${evaluation.id}`);
  } catch (error) {
    console.error('Failed to create evaluation:', error);
  }
}

function viewEvaluation(evaluation: Evaluation) {
  router.push(`/guardstack/evaluations/${evaluation.id}`);
}

function getModelName(modelId: string): string {
  const model = models.value.find(m => m.id === modelId);
  return model?.name || 'Unknown Model';
}

function togglePillar(pillar: PillarType) {
  const index = newEvaluation.value.pillars.indexOf(pillar);
  if (index === -1) {
    newEvaluation.value.pillars.push(pillar);
  } else {
    newEvaluation.value.pillars.splice(index, 1);
  }
}

watch(filterStatus, loadData);

onMounted(loadData);
</script>

<template>
  <div class="evaluations-list p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Evaluations
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          View and manage model safety evaluations
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="showCreateModal = true"
      >
        New Evaluation
      </button>
    </div>
    
    <!-- Filters -->
    <div class="flex items-center gap-4 mb-6">
      <!-- Search -->
      <div class="flex-grow max-w-md">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search evaluations..."
          class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800"
        />
      </div>
      
      <!-- Status filter -->
      <select
        v-model="filterStatus"
        class="px-3 py-2 border rounded-lg dark:bg-gray-800"
      >
        <option value="all">All Statuses</option>
        <option value="pending">Pending</option>
        <option value="running">Running</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
        <option value="cancelled">Cancelled</option>
      </select>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <template v-else>
      <!-- Results count -->
      <div class="text-sm text-gray-500 mb-4">
        Showing {{ filteredEvaluations.length }} of {{ totalCount }} evaluations
      </div>
      
      <!-- Evaluations list -->
      <div v-if="filteredEvaluations.length > 0" class="space-y-4">
        <div
          v-for="evaluation in filteredEvaluations"
          :key="evaluation.id"
          class="bg-white dark:bg-gray-800 rounded-lg border p-4 hover:shadow-md transition-shadow cursor-pointer"
          @click="viewEvaluation(evaluation)"
        >
          <div class="flex items-start justify-between mb-3">
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-gray-100">
                {{ evaluation.name }}
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ getModelName(evaluation.modelId) }}
              </p>
            </div>
            <div class="flex items-center gap-3">
              <span
                v-if="evaluation.overallScore !== undefined"
                :class="[
                  'text-xl font-bold',
                  evaluation.overallScore >= 80 ? 'text-green-600' :
                  evaluation.overallScore >= 60 ? 'text-yellow-600' : 'text-red-600',
                ]"
              >
                {{ Math.round(evaluation.overallScore) }}
              </span>
              <StatusBadge
                :status="evaluation.status === 'completed' ? 'pass' :
                         evaluation.status === 'failed' ? 'fail' :
                         evaluation.status === 'running' ? 'pending' : 'warn'"
                :label="evaluation.status"
              />
            </div>
          </div>
          
          <!-- Progress for running evaluations -->
          <div v-if="evaluation.status === 'running'" class="mb-3">
            <ProgressTracker
              :stages="(evaluation.pillars || []).map(p => ({
                id: p,
                name: p.charAt(0).toUpperCase() + p.slice(1),
                status: evaluation.pillarScores?.[p] ? 'completed' : 
                        evaluation.currentPillar === p ? 'running' : 'pending',
              }))"
              compact
            />
          </div>
          
          <!-- Pillar badges -->
          <div class="flex items-center gap-2 flex-wrap">
            <span
              v-for="pillar in evaluation.pillars"
              :key="pillar"
              :class="[
                'px-2 py-0.5 rounded text-xs capitalize',
                evaluation.pillarScores?.[pillar]
                  ? evaluation.pillarScores[pillar].score >= 80
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : evaluation.pillarScores[pillar].score >= 60
                    ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
              ]"
            >
              {{ pillar }}
              <span v-if="evaluation.pillarScores?.[pillar]" class="ml-1 font-medium">
                {{ Math.round(evaluation.pillarScores[pillar].score) }}
              </span>
            </span>
          </div>
          
          <!-- Footer -->
          <div class="flex items-center justify-between mt-3 pt-3 border-t text-sm text-gray-500">
            <span>
              {{ new Date(evaluation.createdAt).toLocaleString() }}
            </span>
            <span v-if="evaluation.duration">
              Duration: {{ (evaluation.duration / 1000).toFixed(1) }}s
            </span>
          </div>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-else class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border">
        <span class="text-4xl">📋</span>
        <h3 class="mt-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
          No evaluations found
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mt-2">
          {{ searchQuery || filterStatus !== 'all'
            ? 'Try adjusting your filters'
            : 'Start your first evaluation to assess model safety' }}
        </p>
        <button
          v-if="!searchQuery && filterStatus === 'all'"
          class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          @click="showCreateModal = true"
        >
          New Evaluation
        </button>
      </div>
    </template>
    
    <!-- Create modal -->
    <div
      v-if="showCreateModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      @click.self="showCreateModal = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div class="flex items-start justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
            New Evaluation
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="showCreateModal = false"
          >
            ✕
          </button>
        </div>
        
        <form @submit.prevent="createEvaluation" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Model *
            </label>
            <select
              v-model="newEvaluation.modelId"
              required
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
            >
              <option value="" disabled>Select a model</option>
              <option v-for="model in models" :key="model.id" :value="model.id">
                {{ model.name }} ({{ model.modelType }})
              </option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name
            </label>
            <input
              v-model="newEvaluation.name"
              type="text"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900"
              placeholder="Evaluation - {{ new Date().toISOString().split('T')[0] }}"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Pillars to Evaluate *
            </label>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="pillar in availablePillars"
                :key="pillar.id"
                type="button"
                :class="[
                  'px-3 py-2 text-sm rounded-lg border transition-colors text-left',
                  newEvaluation.pillars.includes(pillar.id)
                    ? 'bg-blue-100 border-blue-500 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700',
                ]"
                @click="togglePillar(pillar.id)"
              >
                <span class="mr-2">
                  {{ newEvaluation.pillars.includes(pillar.id) ? '✓' : '○' }}
                </span>
                {{ pillar.name }}
              </button>
            </div>
            <p v-if="newEvaluation.pillars.length === 0" class="mt-2 text-sm text-red-500">
              Please select at least one pillar
            </p>
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
              :disabled="!newEvaluation.modelId || newEvaluation.pillars.length === 0"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Start Evaluation
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
