/**
 * Models Store
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { RegisteredModel, ModelType, PaginationParams, FilterParams } from '../types';
import { api } from '../api';

export const useModelsStore = defineStore('models', () => {
  // State
  const models = ref<RegisteredModel[]>([]);
  const currentModel = ref<RegisteredModel | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const total = ref(0);
  const page = ref(1);
  const perPage = ref(20);

  // Getters
  const isLoading = computed(() => loading.value);
  const hasError = computed(() => error.value !== null);
  
  const modelsByType = computed(() => {
    const grouped: Record<ModelType, RegisteredModel[]> = {
      predictive: [],
      genai: [],
      agentic: [],
    };
    models.value.forEach(model => {
      grouped[model.model_type].push(model);
    });
    return grouped;
  });

  const totalPages = computed(() => Math.ceil(total.value / perPage.value));

  // Actions
  async function fetchModels(filters?: FilterParams, pagination?: PaginationParams) {
    loading.value = true;
    error.value = null;
    
    try {
      const params = {
        page: pagination?.page ?? page.value,
        per_page: pagination?.per_page ?? perPage.value,
        ...filters,
      };
      
      const response = await api.models.list(params);
      models.value = response.data;
      
      if (response.meta) {
        total.value = response.meta.total;
        page.value = response.meta.page;
        perPage.value = response.meta.per_page;
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch models';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function fetchModel(id: string) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await api.models.get(id);
      currentModel.value = response.data;
      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch model';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function registerModel(data: Partial<RegisteredModel>) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await api.models.register(data);
      models.value.push(response.data);
      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to register model';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function updateModel(id: string, data: Partial<RegisteredModel>) {
    loading.value = true;
    error.value = null;
    
    try {
      const response = await api.models.update(id, data);
      const index = models.value.findIndex(m => m.id === id);
      if (index >= 0) {
        models.value[index] = response.data;
      }
      if (currentModel.value?.id === id) {
        currentModel.value = response.data;
      }
      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update model';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function deleteModel(id: string) {
    loading.value = true;
    error.value = null;
    
    try {
      await api.models.delete(id);
      models.value = models.value.filter(m => m.id !== id);
      if (currentModel.value?.id === id) {
        currentModel.value = null;
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete model';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  function clearError() {
    error.value = null;
  }

  function setPage(newPage: number) {
    page.value = newPage;
  }

  return {
    // State
    models,
    currentModel,
    loading,
    error,
    total,
    page,
    perPage,
    // Getters
    isLoading,
    hasError,
    modelsByType,
    totalPages,
    // Actions
    fetchModels,
    fetchModel,
    registerModel,
    updateModel,
    deleteModel,
    clearError,
    setPage,
  };
});
