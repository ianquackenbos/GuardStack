<script lang="ts" setup>
/**
 * Model Detail Page
 * Displays comprehensive model information with evaluation history
 */
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useModelsStore } from '../../store/models';
import { useEvaluationsStore } from '../../store/evaluations';
import StatusBadge from '../../components/StatusBadge.vue';
import ScoreGauge from '../../components/ScoreGauge.vue';
import PillarRadar from '../../components/PillarRadar.vue';
import TrendChart from '../../components/TrendChart.vue';
import PillarScoreCard from '../../components/PillarScoreCard.vue';
import FindingsTable from '../../components/FindingsTable.vue';
import type { Model, Evaluation } from '../../types';

const route = useRoute();
const router = useRouter();
const modelsStore = useModelsStore();
const evaluationsStore = useEvaluationsStore();

const loading = ref(true);
const activeTab = ref('overview');
const model = ref<Model | null>(null);
const evaluations = ref<Evaluation[]>([]);

const modelId = computed(() => route.params.id as string);

const latestEvaluation = computed(() => {
  return evaluations.value.find(e => e.status === 'completed');
});

const pillarScores = computed(() => {
  if (!latestEvaluation.value?.pillarScores) return [];
  return Object.entries(latestEvaluation.value.pillarScores).map(([key, value]) => ({
    pillar: key,
    score: value.score,
    confidence: value.confidence,
    riskLevel: value.riskLevel,
  }));
});

const scoreTrend = computed(() => {
  return evaluations.value
    .filter(e => e.status === 'completed' && e.overallScore !== undefined)
    .map(e => ({
      date: e.completedAt || e.startedAt,
      value: e.overallScore!,
      label: `v${e.modelVersion || '1.0'}`,
    }))
    .reverse();
});

const findings = computed(() => {
  if (!latestEvaluation.value?.findings) return [];
  return latestEvaluation.value.findings;
});

async function loadData() {
  loading.value = true;
  try {
    await modelsStore.fetchModel(modelId.value);
    model.value = modelsStore.currentModel;
    
    await evaluationsStore.fetchEvaluations({ modelId: modelId.value });
    evaluations.value = evaluationsStore.evaluations;
  } catch (error) {
    console.error('Failed to load model:', error);
  } finally {
    loading.value = false;
  }
}

async function startEvaluation() {
  if (!model.value) return;
  
  try {
    const evaluation = await evaluationsStore.createEvaluation({
      modelId: model.value.id,
      name: `Evaluation - ${new Date().toISOString().split('T')[0]}`,
      pillars: model.value.modelType === 'predictive' 
        ? ['explain', 'fairness', 'robustness', 'privacy']
        : ['toxicity', 'security', 'privacy', 'fairness'],
    });
    
    router.push(`/guardstack/evaluations/${evaluation.id}`);
  } catch (error) {
    console.error('Failed to start evaluation:', error);
  }
}

function goToEvaluation(evaluation: Evaluation) {
  router.push(`/guardstack/evaluations/${evaluation.id}`);
}

onMounted(loadData);
</script>

<template>
  <div class="model-detail p-6">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <!-- Content -->
    <template v-else-if="model">
      <!-- Header -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <button
              class="text-gray-400 hover:text-gray-600"
              @click="router.back()"
            >
              ← Back
            </button>
          </div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {{ model.name }}
          </h1>
          <div class="flex items-center gap-4 mt-2">
            <span class="text-gray-500 dark:text-gray-400 capitalize">
              {{ model.modelType }} Model
            </span>
            <span class="text-gray-400">•</span>
            <span class="text-gray-500 dark:text-gray-400">
              Version {{ model.version }}
            </span>
            <StatusBadge
              v-if="model.riskLevel"
              :status="model.riskLevel === 'high' || model.riskLevel === 'critical' ? 'fail' : 
                       model.riskLevel === 'medium' ? 'warn' : 'pass'"
              :label="`${model.riskLevel} Risk`"
            />
          </div>
        </div>
        
        <div class="flex items-center gap-3">
          <button
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            @click="startEvaluation"
          >
            New Evaluation
          </button>
        </div>
      </div>
      
      <!-- Score overview -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <!-- Current score -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
            Current Safety Score
          </h3>
          <div class="flex items-center justify-center">
            <ScoreGauge
              :score="model.lastScore || 0"
              :size="150"
              :show-label="true"
            />
          </div>
        </div>
        
        <!-- Pillar radar -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
            Pillar Breakdown
          </h3>
          <PillarRadar
            v-if="pillarScores.length > 0"
            :scores="pillarScores.reduce((acc, p) => ({ ...acc, [p.pillar]: p.score }), {})"
            :size="200"
          />
          <div v-else class="flex items-center justify-center h-48 text-gray-400">
            No evaluation data
          </div>
        </div>
        
        <!-- Score trend -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
            Score Trend
          </h3>
          <TrendChart
            v-if="scoreTrend.length > 0"
            :data="scoreTrend"
            :height="180"
            :thresholds="[{ value: 60, color: '#f59e0b', label: 'Min' }]"
          />
          <div v-else class="flex items-center justify-center h-48 text-gray-400">
            No trend data
          </div>
        </div>
      </div>
      
      <!-- Tabs -->
      <div class="border-b mb-6">
        <nav class="flex gap-6">
          <button
            v-for="tab in ['overview', 'evaluations', 'findings', 'settings']"
            :key="tab"
            :class="[
              'py-3 border-b-2 font-medium capitalize transition-colors',
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700',
            ]"
            @click="activeTab = tab"
          >
            {{ tab }}
          </button>
        </nav>
      </div>
      
      <!-- Tab content -->
      <div class="tab-content">
        <!-- Overview -->
        <div v-if="activeTab === 'overview'">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Model info -->
            <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
              <h3 class="font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Model Information
              </h3>
              <dl class="space-y-3">
                <div class="flex justify-between">
                  <dt class="text-gray-500 dark:text-gray-400">Framework</dt>
                  <dd class="text-gray-900 dark:text-gray-100">{{ model.framework || 'N/A' }}</dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-gray-500 dark:text-gray-400">Created</dt>
                  <dd class="text-gray-900 dark:text-gray-100">
                    {{ new Date(model.createdAt).toLocaleDateString() }}
                  </dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-gray-500 dark:text-gray-400">Last Evaluated</dt>
                  <dd class="text-gray-900 dark:text-gray-100">
                    {{ model.lastEvaluatedAt ? new Date(model.lastEvaluatedAt).toLocaleDateString() : 'Never' }}
                  </dd>
                </div>
                <div class="flex justify-between">
                  <dt class="text-gray-500 dark:text-gray-400">Evaluations</dt>
                  <dd class="text-gray-900 dark:text-gray-100">{{ evaluations.length }}</dd>
                </div>
              </dl>
            </div>
            
            <!-- Pillar scores -->
            <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
              <h3 class="font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Pillar Scores
              </h3>
              <div class="grid grid-cols-2 gap-3">
                <PillarScoreCard
                  v-for="pillar in pillarScores"
                  :key="pillar.pillar"
                  :pillar="pillar.pillar"
                  :score="pillar.score"
                  :confidence="pillar.confidence"
                  :risk-level="pillar.riskLevel"
                  compact
                />
              </div>
            </div>
          </div>
        </div>
        
        <!-- Evaluations -->
        <div v-else-if="activeTab === 'evaluations'">
          <div class="bg-white dark:bg-gray-800 rounded-lg border">
            <table class="w-full">
              <thead class="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Name</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Status</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Score</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Date</th>
                  <th class="px-4 py-3 text-left text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="evaluation in evaluations"
                  :key="evaluation.id"
                  class="border-t hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <td class="px-4 py-3 text-gray-900 dark:text-gray-100">
                    {{ evaluation.name }}
                  </td>
                  <td class="px-4 py-3">
                    <StatusBadge
                      :status="evaluation.status === 'completed' ? 'pass' : 
                               evaluation.status === 'failed' ? 'fail' : 
                               evaluation.status === 'running' ? 'pending' : 'warn'"
                      :label="evaluation.status"
                    />
                  </td>
                  <td class="px-4 py-3">
                    <span
                      v-if="evaluation.overallScore !== undefined"
                      :class="[
                        'font-semibold',
                        evaluation.overallScore >= 80 ? 'text-green-600' :
                        evaluation.overallScore >= 60 ? 'text-yellow-600' : 'text-red-600'
                      ]"
                    >
                      {{ Math.round(evaluation.overallScore) }}
                    </span>
                    <span v-else class="text-gray-400">—</span>
                  </td>
                  <td class="px-4 py-3 text-gray-500 dark:text-gray-400">
                    {{ new Date(evaluation.startedAt || evaluation.createdAt).toLocaleDateString() }}
                  </td>
                  <td class="px-4 py-3">
                    <button
                      class="text-blue-600 hover:underline"
                      @click="goToEvaluation(evaluation)"
                    >
                      View
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Findings -->
        <div v-else-if="activeTab === 'findings'">
          <FindingsTable
            :findings="findings"
            :show-pagination="true"
            :page-size="10"
          />
        </div>
        
        <!-- Settings -->
        <div v-else-if="activeTab === 'settings'">
          <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 class="font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Model Settings
            </h3>
            <p class="text-gray-500 dark:text-gray-400">
              Configure model-specific settings, thresholds, and notification preferences.
            </p>
            <!-- Settings form would go here -->
          </div>
        </div>
      </div>
    </template>
    
    <!-- Not found -->
    <div v-else class="text-center py-12">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
        Model not found
      </h2>
      <p class="text-gray-500 dark:text-gray-400 mt-2">
        The model you're looking for doesn't exist or has been deleted.
      </p>
      <button
        class="mt-4 text-blue-600 hover:underline"
        @click="router.push('/guardstack/models')"
      >
        Back to Models
      </button>
    </div>
  </div>
</template>
