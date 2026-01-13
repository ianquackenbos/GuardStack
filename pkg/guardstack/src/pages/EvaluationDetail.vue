<template>
  <div class="evaluation-detail">
    <header class="page-header">
      <div class="breadcrumb">
        <router-link :to="{ name: 'guardstack-evaluations' }">Evaluations</router-link>
        <span>/</span>
        <span>{{ evaluation?.model_id || 'Loading...' }}</span>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" @click="downloadReport('pdf')">Export PDF</button>
        <button class="btn btn-outline" @click="downloadReport('json')">Export JSON</button>
      </div>
    </header>

    <div v-if="evaluation" class="evaluation-content">
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-value">{{ evaluation.overall_score }}%</div>
          <div class="card-label">Overall Score</div>
        </div>
        <div class="summary-card" :class="`risk-${evaluation.risk_level}`">
          <div class="card-value">{{ evaluation.risk_level }}</div>
          <div class="card-label">Risk Level</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ evaluation.pillar_results.length }}</div>
          <div class="card-label">Pillars Evaluated</div>
        </div>
      </div>

      <div class="pillar-results">
        <h2>Pillar Results</h2>
        <div class="pillars-grid">
          <div
            v-for="pillar in evaluation.pillar_results"
            :key="pillar.id"
            class="pillar-card"
            :class="{ 'pillar-passed': pillar.passed, 'pillar-failed': !pillar.passed }"
          >
            <div class="pillar-header">
              <h3>{{ formatPillarName(pillar.pillar_name) }}</h3>
              <span class="pillar-score">{{ pillar.score }}%</span>
            </div>
            <div class="pillar-status">
              {{ pillar.passed ? '✓ Passed' : '✗ Failed' }}
            </div>
            <div class="pillar-findings">
              {{ pillar.findings.length }} finding(s)
            </div>
            <div class="pillar-time">
              Executed in {{ pillar.execution_time_ms }}ms
            </div>
          </div>
        </div>
      </div>

      <div v-if="allFindings.length" class="findings-section">
        <h2>All Findings</h2>
        <div class="findings-list">
          <div
            v-for="finding in allFindings"
            :key="finding.id"
            class="finding-card"
            :class="`severity-${finding.severity}`"
          >
            <div class="finding-header">
              <span class="finding-type">{{ finding.type }}</span>
              <span class="finding-severity">{{ finding.severity }}</span>
            </div>
            <h4>{{ finding.title }}</h4>
            <p>{{ finding.description }}</p>
            <div class="finding-recommendation">
              <strong>Recommendation:</strong> {{ finding.recommendation }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useEvaluationsStore } from '../stores/evaluations';
import type { Finding } from '../types';

const route = useRoute();
const store = useEvaluationsStore();

const evaluation = ref(store.currentEvaluation);

const allFindings = computed<Finding[]>(() => {
  if (!evaluation.value) return [];
  return evaluation.value.pillar_results.flatMap(p => p.findings);
});

async function loadEvaluation() {
  const id = route.params.id as string;
  evaluation.value = await store.fetchEvaluation(id);
}

function formatPillarName(name: string): string {
  return name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
}

function downloadReport(format: 'pdf' | 'json') {
  const id = evaluation.value?.id;
  if (id) {
    window.open(`/api/v1/evaluations/${id}/report?format=${format}`, '_blank');
  }
}

onMounted(() => {
  loadEvaluation();
});
</script>

<style lang="scss" scoped>
.evaluation-detail { padding: 20px; }
.page-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
}
.breadcrumb {
  display: flex;
  gap: 8px;
  color: var(--text-muted);
  a { color: var(--primary); }
}
.header-actions { display: flex; gap: 8px; }

.summary-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}
.summary-card {
  padding: 24px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  text-align: center;
  .card-value { font-size: 36px; font-weight: bold; }
  .card-label { color: var(--text-muted); }
  &.risk-low { border-left: 4px solid #22c55e; }
  &.risk-medium { border-left: 4px solid #f59e0b; }
  &.risk-high { border-left: 4px solid #ef4444; }
  &.risk-critical { border-left: 4px solid #991b1b; }
}

.pillar-results {
  margin-bottom: 24px;
  h2 { margin-bottom: 16px; }
}
.pillars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}
.pillar-card {
  padding: 16px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  border-left: 4px solid;
  &.pillar-passed { border-color: #22c55e; }
  &.pillar-failed { border-color: #ef4444; }
  .pillar-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
  h3 { margin: 0; font-size: 16px; }
  .pillar-score { font-weight: bold; }
  .pillar-status { margin-bottom: 8px; }
  .pillar-findings, .pillar-time { font-size: 12px; color: var(--text-muted); }
}

.findings-section h2 { margin-bottom: 16px; }
.findings-list { display: flex; flex-direction: column; gap: 12px; }
.finding-card {
  padding: 16px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  border-left: 4px solid;
  &.severity-low { border-color: #22c55e; }
  &.severity-medium { border-color: #f59e0b; }
  &.severity-high { border-color: #ef4444; }
  &.severity-critical { border-color: #991b1b; }
  .finding-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
  .finding-type { font-size: 12px; color: var(--text-muted); text-transform: uppercase; }
  .finding-severity {
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 12px;
  }
  h4 { margin: 0 0 8px; }
  p { color: var(--text-muted); margin-bottom: 12px; }
  .finding-recommendation {
    padding: 8px;
    background: var(--bg-muted, #f9fafb);
    border-radius: 4px;
    font-size: 14px;
  }
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  &.btn-outline { background: transparent; border: 1px solid var(--border); }
}
</style>
