/**
 * Settings E2E Tests
 * Tests for configuration management
 */
import { test, expect } from '@playwright/test';

test.describe('Settings', () => {
  test.beforeEach(async ({ page }) => {
    // Mock connectors API
    await page.route('**/api/v1/connectors*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'conn-1',
                name: 'OpenAI Production',
                type: 'openai',
                status: 'connected',
                createdAt: new Date().toISOString(),
              },
            ],
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
            id: 'new-conn',
            name: 'New Connector',
            type: 'anthropic',
            status: 'connected',
          }),
        });
      }
    });

    // Mock guardrails API
    await page.route('**/api/v1/guardrails*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'rail-1',
                name: 'Content Filter',
                type: 'content_filter',
                enabled: true,
                config: { threshold: 0.8 },
              },
            ],
            page: 1,
            pageSize: 20,
            total: 1,
          }),
        });
      }
    });

    // Mock policies API
    await page.route('**/api/v1/policies*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'policy-1',
              name: 'EU AI Act Compliance',
              framework: 'eu_ai_act',
              enabled: true,
            },
          ],
          page: 1,
          pageSize: 20,
          total: 1,
        }),
      });
    });
  });

  test.describe('Connectors', () => {
    test('displays connector list', async ({ page }) => {
      await page.goto('/settings/connectors');
      
      await expect(page.getByText('OpenAI Production')).toBeVisible();
      await expect(page.getByText(/connected/i)).toBeVisible();
    });

    test('creates new connector', async ({ page }) => {
      await page.goto('/settings/connectors');
      await page.getByRole('button', { name: /add|new|create/i }).click();
      
      await page.getByLabel(/name/i).fill('Anthropic API');
      await page.getByRole('combobox', { name: /type/i }).click();
      await page.getByRole('option', { name: /anthropic/i }).click();
      await page.getByLabel(/api key/i).fill('sk-test-key');
      
      await page.getByRole('button', { name: /save|create/i }).click();
      
      await expect(page.getByText(/created|success/i)).toBeVisible();
    });

    test('tests connector connection', async ({ page }) => {
      await page.route('**/api/v1/connectors/conn-1/test', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, latency_ms: 150 }),
        });
      });

      await page.goto('/settings/connectors');
      await page.getByRole('button', { name: /test/i }).click();
      
      await expect(page.getByText(/success|connected/i)).toBeVisible();
    });
  });

  test.describe('Guardrails', () => {
    test('displays guardrails list', async ({ page }) => {
      await page.goto('/settings/guardrails');
      
      await expect(page.getByText('Content Filter')).toBeVisible();
    });

    test('toggles guardrail enabled state', async ({ page }) => {
      await page.route('**/api/v1/guardrails/rail-1', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'rail-1',
            name: 'Content Filter',
            type: 'content_filter',
            enabled: false,
          }),
        });
      });

      await page.goto('/settings/guardrails');
      await page.getByRole('switch').click();
      
      await page.waitForResponse('**/api/v1/guardrails/rail-1');
    });

    test('configures guardrail settings', async ({ page }) => {
      await page.goto('/settings/guardrails');
      await page.getByText('Content Filter').click();
      
      await page.getByLabel(/threshold/i).clear();
      await page.getByLabel(/threshold/i).fill('0.9');
      
      await page.getByRole('button', { name: /save/i }).click();
      
      await expect(page.getByText(/saved|updated/i)).toBeVisible();
    });
  });

  test.describe('Policies', () => {
    test('displays policies list', async ({ page }) => {
      await page.goto('/settings/policies');
      
      await expect(page.getByText('EU AI Act Compliance')).toBeVisible();
    });

    test('enables compliance policy', async ({ page }) => {
      await page.goto('/settings/policies');
      await page.getByRole('switch').click();
      
      await page.waitForResponse('**/api/v1/policies*');
    });

    test('views policy details', async ({ page }) => {
      await page.goto('/settings/policies');
      await page.getByText('EU AI Act Compliance').click();
      
      await expect(page.getByText(/eu ai act/i)).toBeVisible();
    });
  });
});
