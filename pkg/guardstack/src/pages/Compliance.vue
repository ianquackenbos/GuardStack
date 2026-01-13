<template>
  <div class="guardstack-compliance">
    <header class="page-header">
      <h1>Compliance</h1>
    </header>

    <div class="compliance-overview">
      <div class="score-card">
        <div class="score-value">{{ overallScore }}%</div>
        <div class="score-label">Overall Compliance Score</div>
      </div>
    </div>

    <div class="frameworks-grid">
      <div v-for="framework in frameworks" :key="framework.id" class="framework-card">
        <h3>{{ framework.name }}</h3>
        <p>{{ framework.description }}</p>
        <div class="framework-version">Version {{ framework.version }}</div>
        <button class="btn btn-outline" @click="viewFramework(framework.id)">
          View Details
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { api } from '../api';

interface Framework {
  id: string;
  name: string;
  version: string;
  description: string;
}

const frameworks = ref<Framework[]>([]);
const overallScore = ref(85);

async function loadFrameworks() {
  try {
    const response = await api.compliance.listFrameworks();
    frameworks.value = response.data as Framework[];
  } catch (e) {
    console.error('Failed to load frameworks:', e);
  }
}

function viewFramework(id: string) {
  // Navigate to framework detail
}

onMounted(() => {
  loadFrameworks();
});
</script>

<style lang="scss" scoped>
.guardstack-compliance {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.compliance-overview {
  margin-bottom: 24px;
}

.score-card {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 48px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  border-left: 4px solid #22c55e;

  .score-value {
    font-size: 48px;
    font-weight: bold;
    color: #22c55e;
  }

  .score-label {
    color: var(--text-muted);
  }
}

.frameworks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.framework-card {
  padding: 20px;
  background: var(--card-bg, #fff);
  border-radius: 8px;

  h3 {
    margin: 0 0 8px;
  }

  p {
    color: var(--text-muted);
    margin-bottom: 12px;
  }

  .framework-version {
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 16px;
  }
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;

  &.btn-outline {
    background: transparent;
    border: 1px solid var(--border);
  }
}
</style>
