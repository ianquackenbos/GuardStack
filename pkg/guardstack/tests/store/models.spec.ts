/**
 * Models Store Tests
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useModelsStore } from '../../store/models';
import { mockFetch, createMockModel } from '../setup';

describe('useModelsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('initial state', () => {
    it('has empty models array', () => {
      const store = useModelsStore();
      expect(store.models).toEqual([]);
    });

    it('has null currentModel', () => {
      const store = useModelsStore();
      expect(store.currentModel).toBeNull();
    });

    it('has loading false', () => {
      const store = useModelsStore();
      expect(store.loading).toBe(false);
    });

    it('has null error', () => {
      const store = useModelsStore();
      expect(store.error).toBeNull();
    });

    it('has default pagination', () => {
      const store = useModelsStore();
      expect(store.pagination).toEqual({
        page: 1,
        pageSize: 20,
        total: 0,
      });
    });

    it('has empty filters', () => {
      const store = useModelsStore();
      expect(store.filters).toEqual({
        type: null,
        riskLevel: null,
        search: '',
        tags: [],
      });
    });
  });

  describe('getters', () => {
    it('filteredModels returns all models when no filters', () => {
      const store = useModelsStore();
      const model1 = createMockModel({ id: '1', name: 'Model 1' });
      const model2 = createMockModel({ id: '2', name: 'Model 2' });
      store.models = [model1, model2];

      expect(store.filteredModels).toHaveLength(2);
    });

    it('filteredModels filters by type', () => {
      const store = useModelsStore();
      store.models = [
        createMockModel({ id: '1', type: 'llm' }),
        createMockModel({ id: '2', type: 'embedding' }),
      ];
      store.filters.type = 'llm';

      expect(store.filteredModels).toHaveLength(1);
      expect(store.filteredModels[0].type).toBe('llm');
    });

    it('filteredModels filters by riskLevel', () => {
      const store = useModelsStore();
      store.models = [
        createMockModel({ id: '1', riskLevel: 'low' }),
        createMockModel({ id: '2', riskLevel: 'high' }),
      ];
      store.filters.riskLevel = 'high';

      expect(store.filteredModels).toHaveLength(1);
      expect(store.filteredModels[0].riskLevel).toBe('high');
    });

    it('filteredModels filters by search term', () => {
      const store = useModelsStore();
      store.models = [
        createMockModel({ id: '1', name: 'GPT-4' }),
        createMockModel({ id: '2', name: 'Claude' }),
      ];
      store.filters.search = 'gpt';

      expect(store.filteredModels).toHaveLength(1);
      expect(store.filteredModels[0].name).toBe('GPT-4');
    });

    it('filteredModels filters by tags', () => {
      const store = useModelsStore();
      store.models = [
        createMockModel({ id: '1', tags: ['production'] }),
        createMockModel({ id: '2', tags: ['development'] }),
      ];
      store.filters.tags = ['production'];

      expect(store.filteredModels).toHaveLength(1);
      expect(store.filteredModels[0].tags).toContain('production');
    });

    it('hasModels returns true when models exist', () => {
      const store = useModelsStore();
      store.models = [createMockModel()];

      expect(store.hasModels).toBe(true);
    });

    it('hasModels returns false when no models', () => {
      const store = useModelsStore();
      expect(store.hasModels).toBe(false);
    });

    it('totalModels returns pagination total', () => {
      const store = useModelsStore();
      store.pagination.total = 100;

      expect(store.totalModels).toBe(100);
    });
  });

  describe('actions', () => {
    it('fetchModels updates models on success', async () => {
      const store = useModelsStore();
      const mockData = {
        items: [createMockModel()],
        page: 1,
        pageSize: 20,
        total: 1,
      };

      mockFetch(mockData);

      await store.fetchModels();

      expect(store.models).toHaveLength(1);
      expect(store.pagination.total).toBe(1);
      expect(store.loading).toBe(false);
      expect(store.error).toBeNull();
    });

    it('fetchModels sets error on failure', async () => {
      const store = useModelsStore();

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await store.fetchModels();

      expect(store.error).not.toBeNull();
      expect(store.loading).toBe(false);
    });

    it('fetchModel sets currentModel on success', async () => {
      const store = useModelsStore();
      const mockModel = createMockModel({ id: 'test-id' });

      mockFetch(mockModel);

      await store.fetchModel('test-id');

      expect(store.currentModel).toEqual(mockModel);
      expect(store.loading).toBe(false);
    });

    it('createModel adds model to list', async () => {
      const store = useModelsStore();
      const newModel = createMockModel({ id: 'new-id', name: 'New Model' });

      mockFetch(newModel);

      const result = await store.createModel({ name: 'New Model' });

      expect(result).toEqual(newModel);
      expect(store.models).toContainEqual(newModel);
    });

    it('updateModel updates model in list', async () => {
      const store = useModelsStore();
      const existingModel = createMockModel({ id: 'test-id', name: 'Old Name' });
      store.models = [existingModel];

      const updatedModel = { ...existingModel, name: 'New Name' };
      mockFetch(updatedModel);

      await store.updateModel('test-id', { name: 'New Name' });

      expect(store.models[0].name).toBe('New Name');
    });

    it('updateModel updates currentModel if same id', async () => {
      const store = useModelsStore();
      const existingModel = createMockModel({ id: 'test-id' });
      store.models = [existingModel];
      store.currentModel = existingModel;

      const updatedModel = { ...existingModel, name: 'Updated' };
      mockFetch(updatedModel);

      await store.updateModel('test-id', { name: 'Updated' });

      expect(store.currentModel?.name).toBe('Updated');
    });

    it('deleteModel removes model from list', async () => {
      const store = useModelsStore();
      store.models = [
        createMockModel({ id: '1' }),
        createMockModel({ id: '2' }),
      ];

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
      });

      await store.deleteModel('1');

      expect(store.models).toHaveLength(1);
      expect(store.models[0].id).toBe('2');
    });

    it('deleteModel clears currentModel if same id', async () => {
      const store = useModelsStore();
      const model = createMockModel({ id: 'test-id' });
      store.models = [model];
      store.currentModel = model;

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
      });

      await store.deleteModel('test-id');

      expect(store.currentModel).toBeNull();
    });

    it('setFilters updates filter values', () => {
      const store = useModelsStore();

      store.setFilters({ search: 'test', type: 'llm' });

      expect(store.filters.search).toBe('test');
      expect(store.filters.type).toBe('llm');
    });

    it('clearFilters resets all filters', () => {
      const store = useModelsStore();
      store.filters = {
        type: 'llm',
        riskLevel: 'high',
        search: 'test',
        tags: ['tag1'],
      };

      store.clearFilters();

      expect(store.filters).toEqual({
        type: null,
        riskLevel: null,
        search: '',
        tags: [],
      });
    });

    it('clearCurrentModel sets currentModel to null', () => {
      const store = useModelsStore();
      store.currentModel = createMockModel();

      store.clearCurrentModel();

      expect(store.currentModel).toBeNull();
    });
  });
});
