<template>
  <div class="guardstack-evaluations">
    <header class="page-header">
      <h1>Evaluations</h1>
      <button class="btn btn-primary" @click="showNewEvaluation = true">
        <i class="icon icon-plus" />
        New Evaluation
      </button>
    </header>

    <!-- Running Evaluations -->
    <div v-if="runningEvaluations.length" class="running-evaluations">
      <h2>Running Evaluations</h2>
      <div class="running-list">
        <div
          v-for="evaluation in runningEvaluations"
          :key="evaluation.id"
          class="running-card"
        >
          <div class="running-info">
            <span class="model-id">{{ evaluation.model_id }}</span>
            <span class="status status-running">{{ evaluation.status }}</span>
          </div>
          <div class="progress-bar">
            <div class="progress" :style="{ width: '50%' }" />
          </div>
          <button class="btn btn-sm btn-outline" @click="cancelEvaluation(evaluation.id)">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Evaluations Table -->
    <div class="evaluations-table">
      <table class="table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Type</th>
            <th>Status</th>
            <th>Score</th>
            <th>Risk Level</th>
            <th>Started</th>
            <th>Duration</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="evaluation in evaluations"
            :key="evaluation.id"
            @click="viewEvaluation(evaluation.id)"
          >
            <td>{{ evaluation.model_id }}</td>
            <td>
              <span class="badge" :class="`badge-${evaluation.evaluation_type}`">
                {{ evaluation.evaluation_type }}
              </span>
            </td>
            <td>
              <span class="status" :class="`status-${evaluation.status}`">
                {{ evaluation.status }}
              </span>
            </td>
            <td>{{ evaluation.overall_score }}%</td>
            <td>
              <span class="risk-badge" :class="`risk-${evaluation.risk_level}`">
                {{ evaluation.risk_level }}
              </span>
            </td>
            <td>{{ formatDate(evaluation.started_at) }}</td>
            <td>{{ getDuration(evaluation) }}</td>
            <td>
              <div class="actions" @click.stop>
                <button class="btn btn-sm btn-outline" @click="viewReport(evaluation.id)">
                  Report
                </button>
                <button
                  class="btn btn-sm btn-danger-outline"
                  @click="confirmDelete(evaluation)"
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button class="btn btn-sm" :disabled="page === 1" @click="goToPage(page - 1)">
        Previous
      </button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button class="btn btn-sm" :disabled="page === totalPages" @click="goToPage(page + 1)">
        Next
      </button>
    </div>

    <!-- New Evaluation Modal -->
    <div v-if="showNewEvaluation" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h2>New Evaluation</h2>
          <button class="btn btn-icon" @click="closeModal">×</button>
        </div>
        <form class="modal-body" @submit.prevent="startEvaluation">
          <div class="form-group">
            <label>Model *</label>
            <select v-model="evalForm.modelId" required>
              <option value="">Select a model</option>
              <option v-for="model in availableModels" :key="model.id" :value="model.id">
                {{ model.name }} ({{ model.model_type }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Pillars</label>
            <div class="pillar-checkboxes">
              <label v-for="pillar in availablePillars" :key="pillar">
                <input
                  v-model="evalForm.pillars"
                  type="checkbox"
                  :value="pillar"
                />
                {{ pillar }}
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>Dataset URI (optional)</label>
            <input v-model="evalForm.datasetUri" type="text" placeholder="s3://..." />
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeModal">
              Cancel
            </button>
            <button type="submit" class="btn btn-primary">Start Evaluation</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useEvaluationsStore } from '../stores/evaluations';
import { useModelsStore } from '../stores/models';
import type { Evaluation } from '../types';

const router = useRouter();
const store = useEvaluationsStore();
const modelsStore = useModelsStore();

const evaluations = computed(() => store.evaluations);
const runningEvaluations = computed(() => store.runningEvaluations);
const page = computed(() => store.page);
const totalPages = computed(() => store.totalPages);
const availableModels = computed(() => modelsStore.models);

const showNewEvaluation = ref(false);

const evalForm = reactive({
  modelId: '',
  pillars: [] as string[],
  datasetUri: '',
});

const availablePillars = [
  'privacy', 'toxicity', 'fairness', 'security',
  'explain', 'actions', 'robustness', 'trace', 'testing', 'imitation',
];

function viewEvaluation(id: string) {
  router.push({ name: 'guardstack-evaluation-detail', params: { id } });
}

function viewReport(id: string) {
  window.open(`/api/v1/evaluations/${id}/report?format=html`, '_blank');
}

async function startEvaluation() {
  await store.startEvaluation(evalForm.modelId, {
    pillars: evalForm.pillars.length ? evalForm.pillars : ['all'],
    thresholds: {},
    dataset_uri: evalForm.datasetUri || undefined,
  });
  closeModal();
}

async function cancelEvaluation(id: string) {
  await store.cancelEvaluation(id);
}

function confirmDelete(evaluation: Evaluation) {
  if (confirm(`Delete evaluation for ${evaluation.model_id}?`)) {
    store.deleteEvaluation(evaluation.id);
  }
}

function goToPage(newPage: number) {
  store.setPage(newPage);
  store.fetchEvaluations();
}

function closeModal() {
  showNewEvaluation.value = false;
  evalForm.modelId = '';
  evalForm.pillars = [];
  evalForm.datasetUri = '';
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getDuration(evaluation: Evaluation): string {
  const start = new Date(evaluation.started_at);
  const end = evaluation.completed_at ? new Date(evaluation.completed_at) : new Date();
  const ms = end.getTime() - start.getTime();
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}

onMounted(() => {
  store.fetchEvaluations();
  modelsStore.fetchModels();
});

onUnmounted(() => {
  store.stopPolling();
});
</script>

<style lang="scss" scoped>
.guardstack-evaluations {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.running-evaluations {
  margin-bottom: 24px;

  h2 {
    font-size: 16px;
    margin-bottom: 12px;
  }
}

.running-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.running-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  border-left: 4px solid #3b82f6;

  .running-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .progress-bar {
    flex: 2;
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;

    .progress {
      height: 100%;
      background: #3b82f6;
      transition: width 0.3s;
    }
  }
}

.table {
  width: 100%;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  overflow: hidden;

  th, td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }

  th {
    background: var(--header-bg, #f9fafb);
    font-weight: 600;
  }

  tbody tr {
    cursor: pointer;

    &:hover {
      background: var(--hover-bg, #f9fafb);
    }
  }
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-transform: uppercase;

  &.badge-predictive { background: #dbeafe; color: #1d4ed8; }
  &.badge-genai { background: #dcfce7; color: #166534; }
  &.badge-agentic { background: #fef3c7; color: #92400e; }
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;

  &.status-pending { background: #fef3c7; color: #92400e; }
  &.status-running { background: #dbeafe; color: #1d4ed8; }
  &.status-completed { background: #dcfce7; color: #166534; }
  &.status-failed { background: #fee2e2; color: #991b1b; }
  &.status-cancelled { background: #e5e7eb; color: #374151; }
}

.risk-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  text-transform: uppercase;

  &.risk-low { background: #dcfce7; color: #166534; }
  &.risk-medium { background: #fef3c7; color: #92400e; }
  &.risk-high { background: #fee2e2; color: #991b1b; }
  &.risk-critical { background: #991b1b; color: #fff; }
}

.actions {
  display: flex;
  gap: 8px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--card-bg, #fff);
  border-radius: 8px;
  width: 100%;
  max-width: 500px;

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--border);

    h2 { margin: 0; }
  }

  .modal-body {
    padding: 20px;
  }
}

.form-group {
  margin-bottom: 16px;

  label {
    display: block;
    margin-bottom: 4px;
    font-weight: 500;
  }

  input, select {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
  }
}

.pillar-checkboxes {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;

  label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: normal;
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;

  &.btn-sm { padding: 6px 12px; }
  &.btn-primary { background: var(--primary); color: #fff; }
  &.btn-outline { background: transparent; border: 1px solid var(--border); }
  &.btn-danger-outline { background: transparent; border: 1px solid #ef4444; color: #ef4444; }
  &.btn-icon { padding: 8px; background: transparent; font-size: 20px; }
}
</style>
