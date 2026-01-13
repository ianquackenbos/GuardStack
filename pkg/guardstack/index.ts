/**
 * GuardStack - Rancher UI Extension
 * AI Safety & Governance Platform
 * 
 * Main entry point for the Rancher UI Extension
 */
import type { IPlugin } from '@shell/core/types';
import { routes, navigation } from './routing';

// Import stores
import { useModelsStore } from './store/models';
import { useEvaluationsStore } from './store/evaluations';
import { useDashboardStore } from './store/dashboard';

// Export types
export * from './types';

// Export components
export * from './components';

// Export stores
export { useModelsStore, useEvaluationsStore, useDashboardStore };

// Extension definition
const extension: IPlugin = {
  name: 'guardstack',
  displayName: 'GuardStack',
  description: 'AI Safety & Governance Platform',
  icon: 'shield',
  version: '1.0.0',
  
  routes,
  
  // Navigation configuration
  nav: navigation,
  
  // Product registration
  product: {
    name: 'guardstack',
    label: 'GuardStack',
    icon: 'shield',
    weight: 100,
    to: { name: 'guardstack-dashboard' },
  },
  
  // Localization
  l10n: {
    'en-us': () => import('./l10n/en-us.yaml'),
  },
  
  // Hooks
  onBeforeCreate(store: any) {
    // Register Pinia stores if needed
    console.log('GuardStack: Extension loading...');
  },
  
  onAfterCreate() {
    console.log('GuardStack: Extension loaded successfully');
  },
};

export default extension;
