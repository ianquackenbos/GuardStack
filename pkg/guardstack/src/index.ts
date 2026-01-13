/**
 * GuardStack Rancher UI Extension
 * 
 * Main entry point for the extension.
 */

import type { App } from 'vue';
import type { Router } from 'vue-router';
import { createPinia } from 'pinia';

// Import routes
import { routes } from './routes';

// Import components
import Dashboard from './pages/Dashboard.vue';
import Models from './pages/Models.vue';
import Evaluations from './pages/Evaluations.vue';
import Compliance from './pages/Compliance.vue';
import Guardrails from './pages/Guardrails.vue';
import Settings from './pages/Settings.vue';

// Import stores
import { useGuardStackStore } from './stores/guardstack';
import { useModelsStore } from './stores/models';
import { useEvaluationsStore } from './stores/evaluations';

// Extension metadata
export const metadata = {
  name: 'guardstack',
  displayName: 'GuardStack',
  description: 'AI Safety & Security Platform',
  version: '0.1.0',
  icon: 'shield-check',
  category: 'ai',
};

// Extension routes for Rancher
export const extensionRoutes = routes;

// Install function for Vue
export function install(app: App, options: { router?: Router } = {}) {
  // Create and use Pinia store
  const pinia = createPinia();
  app.use(pinia);

  // Register global components
  app.component('GuardStackDashboard', Dashboard);
  app.component('GuardStackModels', Models);
  app.component('GuardStackEvaluations', Evaluations);
  app.component('GuardStackCompliance', Compliance);
  app.component('GuardStackGuardrails', Guardrails);
  app.component('GuardStackSettings', Settings);

  // Add routes if router provided
  if (options.router) {
    routes.forEach((route) => {
      options.router!.addRoute(route);
    });
  }
}

// Export components
export {
  Dashboard,
  Models,
  Evaluations,
  Compliance,
  Guardrails,
  Settings,
};

// Export stores
export {
  useGuardStackStore,
  useModelsStore,
  useEvaluationsStore,
};

// Export types
export * from './types';

// Default export
export default {
  install,
  metadata,
  routes,
};
