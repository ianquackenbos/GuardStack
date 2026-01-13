<script setup lang="ts">
/**
 * GenAI Model Detail Page
 * 
 * Displays 4-pillar evaluation results for Generative AI models.
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
const activeTab = ref('overview');

// 4 Pillars for GenAI
const pillars = [
  { key: 'content_safety', name: 'Content Safety', icon: 'icon-shield-check', color: '#EF4444', description: 'Harmful, toxic, or inappropriate content generation' },
  { key: 'prompt_injection', name: 'Prompt Injection', icon: 'icon-code', color: '#F59E0B', description: 'Resistance to prompt injection attacks' },
  { key: 'hallucination', name: 'Hallucination', icon: 'icon-alert-triangle', color: '#8B5CF6', description: 'Factual accuracy and grounding' },
  { key: 'bias_toxicity', name: 'Bias & Toxicity', icon: 'icon-users', color: '#3B82F6', description: 'Fairness and harmful bias detection' },
];

// Garak probe categories
const garakCategories = [
  { key: 'dan', name: 'DAN Jailbreaks', count: 0 },
  { key: 'encoding', name: 'Encoding Attacks', count: 0 },
  { key: 'glitch', name: 'Glitch Tokens', count: 0 },
  { key: 'knownbadsignatures', name: 'Known Bad Signatures', count: 0 },
  { key: 'misleading', name: 'Misleading Prompts', count: 0 },
  { key: 'packagehallucination', name: 'Package Hallucination', count: 0 },
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

const garakResults = computed(() => {
  if (!latestEvaluation.value?.results) return null;
  return latestEvaluation.value.results.garak_results || null;
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
    evaluation_type: 'genai',
    pillars: pillars.map(p => p.key),
    include_garak: true,
  });
}

function getRiskLevel(score: number): string {
  if (score >= 80) return 'low';
  if (score >= 60) return 'medium';
  if (score >= 40) return 'high';
  return 'critical';
}
</script>

<template>
  <div class="genai-model-view">
    <header class="model-header">
      <div class="model-info">
        <h1>{{ model?.name || 'Loading...' }}</h1>
        <p class="model-type">Generative AI Model</p>
        <StatusBadge v-if="model" :status="model.status" />
      </div>
      <div class="model-actions">
        <button class="btn role-secondary" @click="activeTab = 'garak'">
          <i class="icon icon-terminal" />
          Garak Results
        </button>
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
      <!-- Tab Navigation -->
      <nav class="tab-nav">
        <button 
          :class="['tab', { active: activeTab === 'overview' }]"
          @click="activeTab = 'overview'"
        >
          Overview
        </button>
        <button 
          :class="['tab', { active: activeTab === 'pillars' }]"
          @click="activeTab = 'pillars'"
        >
          4-Pillar Analysis
        </button>
        <button 
          :class="['tab', { active: activeTab === 'garak' }]"
          @click="activeTab = 'garak'"
        >
          Garak Probes
        </button>
        <button 
          :class="['tab', { active: activeTab === 'history' }]"
          @click="activeTab = 'history'"
        >
          History
        </button>
      </nav>

      <!-- Overview Tab -->
      <div v-if="activeTab === 'overview'" class="tab-content">
        <div class="overview-grid">
          <div class="score-card main-score">
            <h2>Overall Safety Score</h2>
            <ScoreGauge :score="overallScore" :size="180" />
            <div :class="['risk-badge', getRiskLevel(overallScore)]">
              {{ getRiskLevel(overallScore).toUpperCase() }} RISK
            </div>
          </div>
          
          <div class="pillars-summary">
            <h3>4-Pillar Summary</h3>
            <div class="pillar-bars">
              <div v-for="pillar in pillars" :key="pillar.key" class="pillar-bar">
                <div class="pillar-label">
                  <i :class="['icon', pillar.icon]" :style="{ color: pillar.color }" />
                  <span>{{ pillar.name }}</span>
                </div>
                <div class="bar-container">
                  <div 
                    class="bar-fill"
                    :style="{ 
                      width: `${pillarScores[pillar.key] || 0}%`,
                      backgroundColor: pillar.color 
                    }"
                  />
                </div>
                <span class="score-value">{{ pillarScores[pillar.key]?.toFixed(0) || 0 }}%</span>
              </div>
            </div>
          </div>
          
          <div class="quick-stats">
            <h3>Quick Stats</h3>
            <div class="stat-grid">
              <div class="stat">
                <span class="stat-value">{{ evaluationHistory.length }}</span>
                <span class="stat-label">Total Evaluations</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ garakResults?.total_probes || 0 }}</span>
                <span class="stat-label">Garak Probes Run</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ garakResults?.failures || 0 }}</span>
                <span class="stat-label">Probe Failures</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ latestEvaluation?.duration || '-' }}s</span>
                <span class="stat-label">Last Eval Duration</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="trend-section">
          <h3>Score Trend Over Time</h3>
          <TrendChart
            :data="evaluationHistory.map(e => ({ date: e.created_at, value: e.results?.overall_score || 0 }))"
            :height="200"
          />
        </div>
      </div>

      <!-- Pillars Tab -->
      <div v-if="activeTab === 'pillars'" class="tab-content">
        <div class="pillars-grid">
          <div v-for="pillar in pillars" :key="pillar.key" class="pillar-detail-card">
            <div class="pillar-header" :style="{ borderColor: pillar.color }">
              <i :class="['icon', pillar.icon]" :style="{ color: pillar.color }" />
              <h3>{{ pillar.name }}</h3>
              <ScoreGauge :score="pillarScores[pillar.key] || 0" :size="80" />
            </div>
            <p class="pillar-description">{{ pillar.description }}</p>
            
            <div class="pillar-metrics" v-if="latestEvaluation?.results?.pillar_details?.[pillar.key]">
              <h4>Metrics</h4>
              <div 
                v-for="(value, metric) in latestEvaluation.results.pillar_details[pillar.key]"
                :key="metric"
                class="metric-row"
              >
                <span class="metric-name">{{ metric }}</span>
                <span class="metric-value">{{ typeof value === 'number' ? (value * 100).toFixed(1) + '%' : value }}</span>
              </div>
            </div>
            
            <div class="pillar-issues" v-if="latestEvaluation?.results?.pillar_issues?.[pillar.key]?.length">
              <h4>Issues Found</h4>
              <ul>
                <li v-for="(issue, idx) in latestEvaluation.results.pillar_issues[pillar.key].slice(0, 5)" :key="idx">
                  {{ issue }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Garak Tab -->
      <div v-if="activeTab === 'garak'" class="tab-content">
        <div class="garak-header">
          <h2>Garak Security Probes</h2>
          <p>Results from automated LLM security testing using Garak framework</p>
        </div>
        
        <div v-if="garakResults" class="garak-results">
          <div class="garak-summary">
            <div class="summary-stat passed">
              <span class="value">{{ garakResults.passed || 0 }}</span>
              <span class="label">Passed</span>
            </div>
            <div class="summary-stat failed">
              <span class="value">{{ garakResults.failures || 0 }}</span>
              <span class="label">Failed</span>
            </div>
            <div class="summary-stat total">
              <span class="value">{{ garakResults.total_probes || 0 }}</span>
              <span class="label">Total Probes</span>
            </div>
          </div>
          
          <div class="probe-categories">
            <h3>Probe Categories</h3>
            <div class="category-grid">
              <div v-for="cat in garakCategories" :key="cat.key" class="category-card">
                <h4>{{ cat.name }}</h4>
                <div class="category-results">
                  <span class="passed">{{ garakResults.categories?.[cat.key]?.passed || 0 }} passed</span>
                  <span class="failed">{{ garakResults.categories?.[cat.key]?.failed || 0 }} failed</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="failed-probes" v-if="garakResults.failed_probes?.length">
            <h3>Failed Probes</h3>
            <table class="probe-table">
              <thead>
                <tr>
                  <th>Probe</th>
                  <th>Category</th>
                  <th>Severity</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="probe in garakResults.failed_probes" :key="probe.id">
                  <td>{{ probe.name }}</td>
                  <td>{{ probe.category }}</td>
                  <td>
                    <span :class="['severity-badge', probe.severity]">
                      {{ probe.severity }}
                    </span>
                  </td>
                  <td>{{ probe.details }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <div v-else class="no-garak">
          <i class="icon icon-terminal" />
          <p>No Garak results available</p>
          <button class="btn role-primary" @click="startEvaluation">
            Run Garak Probes
          </button>
        </div>
      </div>

      <!-- History Tab -->
      <div v-if="activeTab === 'history'" class="tab-content">
        <h2>Evaluation History</h2>
        <EvaluationTimeline :evaluations="evaluationHistory" :showDetails="true" />
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.genai-model-view {
  padding: 20px;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  
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
  
  .model-actions {
    display: flex;
    gap: 10px;
  }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--body-text);
}

.tab-nav {
  display: flex;
  gap: 5px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
  
  .tab {
    padding: 10px 20px;
    background: none;
    border: none;
    color: var(--body-text);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    
    &:hover {
      color: var(--link);
    }
    
    &.active {
      color: var(--link);
      border-bottom-color: var(--link);
    }
  }
}

.tab-content {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.overview-grid {
  display: grid;
  grid-template-columns: 250px 1fr 300px;
  gap: 20px;
  margin-bottom: 30px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
}

.score-card, .pillars-summary, .quick-stats {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
}

.main-score {
  text-align: center;
  
  h2 {
    margin: 0 0 20px 0;
    font-size: 16px;
  }
  
  .risk-badge {
    margin-top: 15px;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    
    &.low { background: #10B981; color: white; }
    &.medium { background: #F59E0B; color: white; }
    &.high { background: #EF4444; color: white; }
    &.critical { background: #7F1D1D; color: white; }
  }
}

.pillars-summary {
  h3 {
    margin: 0 0 20px 0;
  }
  
  .pillar-bar {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    
    .pillar-label {
      width: 150px;
      display: flex;
      align-items: center;
      gap: 8px;
      
      i { font-size: 16px; }
    }
    
    .bar-container {
      flex: 1;
      height: 8px;
      background: var(--disabled-bg);
      border-radius: 4px;
      overflow: hidden;
      margin: 0 15px;
      
      .bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
      }
    }
    
    .score-value {
      width: 50px;
      text-align: right;
      font-weight: 600;
    }
  }
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  
  .stat {
    text-align: center;
    
    .stat-value {
      display: block;
      font-size: 24px;
      font-weight: 600;
      color: var(--link);
    }
    
    .stat-label {
      font-size: 12px;
      color: var(--body-text);
      opacity: 0.7;
    }
  }
}

.pillars-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  
  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.pillar-detail-card {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
  
  .pillar-header {
    display: flex;
    align-items: center;
    gap: 15px;
    padding-bottom: 15px;
    border-bottom: 2px solid;
    margin-bottom: 15px;
    
    i { font-size: 24px; }
    h3 { flex: 1; margin: 0; }
  }
  
  .pillar-description {
    color: var(--body-text);
    opacity: 0.8;
    margin-bottom: 15px;
  }
  
  h4 {
    margin: 15px 0 10px 0;
    font-size: 14px;
    color: var(--body-text);
  }
  
  .metric-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
    
    .metric-name { text-transform: capitalize; }
    .metric-value { font-weight: 600; }
  }
  
  .pillar-issues ul {
    margin: 0;
    padding-left: 20px;
    
    li {
      padding: 3px 0;
      color: var(--error);
    }
  }
}

.garak-header {
  margin-bottom: 20px;
  
  h2 { margin: 0 0 5px 0; }
  p { color: var(--body-text); opacity: 0.8; margin: 0; }
}

.garak-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  
  .summary-stat {
    flex: 1;
    text-align: center;
    padding: 20px;
    border-radius: var(--border-radius);
    
    &.passed { background: rgba(16, 185, 129, 0.1); }
    &.failed { background: rgba(239, 68, 68, 0.1); }
    &.total { background: var(--box-bg); border: 1px solid var(--border); }
    
    .value {
      display: block;
      font-size: 32px;
      font-weight: 600;
    }
    
    .label {
      font-size: 14px;
      color: var(--body-text);
    }
  }
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.category-card {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 15px;
  
  h4 { margin: 0 0 10px 0; font-size: 14px; }
  
  .category-results {
    display: flex;
    gap: 15px;
    font-size: 12px;
    
    .passed { color: #10B981; }
    .failed { color: #EF4444; }
  }
}

.probe-table {
  width: 100%;
  border-collapse: collapse;
  
  th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }
  
  th {
    background: var(--box-bg);
    font-weight: 600;
  }
  
  .severity-badge {
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 12px;
    
    &.high { background: #EF4444; color: white; }
    &.medium { background: #F59E0B; color: white; }
    &.low { background: #10B981; color: white; }
  }
}

.no-garak {
  text-align: center;
  padding: 60px;
  
  i { font-size: 48px; color: var(--disabled-bg); }
  p { margin: 20px 0; color: var(--body-text); }
}
</style>
