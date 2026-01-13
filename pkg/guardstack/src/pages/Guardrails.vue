<template>
  <div class="guardstack-guardrails">
    <header class="page-header">
      <h1>Guardrails</h1>
      <button class="btn btn-primary" @click="showCreateModal = true">
        <i class="icon icon-plus" />
        Create Guardrail
      </button>
    </header>

    <div class="guardrails-list">
      <div v-for="guardrail in guardrails" :key="guardrail.id" class="guardrail-card">
        <div class="guardrail-header">
          <h3>{{ guardrail.name }}</h3>
          <label class="toggle">
            <input
              type="checkbox"
              :checked="guardrail.enabled"
              @change="toggleGuardrail(guardrail)"
            />
            <span class="slider" />
          </label>
        </div>
        <p>{{ guardrail.description }}</p>
        <span class="guardrail-type">{{ guardrail.type }}</span>
        <div class="guardrail-actions">
          <button class="btn btn-sm btn-outline" @click="editGuardrail(guardrail)">
            Edit
          </button>
          <button class="btn btn-sm btn-danger-outline" @click="deleteGuardrail(guardrail.id)">
            Delete
          </button>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h2>Create Guardrail</h2>
          <button class="btn btn-icon" @click="closeModal">×</button>
        </div>
        <form class="modal-body" @submit.prevent="createGuardrail">
          <div class="form-group">
            <label>Name</label>
            <input v-model="form.name" type="text" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="form.description" rows="3" />
          </div>
          <div class="form-group">
            <label>Type</label>
            <select v-model="form.type" required>
              <option value="input_validation">Input Validation</option>
              <option value="output_filtering">Output Filtering</option>
              <option value="rate_limiting">Rate Limiting</option>
              <option value="content_moderation">Content Moderation</option>
              <option value="pii_redaction">PII Redaction</option>
              <option value="prompt_injection_detection">Prompt Injection Detection</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeModal">Cancel</button>
            <button type="submit" class="btn btn-primary">Create</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { api } from '../api';
import type { Guardrail, GuardrailType } from '../types';

const guardrails = ref<Guardrail[]>([]);
const showCreateModal = ref(false);

const form = reactive({
  name: '',
  description: '',
  type: 'input_validation' as GuardrailType,
});

async function loadGuardrails() {
  try {
    const response = await api.guardrails.list();
    guardrails.value = response.data;
  } catch (e) {
    console.error('Failed to load guardrails:', e);
  }
}

async function createGuardrail() {
  try {
    const response = await api.guardrails.create({
      name: form.name,
      description: form.description,
      type: form.type,
      enabled: true,
      config: { rules: [], thresholds: {}, actions: [] },
    });
    guardrails.value.push(response.data);
    closeModal();
  } catch (e) {
    console.error('Failed to create guardrail:', e);
  }
}

async function toggleGuardrail(guardrail: Guardrail) {
  try {
    await api.guardrails.toggle(guardrail.id, !guardrail.enabled);
    guardrail.enabled = !guardrail.enabled;
  } catch (e) {
    console.error('Failed to toggle guardrail:', e);
  }
}

function editGuardrail(guardrail: Guardrail) {
  // Open edit modal
}

async function deleteGuardrail(id: string) {
  if (!confirm('Delete this guardrail?')) return;
  try {
    await api.guardrails.delete(id);
    guardrails.value = guardrails.value.filter(g => g.id !== id);
  } catch (e) {
    console.error('Failed to delete guardrail:', e);
  }
}

function closeModal() {
  showCreateModal.value = false;
  form.name = '';
  form.description = '';
  form.type = 'input_validation';
}

onMounted(() => {
  loadGuardrails();
});
</script>

<style lang="scss" scoped>
.guardstack-guardrails {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.guardrails-list {
  display: grid;
  gap: 16px;
}

.guardrail-card {
  padding: 20px;
  background: var(--card-bg, #fff);
  border-radius: 8px;

  .guardrail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    h3 { margin: 0; }
  }

  p {
    color: var(--text-muted);
    margin-bottom: 8px;
  }

  .guardrail-type {
    display: inline-block;
    padding: 4px 8px;
    background: var(--bg-muted, #f3f4f6);
    border-radius: 4px;
    font-size: 12px;
    margin-bottom: 16px;
  }

  .guardrail-actions {
    display: flex;
    gap: 8px;
  }
}

.toggle {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;

  input {
    opacity: 0;
    width: 0;
    height: 0;

    &:checked + .slider {
      background: #22c55e;

      &::before {
        transform: translateX(24px);
      }
    }
  }

  .slider {
    position: absolute;
    inset: 0;
    background: #e5e7eb;
    border-radius: 12px;
    cursor: pointer;
    transition: background 0.3s;

    &::before {
      content: '';
      position: absolute;
      width: 20px;
      height: 20px;
      left: 2px;
      top: 2px;
      background: #fff;
      border-radius: 50%;
      transition: transform 0.3s;
    }
  }
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

  .modal-body { padding: 20px; }
}

.form-group {
  margin-bottom: 16px;

  label {
    display: block;
    margin-bottom: 4px;
    font-weight: 500;
  }

  input, select, textarea {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
  }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
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
