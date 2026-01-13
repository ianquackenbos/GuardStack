<template>
  <div class="model-detail">
    <header class="page-header">
      <div class="breadcrumb">
        <router-link :to="{ name: 'guardstack-models' }">Models</router-link>
        <span>/</span>
        <span>{{ model?.name || 'Loading...' }}</span>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="startEvaluation">Run Evaluation</button>
      </div>
    </header>

    <div v-if="model" class="model-content">
      <div class="model-info">
        <h1>{{ model.name }}</h1>
        <p>{{ model.description }}</p>
        <div class="model-badges">
          <span class="badge" :class="`badge-${model.model_type}`">{{ model.model_type }}</span>
          <span class="badge">{{ model.framework }}</span>
          <span class="badge">v{{ model.version }}</span>
        </div>
      </div>

      <div class="model-evaluations">
        <h2>Evaluation History</h2>
        <div class="evaluations-list">
          <div v-for="evaluation in evaluations" :key="evaluation.id" class="evaluation-item">
            <span class="status" :class="`status-${evaluation.status}`">{{ evaluation.status }}</span>
            <span>Score: {{ evaluation.overall_score }}%</span>
            <span>{{ formatDate(evaluation.started_at) }}</span>
          </div>
          <div v-if="!evaluations.length" class="no-data">No evaluations yet</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useModelsStore } from '../stores/models';
import type { Evaluation } from '../types';

const route = useRoute();
const router = useRouter();
const modelsStore = useModelsStore();

const model = ref(modelsStore.currentModel);
const evaluations = ref<Evaluation[]>([]);

async function loadModel() {
  const id = route.params.id as string;
  model.value = await modelsStore.fetchModel(id);
}

function startEvaluation() {
  router.push({
    name: 'guardstack-evaluations',
    query: { model_id: model.value?.id, action: 'new' }
  });
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString();
}

onMounted(() => {
  loadModel();
});
</script>

<style lang="scss" scoped>
.model-detail { padding: 20px; }
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
.model-info {
  margin-bottom: 24px;
  h1 { margin: 0 0 8px; }
}
.model-badges {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.badge {
  padding: 4px 8px;
  background: var(--bg-muted);
  border-radius: 4px;
  font-size: 12px;
  &.badge-predictive { background: #dbeafe; color: #1d4ed8; }
  &.badge-genai { background: #dcfce7; color: #166534; }
  &.badge-agentic { background: #fef3c7; color: #92400e; }
}
.model-evaluations {
  background: var(--card-bg, #fff);
  border-radius: 8px;
  padding: 20px;
  h2 { margin: 0 0 16px; font-size: 18px; }
}
.evaluations-list { display: flex; flex-direction: column; gap: 8px; }
.evaluation-item {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: var(--bg-muted, #f9fafb);
  border-radius: 4px;
}
.status {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  &.status-completed { background: #dcfce7; color: #166534; }
  &.status-failed { background: #fee2e2; color: #991b1b; }
}
.no-data { color: var(--text-muted); text-align: center; padding: 20px; }
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  &.btn-primary { background: var(--primary); color: #fff; }
}
</style>
