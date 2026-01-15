/**
 * Dashboard E2E Tests
 * Tests for the main dashboard functionality
 */
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/dashboard/overview', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          totalModels: 12,
          totalEvaluations: 45,
          averageScore: 78,
          riskDistribution: {
            critical: 2,
            high: 3,
            medium: 4,
            low: 2,
            minimal: 1,
          },
        }),
      });
    });

    await page.route('**/api/v1/models*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'model-1',
              name: 'GPT-4',
              type: 'llm',
              riskLevel: 'low',
              scores: { overall: 85 },
            },
            {
              id: 'model-2',
              name: 'Claude 3',
              type: 'llm',
              riskLevel: 'minimal',
              scores: { overall: 92 },
            },
          ],
          page: 1,
          pageSize: 20,
          total: 2,
        }),
      });
    });

    await page.goto('/');
  });

  test('displays dashboard overview', async ({ page }) => {
    await expect(page.getByText('Dashboard')).toBeVisible();
    await expect(page.getByText('12')).toBeVisible(); // total models
    await expect(page.getByText('45')).toBeVisible(); // total evaluations
  });

  test('shows risk distribution chart', async ({ page }) => {
    await expect(page.locator('[data-testid="risk-distribution"]')).toBeVisible();
  });

  test('displays model cards', async ({ page }) => {
    await expect(page.getByText('GPT-4')).toBeVisible();
    await expect(page.getByText('Claude 3')).toBeVisible();
  });

  test('navigates to model details on click', async ({ page }) => {
    await page.getByText('GPT-4').click();
    await expect(page).toHaveURL(/\/models\/model-1/);
  });

  test('filters models by risk level', async ({ page }) => {
    await page.getByRole('combobox', { name: /risk level/i }).click();
    await page.getByRole('option', { name: /critical/i }).click();
    
    // Wait for filter to apply
    await page.waitForResponse('**/api/v1/models*');
  });

  test('searches models by name', async ({ page }) => {
    await page.getByPlaceholder(/search/i).fill('gpt');
    await page.keyboard.press('Enter');
    
    // Wait for search to apply
    await page.waitForResponse('**/api/v1/models*');
  });
});
