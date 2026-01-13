<script setup lang="ts">
/**
 * Predictive ML Model Detail Page
 * 
 * Displays 8-pillar evaluation results for traditional ML models.
 */
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useModelsStore } from '../../../store/models';
import { useEvaluationsStore } from '../../../store/evaluations';
import { StatusBadge, ScoreGauge, TrendChart, PillarCard, EvaluationTimeline } from '../../../components';

const route = useRoute();
const modelsStore = useModelsStore();
const evaluationsStore = useEvaluationsStore();

const modelId = computed(() => route.params.id as string);
const model = computed(() => modelsStore.models.find(m => m.id === modelId.value));
const loading = ref(true);

// 8 Pillars for Predictive AI
const pillars = [
  { key: 'fairness', name: 'Fairness', icon: 'icon-scale', color: '#3B82F6' },
  { key: 'explainability', name: 'Explainability', icon: 'icon-lightbulb', color: '#10B981' },
  { key: 'robustness', name: 'Robustness', icon: 'icon-shield', color: '#8B5CF6' },
  { key: 'transparency', name: 'Transparency', icon: 'icon-eye', color: '#F59E0B' },
  { key: 'privacy', name: 'Privacy', icon: 'icon-lock', color: '#EF4444' },
  { key: 'accountability', name: 'Accountability', icon: 'icon-clipboard', color: '#6366F1' },
  { key: 'safety', name: 'Safety', icon: 'icon-alert', color: '#EC4899' },
  { key: 'human_oversight', name: 'Human Oversight', icon: 'icon-user', color: '#14B8A6' },
];

const latestEvaluation = computed(() => {
  if (!model.value) return null;
  return evaluationsStore.getLatestEvaluation(modelId.value);
});

const pillarScores = computed(() => {
  if (!latestEvaluation.value?.results) return {};
  return latestEvaluation.value.results.pillar_scores || {};
});

const overallScore = computed(() => {
  if (!latestEvaluation.value?.results) return 0;
  return latestEvaluation.value.results.overall_score || 0;
});

const evaluationHistory = computed(() => {
  return evaluationsStore.getModelEvaluations(modelId.value);
});

onMounted(async () => {
  loading.value = true;
  await Promise.all([
    modelsStore.fetchModel(modelId.value),
    evaluationsStore.fetchModelEvaluations(modelId.value),
  ]);
  loading.value = false;
});

function startEvaluation() {
  evaluationsStore.startEvaluation({
    model_id: modelId.value,
    evaluation_type: 'predictive',
    pillars: pillars.map(p => p.key),
  });
}
</script>

<template>
  <div class="predictive-model-view">
    <header class="model-header">
      <div class="model-info">
        <h1>{{ model?.name || 'Loading...' }}</h1>
        <p class="model-type">Predictive ML Model</p>
        <StatusBadge v-if="model" :status="model.status" />
      </div>
      <div class="model-actions">
        <button class="btn role-primary" @click="startEvaluation">
          <i class="icon icon-play" />
          Run Evaluation
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading-state">
      <i class="icon icon-spinner icon-spin" />
      Loading model data...
    </div>

    <template v-else>
      <!-- Overall Score -->
      <section class="overall-score-section">
        <div class="score-card">
          <h2>Overall Safety Score</h2>
          <ScoreGauge :score="overallScore" :size="200" />
          <p class="score-description">
            Aggregated score across all 8 evaluation pillars
          </p>
        </div>
        <div class="trend-card">
          <h3>Score Trend</h3>
          <TrendChart
            :data="evaluationHistory.map(e => ({ date: e.created_at, value: e.results?.overall_score || 0 }))"
            :height="150"
          />
        </div>
      </section>

      <!-- 8 Pillars Grid -->
      <section class="pillars-section">
        <h2>8-Pillar Evaluation</h2>
        <div class="pillars-grid">
          <PillarCard
            v-for="pillar in pillars"
            :key="pillar.key"
            :name="pillar.name"
            :icon="pillar.icon"
            :color="pillar.color"
            :score="pillarScores[pillar.key] || 0"
            :details="latestEvaluation?.results?.pillar_details?.[pillar.key]"
          />
        </div>
      </section>

      <!-- Detailed Results -->
      <section class="details-section">
        <div class="details-tabs">
          <h3>Detailed Analysis</h3>
          
          <!-- Fairness Details -->
          <div class="detail-panel" v-if="pillarScores.fairness">
            <h4>Fairness Analysis</h4>
            <div class="metrics-grid">
              <div class="metric">
                <span class="metric-label">Demographic Parity</span>
                <span class="metric-value">{{ (pillarScores.fairness_details?.demographic_parity * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">Equal Opportunity</span>
                <span class="metric-value">{{ (pillarScores.fairness_details?.equal_opportunity * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">Disparate Impact</span>
                <span class="metric-value">{{ (pillarScores.fairness_details?.disparate_impact * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>

          <!-- Robustness Details -->
          <div class="detail-panel" v-if="pillarScores.robustness">
            <h4>Robustness Analysis</h4>
            <div class="metrics-grid">
              <div class="metric">
                <span class="metric-label">Adversarial Resistance</span>
                <span class="metric-value">{{ (pillarScores.robustness_details?.adversarial_resistance * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">Distribution Shift Tolerance</span>
                <span class="metric-value">{{ (pillarScores.robustness_details?.distribution_shift * 100).toFixed(1) }}%</span>
              </div>
              <div class="metric">
                <span class="metric-label">Noise Sensitivity</span>
                <span class="metric-value">{{ (pillarScores.robustness_details?.noise_sensitivity * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Evaluation History -->
      <section class="history-section">
        <h2>Evaluation History</h2>
        <EvaluationTimeline :evaluations="evaluationHistory" />
      </section>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.predictive-model-view {
  padding: 20px;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
  
  .model-info {
    h1 {
      margin: 0 0 5px 0;
      font-size: 24px;
    }
    
    .model-type {
      color: var(--body-text);
      margin: 0 0 10px 0;
      opacity: 0.7;
    }
  }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--body-text);
  
  i {
    margin-right: 10px;
  }
}

.overall-score-section {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  margin-bottom: 30px;
  
  .score-card,
  .trend-card {
    background: var(--box-bg);
    border: 1px solid var(--border);
    border-radius: var(--border-radius);
    padding: 20px;
  }
  
  .score-card {
    text-align: center;
    
    h2 {
      margin: 0 0 20px 0;
    }
    
    .score-description {
      color: var(--body-text);
      opacity: 0.7;
      margin-top: 15px;
    }
  }
  
  .trend-card {
    h3 {
      margin: 0 0 15px 0;
    }
  }
}

.pillars-section {
  margin-bottom: 30px;
  
  h2 {
    margin: 0 0 20px 0;
  }
  
  .pillars-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 15px;
  }
}

.details-section {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
  margin-bottom: 30px;
  
  h3 {
    margin: 0 0 20px 0;
  }
  
  .detail-panel {
    border-bottom: 1px solid var(--border);
    padding-bottom: 20px;
    margin-bottom: 20px;
    
    &:last-child {
      border-bottom: none;
      margin-bottom: 0;
      padding-bottom: 0;
    }
    
    h4 {
      margin: 0 0 15px 0;
      color: var(--link);
    }
  }
  
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
    
    .metric {
      display: flex;
      flex-direction: column;
      
      .metric-label {
        font-size: 12px;
        color: var(--body-text);
        opacity: 0.7;
        margin-bottom: 5px;
      }
      
      .metric-value {
        font-size: 18px;
        font-weight: 600;
      }
    }
  }
}

.history-section {
  h2 {
    margin: 0 0 20px 0;
  }
}
</style>
