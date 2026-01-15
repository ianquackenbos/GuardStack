/**
 * Evaluation Flow E2E Tests
 * Tests for creating and monitoring evaluations
 */
import { test, expect } from '@playwright/test';

test.describe('Evaluation Flow', () => {
  const mockModel = {
    id: 'model-1',
    name: 'Test Model',
    type: 'llm',
    provider: 'openai',
  };

  const mockEvaluation = {
    id: 'eval-1',
    modelId: 'model-1',
    name: 'Security Evaluation',
    status: 'pending',
    pillars: ['security', 'fairness'],
    createdAt: new Date().toISOString(),
  };

  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/models*', async (route) => {
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
    });

    await page.route('**/api/v1/evaluations', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [mockEvaluation],
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
            ...mockEvaluation,
            id: 'new-eval-id',
          }),
        });
      }
    });

    await page.route('**/api/v1/evaluations/eval-1', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockEvaluation,
          status: 'completed',
          scores: {
            overall: 85,
            security: 90,
            fairness: 80,
          },
        }),
      });
    });

    await page.route('**/api/v1/evaluations/eval-1/start', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockEvaluation,
          status: 'running',
        }),
      });
    });

    await page.route('**/api/v1/evaluations/eval-1/results', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { pillar: 'security', score: 90, findings: [] },
          { pillar: 'fairness', score: 80, findings: [] },
        ]),
      });
    });
  });

  test('displays evaluations list', async ({ page }) => {
    await page.goto('/evaluations');
    
    await expect(page.getByText('Security Evaluation')).toBeVisible();
    await expect(page.getByText(/pending/i)).toBeVisible();
  });

  test('creates new evaluation', async ({ page }) => {
    await page.goto('/evaluations');
    await page.getByRole('button', { name: /new|create|add/i }).click();
    
    // Fill form
    await page.getByLabel(/name/i).fill('New Evaluation');
    await page.getByRole('combobox', { name: /model/i }).click();
    await page.getByRole('option', { name: /test model/i }).click();
    
    // Select pillars
    await page.getByLabel(/security/i).check();
    await page.getByLabel(/fairness/i).check();
    
    await page.getByRole('button', { name: /create|save|submit/i }).click();
    
    await expect(page.getByText(/created|success/i)).toBeVisible();
  });

  test('starts evaluation', async ({ page }) => {
    await page.goto('/evaluations/eval-1');
    await page.getByRole('button', { name: /start|run/i }).click();
    
    await expect(page.getByText(/running|started/i)).toBeVisible();
  });

  test('displays evaluation results', async ({ page }) => {
    await page.goto('/evaluations/eval-1');
    
    // Wait for results to load
    await expect(page.getByText('90')).toBeVisible(); // security score
    await expect(page.getByText('80')).toBeVisible(); // fairness score
  });

  test('shows pillar breakdown', async ({ page }) => {
    await page.goto('/evaluations/eval-1');
    
    await expect(page.getByText(/security/i)).toBeVisible();
    await expect(page.getByText(/fairness/i)).toBeVisible();
  });

  test('navigates to model from evaluation', async ({ page }) => {
    await page.goto('/evaluations/eval-1');
    await page.getByRole('link', { name: /test model/i }).click();
    
    await expect(page).toHaveURL(/\/models\/model-1/);
  });

  test('exports evaluation results', async ({ page }) => {
    await page.goto('/evaluations/eval-1');
    
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /export|download/i }).click();
    
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/evaluation.*\.(json|csv|pdf)/);
  });

  test('filters evaluations by status', async ({ page }) => {
    await page.goto('/evaluations');
    await page.getByRole('combobox', { name: /status/i }).click();
    await page.getByRole('option', { name: /completed/i }).click();
    
    await page.waitForResponse('**/api/v1/evaluations*');
  });

  test('filters evaluations by model', async ({ page }) => {
    await page.goto('/evaluations');
    await page.getByRole('combobox', { name: /model/i }).click();
    await page.getByRole('option', { name: /test model/i }).click();
    
    await page.waitForResponse('**/api/v1/evaluations*');
  });
});
