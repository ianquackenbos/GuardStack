/**
 * GuardStack Models Store
 * Pinia state management for model data
 */
import { defineStore } from 'pinia';
import type {
  Model,
  ModelType,
  RiskLevel,
  PaginatedResponse,
  PillarScore,
} from '../types';

interface ModelsState {
  models: Model[];
  currentModel: Model | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  filters: {
    type: ModelType | null;
    riskLevel: RiskLevel | null;
    search: string;
    tags: string[];
  };
}

export const useModelsStore = defineStore('models', {
  state: (): ModelsState => ({
    models: [],
    currentModel: null,
    loading: false,
    error: null,
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0,
    },
    filters: {
      type: null,
      riskLevel: null,
      search: '',
      tags: [],
    },
  }),

  getters: {
    filteredModels(state): Model[] {
      let result = [...state.models];

      if (state.filters.type) {
        result = result.filter((m) => m.type === state.filters.type);
      }

      if (state.filters.riskLevel) {
        result = result.filter((m) => m.riskLevel === state.filters.riskLevel);
      }

      if (state.filters.search) {
        const search = state.filters.search.toLowerCase();
        result = result.filter(
          (m) =>
            m.name.toLowerCase().includes(search) ||
            m.description?.toLowerCase().includes(search)
        );
      }

      if (state.filters.tags.length > 0) {
        result = result.filter((m) =>
          state.filters.tags.some((tag) => m.tags.includes(tag))
        );
      }

      return result;
    },

    modelsByType(state): Record<ModelType, Model[]> {
      return state.models.reduce(
        (acc, model) => {
          if (!acc[model.type]) {
            acc[model.type] = [];
          }
          acc[model.type].push(model);
          return acc;
        },
        {} as Record<ModelType, Model[]>
      );
    },

    modelsByRisk(state): Record<RiskLevel, Model[]> {
      return state.models.reduce(
        (acc, model) => {
          const risk = model.riskLevel || RiskLevel.MINIMAL;
          if (!acc[risk]) {
            acc[risk] = [];
          }
          acc[risk].push(model);
          return acc;
        },
        {} as Record<RiskLevel, Model[]>
      );
    },

    riskDistribution(state): Record<RiskLevel, number> {
      const distribution: Record<RiskLevel, number> = {
        [RiskLevel.CRITICAL]: 0,
        [RiskLevel.HIGH]: 0,
        [RiskLevel.MEDIUM]: 0,
        [RiskLevel.LOW]: 0,
        [RiskLevel.MINIMAL]: 0,
      };

      state.models.forEach((model) => {
        const risk = model.riskLevel || RiskLevel.MINIMAL;
        distribution[risk]++;
      });

      return distribution;
    },

    hasModels(state): boolean {
      return state.models.length > 0;
    },

    totalModels(state): number {
      return state.pagination.total;
    },
  },

  actions: {
    async fetchModels(page = 1, pageSize = 20) {
      this.loading = true;
      this.error = null;

      try {
        const params = new URLSearchParams({
          page: page.toString(),
          page_size: pageSize.toString(),
        });

        if (this.filters.type) {
          params.append('type', this.filters.type);
        }
        if (this.filters.riskLevel) {
          params.append('risk_level', this.filters.riskLevel);
        }
        if (this.filters.search) {
          params.append('search', this.filters.search);
        }

        const response = await fetch(`/api/v1/models?${params}`);
        if (!response.ok) throw new Error('Failed to fetch models');

        const data: PaginatedResponse<Model> = await response.json();

        this.models = data.items;
        this.pagination = {
          page: data.page,
          pageSize: data.pageSize,
          total: data.total,
        };
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        console.error('Failed to fetch models:', error);
      } finally {
        this.loading = false;
      }
    },

    async fetchModel(id: string) {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch(`/api/v1/models/${id}`);
        if (!response.ok) throw new Error('Failed to fetch model');

        this.currentModel = await response.json();
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        console.error('Failed to fetch model:', error);
      } finally {
        this.loading = false;
      }
    },

    async createModel(model: Partial<Model>) {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch('/api/v1/models', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(model),
        });

        if (!response.ok) throw new Error('Failed to create model');

        const newModel: Model = await response.json();
        this.models.unshift(newModel);
        return newModel;
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async updateModel(id: string, updates: Partial<Model>) {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch(`/api/v1/models/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        });

        if (!response.ok) throw new Error('Failed to update model');

        const updated: Model = await response.json();

        const index = this.models.findIndex((m) => m.id === id);
        if (index !== -1) {
          this.models[index] = updated;
        }

        if (this.currentModel?.id === id) {
          this.currentModel = updated;
        }

        return updated;
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async deleteModel(id: string) {
      this.loading = true;
      this.error = null;

      try {
        const response = await fetch(`/api/v1/models/${id}`, {
          method: 'DELETE',
        });

        if (!response.ok) throw new Error('Failed to delete model');

        this.models = this.models.filter((m) => m.id !== id);

        if (this.currentModel?.id === id) {
          this.currentModel = null;
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Unknown error';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    setFilters(filters: Partial<ModelsState['filters']>) {
      this.filters = { ...this.filters, ...filters };
    },

    clearFilters() {
      this.filters = {
        type: null,
        riskLevel: null,
        search: '',
        tags: [],
      };
    },

    clearCurrentModel() {
      this.currentModel = null;
    },
  },
});
