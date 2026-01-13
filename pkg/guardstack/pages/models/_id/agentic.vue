<script setup lang="ts">
/**
 * Agentic AI Model Detail Page
 * 
 * Displays evaluation results for autonomous AI agents.
 */
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useModelsStore } from '../../../store/models';
import { useEvaluationsStore } from '../../../store/evaluations';
import { StatusBadge, ScoreGauge, TrendChart, RiskIndicator } from '../../../components';

const route = useRoute();
const modelsStore = useModelsStore();
const evaluationsStore = useEvaluationsStore();

const modelId = computed(() => route.params.id as string);
const model = computed(() => modelsStore.models.find(m => m.id === modelId.value));
const loading = ref(true);
const activeTab = ref('overview');

// Agentic evaluation dimensions
const dimensions = [
  { 
    key: 'tool_safety', 
    name: 'Tool Safety', 
    icon: 'icon-tool',
    description: 'Safe usage of external tools and APIs'
  },
  { 
    key: 'goal_alignment', 
    name: 'Goal Alignment', 
    icon: 'icon-target',
    description: 'Actions aligned with specified objectives'
  },
  { 
    key: 'boundary_respect', 
    name: 'Boundary Respect', 
    icon: 'icon-shield',
    description: 'Respects operational boundaries and constraints'
  },
  { 
    key: 'reversibility', 
    name: 'Reversibility', 
    icon: 'icon-refresh',
    description: 'Actions can be undone or recovered from'
  },
  { 
    key: 'transparency', 
    name: 'Transparency', 
    icon: 'icon-eye',
    description: 'Clear reasoning and decision explanations'
  },
  { 
    key: 'human_control', 
    name: 'Human Control', 
    icon: 'icon-user',
    description: 'Allows human intervention and override'
  },
];

// Test scenarios
const testScenarios = ref([
  { id: 1, name: 'File System Access', status: 'passed', risk: 'medium' },
  { id: 2, name: 'Network Requests', status: 'passed', risk: 'high' },
  { id: 3, name: 'Code Execution', status: 'failed', risk: 'critical' },
  { id: 4, name: 'Data Exfiltration', status: 'passed', risk: 'critical' },
  { id: 5, name: 'Resource Consumption', status: 'passed', risk: 'medium' },
  { id: 6, name: 'Loop Detection', status: 'passed', risk: 'high' },
]);

const latestEvaluation = computed(() => {
  if (!model.value) return null;
  return evaluationsStore.getLatestEvaluation(modelId.value);
});

const dimensionScores = computed(() => {
  if (!latestEvaluation.value?.results) return {};
  return latestEvaluation.value.results.dimension_scores || {};
});

const overallScore = computed(() => {
  if (!latestEvaluation.value?.results) return 0;
  return latestEvaluation.value.results.overall_score || 0;
});

const sandboxLogs = computed(() => {
  if (!latestEvaluation.value?.results) return [];
  return latestEvaluation.value.results.sandbox_logs || [];
});

const toolUsageStats = computed(() => {
  if (!latestEvaluation.value?.results) return null;
  return latestEvaluation.value.results.tool_usage || null;
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
    evaluation_type: 'agentic',
    scenarios: testScenarios.value.map(s => s.name),
    sandbox_enabled: true,
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
  <div class="agentic-model-view">
    <header class="model-header">
      <div class="model-info">
        <h1>{{ model?.name || 'Loading...' }}</h1>
        <p class="model-type">Agentic AI Model</p>
        <StatusBadge v-if="model" :status="model.status" />
      </div>
      <div class="model-actions">
        <button class="btn role-secondary">
          <i class="icon icon-terminal" />
          View Sandbox Logs
        </button>
        <button class="btn role-primary" @click="startEvaluation">
          <i class="icon icon-play" />
          Run Evaluation
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading-state">
      <i class="icon icon-spinner icon-spin" />
      Loading agent data...
    </div>

    <template v-else>
      <!-- Warning Banner for Agentic Models -->
      <div class="warning-banner">
        <i class="icon icon-alert-triangle" />
        <div class="warning-content">
          <strong>Agentic AI Safety Notice</strong>
          <p>This agent has autonomous capabilities. All evaluations run in isolated sandbox environments.</p>
        </div>
      </div>

      <!-- Tab Navigation -->
      <nav class="tab-nav">
        <button 
          :class="['tab', { active: activeTab === 'overview' }]"
          @click="activeTab = 'overview'"
        >
          Overview
        </button>
        <button 
          :class="['tab', { active: activeTab === 'dimensions' }]"
          @click="activeTab = 'dimensions'"
        >
          Safety Dimensions
        </button>
        <button 
          :class="['tab', { active: activeTab === 'scenarios' }]"
          @click="activeTab = 'scenarios'"
        >
          Test Scenarios
        </button>
        <button 
          :class="['tab', { active: activeTab === 'sandbox' }]"
          @click="activeTab = 'sandbox'"
        >
          Sandbox Logs
        </button>
        <button 
          :class="['tab', { active: activeTab === 'tools' }]"
          @click="activeTab = 'tools'"
        >
          Tool Usage
        </button>
      </nav>

      <!-- Overview Tab -->
      <div v-if="activeTab === 'overview'" class="tab-content">
        <div class="overview-grid">
          <div class="score-card">
            <h2>Agent Safety Score</h2>
            <ScoreGauge :score="overallScore" :size="180" />
            <div :class="['risk-level', getRiskLevel(overallScore)]">
              {{ getRiskLevel(overallScore).toUpperCase() }} RISK
            </div>
          </div>
          
          <div class="dimensions-summary">
            <h3>Safety Dimensions</h3>
            <div class="dimension-bars">
              <div v-for="dim in dimensions" :key="dim.key" class="dimension-bar">
                <div class="dim-label">
                  <i :class="['icon', dim.icon]" />
                  <span>{{ dim.name }}</span>
                </div>
                <div class="bar-wrapper">
                  <div 
                    class="bar-fill"
                    :style="{ width: `${dimensionScores[dim.key] || 0}%` }"
                    :class="getRiskLevel(dimensionScores[dim.key] || 0)"
                  />
                </div>
                <span class="dim-score">{{ (dimensionScores[dim.key] || 0).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
          
          <div class="scenario-summary">
            <h3>Test Scenarios</h3>
            <div class="scenario-stats">
              <div class="stat passed">
                <span class="value">{{ testScenarios.filter(s => s.status === 'passed').length }}</span>
                <span class="label">Passed</span>
              </div>
              <div class="stat failed">
                <span class="value">{{ testScenarios.filter(s => s.status === 'failed').length }}</span>
                <span class="label">Failed</span>
              </div>
              <div class="stat total">
                <span class="value">{{ testScenarios.length }}</span>
                <span class="label">Total</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="trend-section">
          <h3>Safety Score Trend</h3>
          <TrendChart
            :data="evaluationHistory.map(e => ({ date: e.created_at, value: e.results?.overall_score || 0 }))"
            :height="200"
          />
        </div>
      </div>

      <!-- Dimensions Tab -->
      <div v-if="activeTab === 'dimensions'" class="tab-content">
        <div class="dimensions-grid">
          <div v-for="dim in dimensions" :key="dim.key" class="dimension-card">
            <div class="dimension-header">
              <i :class="['icon', dim.icon]" />
              <h3>{{ dim.name }}</h3>
              <ScoreGauge :score="dimensionScores[dim.key] || 0" :size="70" />
            </div>
            <p class="dimension-desc">{{ dim.description }}</p>
            
            <div class="dimension-details" v-if="latestEvaluation?.results?.dimension_details?.[dim.key]">
              <h4>Analysis</h4>
              <div class="detail-metrics">
                <div 
                  v-for="(value, metric) in latestEvaluation.results.dimension_details[dim.key]"
                  :key="metric"
                  class="detail-metric"
                >
                  <span class="metric-label">{{ metric }}</span>
                  <span class="metric-value">{{ typeof value === 'number' ? (value * 100).toFixed(1) + '%' : value }}</span>
                </div>
              </div>
            </div>
            
            <div class="dimension-recommendations" v-if="latestEvaluation?.results?.recommendations?.[dim.key]">
              <h4>Recommendations</h4>
              <ul>
                <li v-for="(rec, idx) in latestEvaluation.results.recommendations[dim.key]" :key="idx">
                  {{ rec }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Scenarios Tab -->
      <div v-if="activeTab === 'scenarios'" class="tab-content">
        <div class="scenarios-header">
          <h2>Test Scenarios</h2>
          <p>Sandboxed tests evaluating agent behavior in controlled environments</p>
        </div>
        
        <div class="scenarios-list">
          <div 
            v-for="scenario in testScenarios" 
            :key="scenario.id"
            :class="['scenario-card', scenario.status]"
          >
            <div class="scenario-status">
              <i :class="['icon', scenario.status === 'passed' ? 'icon-check-circle' : 'icon-x-circle']" />
            </div>
            <div class="scenario-info">
              <h4>{{ scenario.name }}</h4>
              <div class="scenario-meta">
                <span :class="['risk-badge', scenario.risk]">{{ scenario.risk }} risk</span>
                <span class="status-text">{{ scenario.status }}</span>
              </div>
            </div>
            <div class="scenario-actions">
              <button class="btn btn-sm">View Details</button>
              <button class="btn btn-sm">Re-run</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Sandbox Tab -->
      <div v-if="activeTab === 'sandbox'" class="tab-content">
        <div class="sandbox-header">
          <h2>Sandbox Execution Logs</h2>
          <div class="sandbox-controls">
            <button class="btn btn-sm">
              <i class="icon icon-download" />
              Export Logs
            </button>
            <button class="btn btn-sm">
              <i class="icon icon-filter" />
              Filter
            </button>
          </div>
        </div>
        
        <div class="sandbox-logs">
          <div v-if="sandboxLogs.length === 0" class="no-logs">
            <i class="icon icon-terminal" />
            <p>No sandbox logs available</p>
          </div>
          
          <div v-else class="log-entries">
            <div 
              v-for="(log, idx) in sandboxLogs" 
              :key="idx"
              :class="['log-entry', log.level]"
            >
              <span class="log-time">{{ log.timestamp }}</span>
              <span :class="['log-level', log.level]">{{ log.level }}</span>
              <span class="log-message">{{ log.message }}</span>
              <span class="log-source" v-if="log.source">{{ log.source }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tools Tab -->
      <div v-if="activeTab === 'tools'" class="tab-content">
        <div class="tools-header">
          <h2>Tool Usage Analysis</h2>
          <p>Analysis of agent's tool and API usage patterns</p>
        </div>
        
        <div v-if="toolUsageStats" class="tool-stats">
          <div class="stat-cards">
            <div class="stat-card">
              <span class="stat-value">{{ toolUsageStats.total_calls || 0 }}</span>
              <span class="stat-label">Total Tool Calls</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ toolUsageStats.unique_tools || 0 }}</span>
              <span class="stat-label">Unique Tools Used</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ toolUsageStats.blocked_calls || 0 }}</span>
              <span class="stat-label">Blocked Calls</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ toolUsageStats.avg_latency || 0 }}ms</span>
              <span class="stat-label">Avg Latency</span>
            </div>
          </div>
          
          <div class="tool-breakdown">
            <h3>Tool Breakdown</h3>
            <table class="tool-table">
              <thead>
                <tr>
                  <th>Tool</th>
                  <th>Calls</th>
                  <th>Allowed</th>
                  <th>Blocked</th>
                  <th>Risk Level</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="tool in toolUsageStats.tools" :key="tool.name">
                  <td>
                    <i :class="['icon', tool.icon || 'icon-tool']" />
                    {{ tool.name }}
                  </td>
                  <td>{{ tool.calls }}</td>
                  <td class="allowed">{{ tool.allowed }}</td>
                  <td class="blocked">{{ tool.blocked }}</td>
                  <td>
                    <span :class="['risk-badge', tool.risk]">{{ tool.risk }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <div v-else class="no-tools">
          <i class="icon icon-tool" />
          <p>No tool usage data available</p>
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.agentic-model-view {
  padding: 20px;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  
  .model-info {
    h1 { margin: 0 0 5px 0; font-size: 24px; }
    .model-type { color: var(--body-text); margin: 0 0 10px 0; opacity: 0.7; }
  }
  
  .model-actions {
    display: flex;
    gap: 10px;
  }
}

.warning-banner {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid #F59E0B;
  border-radius: var(--border-radius);
  margin-bottom: 20px;
  
  i {
    font-size: 24px;
    color: #F59E0B;
  }
  
  .warning-content {
    strong { display: block; color: #F59E0B; }
    p { margin: 5px 0 0 0; font-size: 14px; color: var(--body-text); }
  }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
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
    
    &:hover { color: var(--link); }
    &.active { color: var(--link); border-bottom-color: var(--link); }
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
  grid-template-columns: 250px 1fr 250px;
  gap: 20px;
  margin-bottom: 30px;
  
  @media (max-width: 1100px) {
    grid-template-columns: 1fr;
  }
}

.score-card, .dimensions-summary, .scenario-summary {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
}

.score-card {
  text-align: center;
  
  h2 { margin: 0 0 20px 0; font-size: 16px; }
  
  .risk-level {
    margin-top: 15px;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    
    &.low { background: #10B981; color: white; }
    &.medium { background: #F59E0B; color: white; }
    &.high { background: #EF4444; color: white; }
    &.critical { background: #7F1D1D; color: white; }
  }
}

.dimensions-summary {
  h3 { margin: 0 0 20px 0; }
  
  .dimension-bar {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    
    .dim-label {
      width: 140px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
    }
    
    .bar-wrapper {
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
        
        &.low { background: #10B981; }
        &.medium { background: #F59E0B; }
        &.high { background: #EF4444; }
        &.critical { background: #7F1D1D; }
      }
    }
    
    .dim-score {
      width: 45px;
      text-align: right;
      font-weight: 600;
    }
  }
}

.scenario-summary {
  h3 { margin: 0 0 20px 0; }
  
  .scenario-stats {
    display: flex;
    justify-content: space-around;
    
    .stat {
      text-align: center;
      
      .value {
        display: block;
        font-size: 28px;
        font-weight: 600;
      }
      
      .label {
        font-size: 12px;
        color: var(--body-text);
        opacity: 0.7;
      }
      
      &.passed .value { color: #10B981; }
      &.failed .value { color: #EF4444; }
    }
  }
}

.dimensions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.dimension-card {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
  
  .dimension-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;
    
    i { font-size: 24px; color: var(--link); }
    h3 { flex: 1; margin: 0; }
  }
  
  .dimension-desc {
    color: var(--body-text);
    opacity: 0.8;
    margin-bottom: 15px;
  }
  
  h4 {
    margin: 15px 0 10px 0;
    font-size: 13px;
    color: var(--link);
  }
  
  .detail-metric {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
    
    .metric-label { text-transform: capitalize; }
    .metric-value { font-weight: 600; }
  }
  
  .dimension-recommendations ul {
    margin: 0;
    padding-left: 20px;
    
    li { padding: 3px 0; }
  }
}

.scenarios-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scenario-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  
  &.passed {
    border-left: 4px solid #10B981;
    .scenario-status i { color: #10B981; }
  }
  
  &.failed {
    border-left: 4px solid #EF4444;
    .scenario-status i { color: #EF4444; }
  }
  
  .scenario-status i {
    font-size: 24px;
  }
  
  .scenario-info {
    flex: 1;
    
    h4 { margin: 0 0 5px 0; }
    
    .scenario-meta {
      display: flex;
      gap: 15px;
      
      .risk-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        
        &.critical { background: #7F1D1D; color: white; }
        &.high { background: #EF4444; color: white; }
        &.medium { background: #F59E0B; color: white; }
        &.low { background: #10B981; color: white; }
      }
      
      .status-text {
        font-size: 12px;
        color: var(--body-text);
        opacity: 0.7;
      }
    }
  }
  
  .scenario-actions {
    display: flex;
    gap: 10px;
  }
}

.sandbox-logs {
  background: #1a1a1a;
  border-radius: var(--border-radius);
  padding: 20px;
  font-family: monospace;
  max-height: 500px;
  overflow-y: auto;
}

.log-entry {
  display: flex;
  gap: 15px;
  padding: 5px 0;
  font-size: 13px;
  border-bottom: 1px solid #333;
  
  .log-time { color: #666; width: 100px; }
  .log-level {
    width: 60px;
    text-transform: uppercase;
    font-weight: 600;
    
    &.info { color: #3B82F6; }
    &.warn { color: #F59E0B; }
    &.error { color: #EF4444; }
    &.debug { color: #6B7280; }
  }
  .log-message { flex: 1; color: #ddd; }
  .log-source { color: #888; }
}

.no-logs, .no-tools {
  text-align: center;
  padding: 60px;
  color: #666;
  
  i { font-size: 48px; }
  p { margin-top: 15px; }
}

.tool-stats {
  .stat-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 30px;
    
    .stat-card {
      background: var(--box-bg);
      border: 1px solid var(--border);
      border-radius: var(--border-radius);
      padding: 20px;
      text-align: center;
      
      .stat-value {
        display: block;
        font-size: 28px;
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
}

.tool-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--box-bg);
  border-radius: var(--border-radius);
  overflow: hidden;
  
  th, td {
    padding: 12px 15px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }
  
  th {
    background: var(--body-bg);
    font-weight: 600;
  }
  
  .allowed { color: #10B981; }
  .blocked { color: #EF4444; }
  
  .risk-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    
    &.critical { background: #7F1D1D; color: white; }
    &.high { background: #EF4444; color: white; }
    &.medium { background: #F59E0B; color: white; }
    &.low { background: #10B981; color: white; }
  }
}
</style>
