<template>
  <div class="guardstack-connectors">
    <header class="page-header">
      <h1>LLM Connectors</h1>
    </header>

    <div class="connectors-grid">
      <div v-for="connector in connectors" :key="connector.id" class="connector-card">
        <div class="connector-icon">
          <img :src="getIcon(connector.type)" :alt="connector.name" />
        </div>
        <h3>{{ connector.name }}</h3>
        <span class="connector-status" :class="`status-${connector.status}`">
          {{ connector.status }}
        </span>
        <div class="connector-actions">
          <button class="btn btn-sm btn-outline" @click="testConnector(connector.id)">
            Test
          </button>
          <button class="btn btn-sm btn-outline" @click="configureConnector(connector)">
            Configure
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from '../api';

interface Connector {
  id: string;
  name: string;
  type: string;
  status: string;
}

const connectors = ref<Connector[]>([
  { id: 'openai', name: 'OpenAI', type: 'openai', status: 'connected' },
  { id: 'anthropic', name: 'Anthropic', type: 'anthropic', status: 'connected' },
  { id: 'ollama', name: 'Ollama', type: 'ollama', status: 'disconnected' },
  { id: 'huggingface', name: 'Hugging Face', type: 'huggingface', status: 'disconnected' },
]);

function getIcon(type: string): string {
  const icons: Record<string, string> = {
    openai: '/icons/openai.svg',
    anthropic: '/icons/anthropic.svg',
    ollama: '/icons/ollama.svg',
    huggingface: '/icons/huggingface.svg',
  };
  return icons[type] || '/icons/default.svg';
}

async function testConnector(id: string) {
  try {
    const result = await api.connectors.test(id);
    if (result.data.success) {
      alert(`Connection successful! Latency: ${result.data.latency_ms}ms`);
    } else {
      alert('Connection failed');
    }
  } catch (e) {
    alert('Connection test failed');
  }
}

function configureConnector(connector: Connector) {
  // Open configuration modal
}

async function loadConnectors() {
  try {
    const response = await api.connectors.list();
    connectors.value = response.data as Connector[];
  } catch (e) {
    console.error('Failed to load connectors:', e);
  }
}

onMounted(() => {
  loadConnectors();
});
</script>

<style lang="scss" scoped>
.guardstack-connectors { padding: 20px; }
.page-header { margin-bottom: 24px; }

.connectors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.connector-card {
  padding: 24px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  text-align: center;

  .connector-icon {
    width: 64px;
    height: 64px;
    margin: 0 auto 16px;
    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  h3 { margin: 0 0 8px; }

  .connector-status {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    margin-bottom: 16px;
    &.status-connected { background: #dcfce7; color: #166534; }
    &.status-disconnected { background: #fee2e2; color: #991b1b; }
  }

  .connector-actions {
    display: flex;
    justify-content: center;
    gap: 8px;
  }
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  &.btn-sm { padding: 6px 12px; }
  &.btn-outline { background: transparent; border: 1px solid var(--border); }
}
</style>
