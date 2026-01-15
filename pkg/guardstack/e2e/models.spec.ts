/**
 * Model Management E2E Tests
 * Tests for model CRUD operations
 */
import { test, expect } from '@playwright/test';

test.describe('Model Management', () => {
  const mockModel = {
    id: 'model-1',
    name: 'Test Model',
    description: 'A test model for E2E testing',
    type: 'llm',
    provider: 'openai',
    version: '1.0',
    riskLevel: 'low',
    tags: ['test', 'demo'],
    scores: {
      overall: 85,
      security: 90,
      fairness: 80,
      privacy: 85,
      robustness: 85,
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/models*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [mockModel],
            page: 1,
            pageSize: 20,
            total: 1,
          }),
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            ...mockModel,
            id: 'new-model-id',
          }),
        });
      }
    });

    await page.route('**/api/v1/models/model-1', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockModel),
        });
      } else if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 204 });
      } else if (route.request().method() === 'PATCH') {
        const body = await route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...mockModel, ...body }),
        });
      }
    });
  });

  test('displays model list', async ({ page }) => {
    await page.goto('/models');
    
    await expect(page.getByText('Test Model')).toBeVisible();
    await expect(page.getByText('openai')).toBeVisible();
  });

  test('navigates to model details', async ({ page }) => {
    await page.goto('/models');
    await page.getByText('Test Model').click();
    
    await expect(page).toHaveURL(/\/models\/model-1/);
    await expect(page.getByText('Test Model')).toBeVisible();
    await expect(page.getByText('A test model for E2E testing')).toBeVisible();
  });

  test('displays model scores', async ({ page }) => {
    await page.goto('/models/model-1');
    
    await expect(page.getByText('85')).toBeVisible(); // overall score
    await expect(page.getByText(/security/i)).toBeVisible();
    await expect(page.getByText(/fairness/i)).toBeVisible();
  });

  test('opens create model dialog', async ({ page }) => {
    await page.goto('/models');
    await page.getByRole('button', { name: /add model|create|new/i }).click();
    
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByLabel(/name/i)).toBeVisible();
  });

  test('creates new model', async ({ page }) => {
    await page.goto('/models');
    await page.getByRole('button', { name: /add model|create|new/i }).click();
    
    await page.getByLabel(/name/i).fill('New Model');
    await page.getByLabel(/description/i).fill('New model description');
    await page.getByLabel(/provider/i).fill('anthropic');
    
    await page.getByRole('button', { name: /save|create|submit/i }).click();
    
    // Should show success message or redirect
    await expect(page.getByText(/created|success/i)).toBeVisible();
  });

  test('edits existing model', async ({ page }) => {
    await page.goto('/models/model-1');
    await page.getByRole('button', { name: /edit/i }).click();
    
    await page.getByLabel(/name/i).clear();
    await page.getByLabel(/name/i).fill('Updated Model');
    
    await page.getByRole('button', { name: /save|update/i }).click();
    
    await expect(page.getByText(/updated|success/i)).toBeVisible();
  });

  test('deletes model with confirmation', async ({ page }) => {
    await page.goto('/models/model-1');
    await page.getByRole('button', { name: /delete/i }).click();
    
    // Confirm deletion
    await expect(page.getByText(/are you sure|confirm/i)).toBeVisible();
    await page.getByRole('button', { name: /confirm|yes|delete/i }).click();
    
    // Should redirect to models list
    await expect(page).toHaveURL('/models');
  });

  test('filters models by type', async ({ page }) => {
    await page.goto('/models');
    await page.getByRole('combobox', { name: /type/i }).click();
    await page.getByRole('option', { name: /llm/i }).click();
    
    await page.waitForResponse('**/api/v1/models*');
  });

  test('sorts models', async ({ page }) => {
    await page.goto('/models');
    await page.getByRole('button', { name: /sort/i }).click();
    await page.getByRole('option', { name: /score|risk/i }).click();
    
    await page.waitForResponse('**/api/v1/models*');
  });
});
