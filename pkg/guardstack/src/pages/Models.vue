<template>
  <div class="guardstack-models">
    <header class="page-header">
      <h1>AI Models</h1>
      <div class="header-actions">
        <button class="btn btn-primary" @click="showRegisterModal = true">
          <i class="icon icon-plus" />
          Register Model
        </button>
      </div>
    </header>

    <!-- Filters -->
    <div class="filters">
      <div class="filter-group">
        <label>Type</label>
        <select v-model="filters.model_type" @change="applyFilters">
          <option value="">All Types</option>
          <option value="predictive">Predictive AI</option>
          <option value="genai">Generative AI</option>
          <option value="agentic">Agentic AI</option>
        </select>
      </div>
      <div class="filter-group">
        <label>Search</label>
        <input
          v-model="filters.search"
          type="text"
          placeholder="Search models..."
          @input="debounceSearch"
        />
      </div>
    </div>

    <!-- Models Grid -->
    <div v-if="isLoading" class="loading">
      <i class="icon icon-spinner icon-spin" />
      Loading models...
    </div>

    <div v-else-if="models.length" class="models-grid">
      <div
        v-for="model in models"
        :key="model.id"
        class="model-card"
        @click="viewModel(model.id)"
      >
        <div class="model-header">
          <span class="model-type" :class="`type-${model.model_type}`">
            {{ model.model_type }}
          </span>
          <span class="model-framework">{{ model.framework }}</span>
        </div>
        <h3 class="model-name">{{ model.name }}</h3>
        <p class="model-description">{{ model.description || 'No description' }}</p>
        <div class="model-meta">
          <span class="model-version">v{{ model.version }}</span>
          <span class="model-date">{{ formatDate(model.created_at) }}</span>
        </div>
        <div class="model-tags">
          <span v-for="tag in model.tags.slice(0, 3)" :key="tag" class="tag">
            {{ tag }}
          </span>
          <span v-if="model.tags.length > 3" class="tag tag-more">
            +{{ model.tags.length - 3 }}
          </span>
        </div>
        <div class="model-actions">
          <button class="btn btn-sm btn-outline" @click.stop="evaluateModel(model)">
            Evaluate
          </button>
          <button class="btn btn-sm btn-outline" @click.stop="editModel(model)">
            Edit
          </button>
          <button class="btn btn-sm btn-danger-outline" @click.stop="confirmDelete(model)">
            Delete
          </button>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <i class="icon icon-cube" />
      <h3>No models registered</h3>
      <p>Register your first AI model to start evaluations.</p>
      <button class="btn btn-primary" @click="showRegisterModal = true">
        Register Model
      </button>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        class="btn btn-sm"
        :disabled="page === 1"
        @click="goToPage(page - 1)"
      >
        Previous
      </button>
      <span class="page-info">Page {{ page }} of {{ totalPages }}</span>
      <button
        class="btn btn-sm"
        :disabled="page === totalPages"
        @click="goToPage(page + 1)"
      >
        Next
      </button>
    </div>

    <!-- Register Modal -->
    <div v-if="showRegisterModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingModel ? 'Edit Model' : 'Register Model' }}</h2>
          <button class="btn btn-icon" @click="closeModals">
            <i class="icon icon-x" />
          </button>
        </div>
        <form class="modal-body" @submit.prevent="submitModel">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="modelForm.name" type="text" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="modelForm.description" rows="3" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Type *</label>
              <select v-model="modelForm.model_type" required>
                <option value="predictive">Predictive AI</option>
                <option value="genai">Generative AI</option>
                <option value="agentic">Agentic AI</option>
              </select>
            </div>
            <div class="form-group">
              <label>Framework *</label>
              <select v-model="modelForm.framework" required>
                <option value="sklearn">scikit-learn</option>
                <option value="pytorch">PyTorch</option>
                <option value="tensorflow">TensorFlow</option>
                <option value="huggingface">Hugging Face</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="ollama">Ollama</option>
                <option value="custom">Custom</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Version *</label>
              <input v-model="modelForm.version" type="text" required placeholder="1.0.0" />
            </div>
            <div class="form-group">
              <label>Artifact URI</label>
              <input v-model="modelForm.artifact_uri" type="text" placeholder="s3://..." />
            </div>
          </div>
          <div class="form-group">
            <label>Tags</label>
            <input
              v-model="tagsInput"
              type="text"
              placeholder="Enter tags separated by commas"
            />
          </div>
          <div class="form-actions">
            <button type="button" class="btn btn-outline" @click="closeModals">
              Cancel
            </button>
            <button type="submit" class="btn btn-primary" :disabled="isLoading">
              {{ editingModel ? 'Update' : 'Register' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h2>Delete Model</h2>
        </div>
        <div class="modal-body">
          <p>
            Are you sure you want to delete <strong>{{ deletingModel?.name }}</strong>?
            This action cannot be undone.
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="closeModals">Cancel</button>
          <button class="btn btn-danger" @click="deleteModel">Delete</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useModelsStore } from '../stores/models';
import type { RegisteredModel, ModelType, ModelFramework } from '../types';

const router = useRouter();
const store = useModelsStore();

const models = computed(() => store.models);
const isLoading = computed(() => store.isLoading);
const page = computed(() => store.page);
const totalPages = computed(() => store.totalPages);

// Modals
const showRegisterModal = ref(false);
const showDeleteModal = ref(false);
const editingModel = ref<RegisteredModel | null>(null);
const deletingModel = ref<RegisteredModel | null>(null);

// Filters
const filters = reactive({
  model_type: '' as ModelType | '',
  search: '',
});

// Form
const modelForm = reactive({
  name: '',
  description: '',
  model_type: 'predictive' as ModelType,
  framework: 'sklearn' as ModelFramework,
  version: '1.0.0',
  artifact_uri: '',
});
const tagsInput = ref('');

let searchTimeout: number | null = null;

function debounceSearch() {
  if (searchTimeout) clearTimeout(searchTimeout);
  searchTimeout = window.setTimeout(() => {
    applyFilters();
  }, 300);
}

function applyFilters() {
  store.fetchModels({
    model_type: filters.model_type || undefined,
    search: filters.search || undefined,
  });
}

function goToPage(newPage: number) {
  store.setPage(newPage);
  store.fetchModels(filters);
}

function viewModel(id: string) {
  router.push({ name: 'guardstack-model-detail', params: { id } });
}

function editModel(model: RegisteredModel) {
  editingModel.value = model;
  modelForm.name = model.name;
  modelForm.description = model.description;
  modelForm.model_type = model.model_type;
  modelForm.framework = model.framework;
  modelForm.version = model.version;
  modelForm.artifact_uri = model.artifact_uri;
  tagsInput.value = model.tags.join(', ');
  showRegisterModal.value = true;
}

function evaluateModel(model: RegisteredModel) {
  router.push({
    name: 'guardstack-evaluations',
    query: { model_id: model.id, action: 'new' },
  });
}

function confirmDelete(model: RegisteredModel) {
  deletingModel.value = model;
  showDeleteModal.value = true;
}

async function deleteModel() {
  if (!deletingModel.value) return;
  await store.deleteModel(deletingModel.value.id);
  closeModals();
}

async function submitModel() {
  const tags = tagsInput.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t);

  const data = {
    ...modelForm,
    tags,
  };

  if (editingModel.value) {
    await store.updateModel(editingModel.value.id, data);
  } else {
    await store.registerModel(data);
  }

  closeModals();
}

function closeModals() {
  showRegisterModal.value = false;
  showDeleteModal.value = false;
  editingModel.value = null;
  deletingModel.value = null;
  resetForm();
}

function resetForm() {
  modelForm.name = '';
  modelForm.description = '';
  modelForm.model_type = 'predictive';
  modelForm.framework = 'sklearn';
  modelForm.version = '1.0.0';
  modelForm.artifact_uri = '';
  tagsInput.value = '';
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

onMounted(() => {
  store.fetchModels();
});
</script>

<style lang="scss" scoped>
.guardstack-models {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;

  label {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-muted);
  }

  select, input {
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
    min-width: 200px;
  }
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.model-card {
  padding: 20px;
  background: var(--card-bg, #fff);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }

  .model-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .model-type {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;

    &.type-predictive { background: #dbeafe; color: #1d4ed8; }
    &.type-genai { background: #dcfce7; color: #166534; }
    &.type-agentic { background: #fef3c7; color: #92400e; }
  }

  .model-framework {
    font-size: 12px;
    color: var(--text-muted);
  }

  .model-name {
    margin: 0 0 8px;
    font-size: 18px;
  }

  .model-description {
    color: var(--text-muted);
    font-size: 14px;
    margin-bottom: 12px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .model-meta {
    display: flex;
    gap: 16px;
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 12px;
  }

  .model-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
  }

  .tag {
    padding: 2px 8px;
    background: var(--bg-muted, #f3f4f6);
    border-radius: 4px;
    font-size: 12px;

    &.tag-more {
      color: var(--text-muted);
    }
  }

  .model-actions {
    display: flex;
    gap: 8px;
    border-top: 1px solid var(--border);
    padding-top: 16px;
  }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: var(--card-bg, #fff);
  border-radius: 8px;

  .icon {
    font-size: 48px;
    color: var(--text-muted);
    margin-bottom: 16px;
  }

  h3 {
    margin: 0 0 8px;
  }

  p {
    color: var(--text-muted);
    margin-bottom: 20px;
  }
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;

  .page-info {
    color: var(--text-muted);
  }
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 60px;
  color: var(--text-muted);
}

// Modal styles
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
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
  max-width: 600px;
  max-height: 90vh;
  overflow: auto;

  &.modal-sm {
    max-width: 400px;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid var(--border);

    h2 {
      margin: 0;
    }
  }

  .modal-body {
    padding: 20px;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 20px;
    border-top: 1px solid var(--border);
  }
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

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

// Button styles
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;

  &.btn-sm {
    padding: 6px 12px;
    font-size: 13px;
  }

  &.btn-primary {
    background: var(--primary);
    color: #fff;
  }

  &.btn-outline {
    background: transparent;
    border: 1px solid var(--border);
  }

  &.btn-danger {
    background: #ef4444;
    color: #fff;
  }

  &.btn-danger-outline {
    background: transparent;
    border: 1px solid #ef4444;
    color: #ef4444;
  }

  &.btn-icon {
    padding: 8px;
    background: transparent;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.icon-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
