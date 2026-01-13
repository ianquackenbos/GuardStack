<script lang="ts" setup>
/**
 * Evaluation Detail Page
 * Displays evaluation results with full details
 */
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useEvaluationsStore } from '../../store/evaluations';
import { useModelsStore } from '../../store/models';
import StatusBadge from '../../components/StatusBadge.vue';
import ScoreGauge from '../../components/ScoreGauge.vue';
import PillarRadar from '../../components/PillarRadar.vue';
import PillarScoreCard from '../../components/PillarScoreCard.vue';
import FindingsTable from '../../components/FindingsTable.vue';
import ProgressTracker from '../../components/ProgressTracker.vue';
import BeforeAfterChart from '../../components/BeforeAfterChart.vue';
import type { Evaluation, Model } from '../../types';

const route = useRoute();
const router = useRouter();
const evaluationsStore = useEvaluationsStore();
const modelsStore = useModelsStore();

const loading = ref(true);
const evaluation = ref<Evaluation | null>(null);
const model = ref<Model | null>(null);
const activeTab = ref('results');
const wsUnsubscribe = ref<(() => void) | null>(null);

const evaluationId = computed(() => route.params.id as string);

const isRunning = computed(() => 
  evaluation.value?.status === 'running' || evaluation.value?.status === 'pending'
);

const pillarScores = computed(() => {
  if (!evaluation.value?.pillarScores) return [];
  return Object.entries(evaluation.value.pillarScores).map(([key, value]) => ({
    pillar: key,
    score: value.score,
    confidence: value.confidence,
    riskLevel: value.riskLevel,
    recommendations: value.recommendations,
  }));
});

const radarScores = computed(() => {
  if (!evaluation.value?.pillarScores) return {};
  return Object.entries(evaluation.value.pillarScores).reduce((acc, [key, value]) => {
    acc[key] = value.score;
    return acc;
  }, {} as Record<string, number>);
});

const evaluationStages = computed(() => {
  const stages = [
    { id: 'setup', name: 'Setup', status: 'completed' as const },
    { id: 'data', name: 'Data Loading', status: 'completed' as const },
  ];
  
  const pillars = evaluation.value?.pillars || [];
  pillars.forEach(pillar => {
    const pillarScore = evaluation.value?.pillarScores?.[pillar];
    let status: 'pending' | 'running' | 'completed' | 'failed' = 'pending';
    
    if (pillarScore) {
      status = 'completed';
    } else if (evaluation.value?.currentPillar === pillar) {
      status = 'running';
    }
    
    stages.push({
      id: pillar,
      name: pillar.charAt(0).toUpperCase() + pillar.slice(1),
      status,
    });
  });
  
  stages.push({
    id: 'aggregate',
    name: 'Aggregation',
    status: evaluation.value?.status === 'completed' ? 'completed' : 'pending',
  });
  
  return stages;
});

const comparisonData = computed(() => {
  if (!evaluation.value?.previousScores || !evaluation.value?.pillarScores) return [];
  
  return Object.keys(evaluation.value.pillarScores).map(pillar => ({
    label: pillar.charAt(0).toUpperCase() + pillar.slice(1),
    before: evaluation.value!.previousScores?.[pillar] || 0,
    after: evaluation.value!.pillarScores![pillar].score,
  }));
});

async function loadData() {
  loading.value = true;
  try {
    await evaluationsStore.fetchEvaluation(evaluationId.value);
    evaluation.value = evaluationsStore.currentEvaluation;
    
    if (evaluation.value?.modelId) {
      await modelsStore.fetchModel(evaluation.value.modelId);
      model.value = modelsStore.currentModel;
    }
    
    // Subscribe to updates if running
    if (isRunning.value) {
      wsUnsubscribe.value = evaluationsStore.subscribeToProgress(
        evaluationId.value,
        (progress) => {
          if (evaluation.value) {
            evaluation.value = { ...evaluation.value, ...progress };
          }
        }
      );
    }
  } catch (error) {
    console.error('Failed to load evaluation:', error);
  } finally {
    loading.value = false;
  }
}

async function cancelEvaluation() {
  if (!evaluation.value) return;
  
  try {
    await evaluationsStore.cancelEvaluation(evaluation.value.id);
    await loadData();
  } catch (error) {
    console.error('Failed to cancel evaluation:', error);
  }
}

async function rerunEvaluation() {
  if (!evaluation.value) return;
  
  try {
    const newEval = await evaluationsStore.createEvaluation({
      modelId: evaluation.value.modelId,
      name: `${evaluation.value.name} (Rerun)`,
      pillars: evaluation.value.pillars,
      config: evaluation.value.config,
    });
    
    router.push(`/guardstack/evaluations/${newEval.id}`);
  } catch (error) {
    console.error('Failed to rerun evaluation:', error);
  }
}

function downloadReport() {
  // Generate and download PDF report
  console.log('Downloading report for evaluation:', evaluation.value?.id);
}

onMounted(loadData);

onUnmounted(() => {
  if (wsUnsubscribe.value) {
    wsUnsubscribe.value();
  }
});
</script>

<template>
  <div class="evaluation-detail p-6">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <!-- Content -->
    <template v-else-if="evaluation">
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
            {{ evaluation.name }}
          </h1>
          <div class="flex items-center gap-4 mt-2">
            <span v-if="model" class="text-gray-500 dark:text-gray-400">
              {{ model.name }}
            </span>
            <span class="text-gray-400">•</span>
            <StatusBadge
              :status="evaluation.status === 'completed' ? 'pass' : 
                       evaluation.status === 'failed' ? 'fail' : 
                       evaluation.status === 'running' ? 'pending' : 'warn'"
              :label="evaluation.status"
            />
            <span v-if="evaluation.startedAt" class="text-gray-500 dark:text-gray-400">
              {{ new Date(evaluation.startedAt).toLocaleString() }}
            </span>
          </div>
        </div>
        
        <div class="flex items-center gap-3">
          <button
            v-if="isRunning"
            class="px-4 py-2 border border-red-600 text-red-600 rounded-lg hover:bg-red-50"
            @click="cancelEvaluation"
          >
            Cancel
          </button>
          <button
            v-if="evaluation.status === 'completed'"
            class="px-4 py-2 border rounded-lg hover:bg-gray-50"
            @click="downloadReport"
          >
            Download Report
          </button>
          <button
            v-if="evaluation.status === 'completed' || evaluation.status === 'failed'"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            @click="rerunEvaluation"
          >
            Rerun
          </button>
        </div>
      </div>
      
      <!-- Progress tracker (if running) -->
      <div v-if="isRunning" class="bg-white dark:bg-gray-800 rounded-lg border p-6 mb-6">
        <h3 class="font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Evaluation Progress
        </h3>
        <ProgressTracker
          :stages="evaluationStages"
          :current-stage="evaluation.currentPillar"
          :show-duration="true"
        />
      </div>
      
      <!-- Results (if completed) -->
      <template v-if="evaluation.status === 'completed'">
        <!-- Score overview -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
              Overall Score
            </h3>
            <div class="flex items-center justify-center">
              <ScoreGauge
                :score="evaluation.overallScore || 0"
                :size="150"
                :show-label="true"
              />
            </div>
          </div>
          
          <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
              Pillar Scores
            </h3>
            <PillarRadar
              v-if="Object.keys(radarScores).length > 0"
              :scores="radarScores"
              :size="200"
            />
          </div>
          
          <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
              Summary
            </h3>
            <dl class="space-y-3 text-sm">
              <div class="flex justify-between">
                <dt class="text-gray-500">Pillars Evaluated</dt>
                <dd class="text-gray-900 dark:text-gray-100">{{ evaluation.pillars?.length || 0 }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">Findings</dt>
                <dd class="text-gray-900 dark:text-gray-100">{{ evaluation.findings?.length || 0 }}</dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">Duration</dt>
                <dd class="text-gray-900 dark:text-gray-100">
                  {{ evaluation.duration ? `${(evaluation.duration / 1000).toFixed(1)}s` : 'N/A' }}
                </dd>
              </div>
              <div class="flex justify-between">
                <dt class="text-gray-500">Risk Level</dt>
                <dd class="capitalize" :class="[
                  evaluation.riskLevel === 'high' || evaluation.riskLevel === 'critical' 
                    ? 'text-red-600' 
                    : evaluation.riskLevel === 'medium' ? 'text-yellow-600' : 'text-green-600'
                ]">
                  {{ evaluation.riskLevel || 'N/A' }}
                </dd>
              </div>
            </dl>
          </div>
        </div>
        
        <!-- Tabs -->
        <div class="border-b mb-6">
          <nav class="flex gap-6">
            <button
              v-for="tab in ['results', 'findings', 'comparison', 'raw']"
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
          <!-- Results -->
          <div v-if="activeTab === 'results'">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <PillarScoreCard
                v-for="pillar in pillarScores"
                :key="pillar.pillar"
                :pillar="pillar.pillar"
                :score="pillar.score"
                :confidence="pillar.confidence"
                :risk-level="pillar.riskLevel"
                :recommendations="pillar.recommendations"
                :expandable="true"
              />
            </div>
          </div>
          
          <!-- Findings -->
          <div v-else-if="activeTab === 'findings'">
            <FindingsTable
              :findings="evaluation.findings || []"
              :show-pagination="true"
              :page-size="10"
              :selectable="true"
            />
          </div>
          
          <!-- Comparison -->
          <div v-else-if="activeTab === 'comparison'">
            <BeforeAfterChart
              v-if="comparisonData.length > 0"
              :data="comparisonData"
              title="Score Comparison"
              before-label="Previous"
              after-label="Current"
              :threshold="60"
            />
            <div v-else class="text-center py-12 text-gray-500">
              No previous evaluation to compare with
            </div>
          </div>
          
          <!-- Raw data -->
          <div v-else-if="activeTab === 'raw'">
            <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 overflow-auto max-h-96">
              <pre class="text-sm text-gray-700 dark:text-gray-300">{{ JSON.stringify(evaluation, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </template>
      
      <!-- Failed state -->
      <div v-else-if="evaluation.status === 'failed'" class="bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 p-6">
        <h3 class="font-semibold text-red-600 mb-2">Evaluation Failed</h3>
        <p class="text-gray-700 dark:text-gray-300">
          {{ evaluation.error || 'An unknown error occurred during evaluation.' }}
        </p>
        <button
          class="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          @click="rerunEvaluation"
        >
          Retry Evaluation
        </button>
      </div>
    </template>
    
    <!-- Not found -->
    <div v-else class="text-center py-12">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
        Evaluation not found
      </h2>
      <p class="text-gray-500 dark:text-gray-400 mt-2">
        The evaluation you're looking for doesn't exist.
      </p>
      <button
        class="mt-4 text-blue-600 hover:underline"
        @click="router.push('/guardstack/evaluations')"
      >
        Back to Evaluations
      </button>
    </div>
  </div>
</template>
