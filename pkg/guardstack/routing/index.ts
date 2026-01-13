/**
 * GuardStack Routing Configuration
 * Defines all routes for the Rancher UI Extension
 */
import type { RouteRecordRaw } from 'vue-router';

// Lazy load pages for better performance
const Dashboard = () => import('../pages/dashboard.vue');
const ModelsList = () => import('../pages/models/index.vue');
const ModelDetail = () => import('../pages/models/_id/index.vue');
const ModelPredictive = () => import('../pages/models/_id/predictive.vue');
const ModelGenAI = () => import('../pages/models/_id/genai.vue');
const ModelSPM = () => import('../pages/models/_id/spm.vue');
const ModelAgentic = () => import('../pages/models/_id/agentic.vue');
const EvaluationsList = () => import('../pages/evaluations/index.vue');
const EvaluationDetail = () => import('../pages/evaluations/_id.vue');
const EvaluationCreate = () => import('../pages/evaluations/create.vue');
const ComplianceEuAiAct = () => import('../pages/compliance/eu-ai-act.vue');
const ComplianceReports = () => import('../pages/compliance/reports.vue');
const SettingsConnectors = () => import('../pages/settings/connectors.vue');
const SettingsGuardrails = () => import('../pages/settings/guardrails.vue');

export const routes: RouteRecordRaw[] = [
  {
    path: '/guardstack',
    name: 'guardstack',
    redirect: '/guardstack/dashboard',
    meta: {
      title: 'GuardStack',
      icon: 'shield',
    },
    children: [
      // Dashboard
      {
        path: 'dashboard',
        name: 'guardstack-dashboard',
        component: Dashboard,
        meta: {
          title: 'Dashboard',
          icon: 'dashboard',
        },
      },
      
      // Models
      {
        path: 'models',
        name: 'guardstack-models',
        component: ModelsList,
        meta: {
          title: 'Models',
          icon: 'box',
        },
      },
      {
        path: 'models/:id',
        name: 'guardstack-model-detail',
        component: ModelDetail,
        meta: {
          title: 'Model Details',
          parent: 'guardstack-models',
        },
        props: true,
      },
      {
        path: 'models/:id/predictive',
        name: 'guardstack-model-predictive',
        component: ModelPredictive,
        meta: {
          title: 'Predictive ML Evaluation',
          parent: 'guardstack-model-detail',
        },
        props: true,
      },
      {
        path: 'models/:id/genai',
        name: 'guardstack-model-genai',
        component: ModelGenAI,
        meta: {
          title: 'GenAI Evaluation',
          parent: 'guardstack-model-detail',
        },
        props: true,
      },
      {
        path: 'models/:id/spm',
        name: 'guardstack-model-spm',
        component: ModelSPM,
        meta: {
          title: 'Security Posture',
          parent: 'guardstack-model-detail',
        },
        props: true,
      },
      {
        path: 'models/:id/agentic',
        name: 'guardstack-model-agentic',
        component: ModelAgentic,
        meta: {
          title: 'Agentic AI Evaluation',
          parent: 'guardstack-model-detail',
        },
        props: true,
      },
      
      // Evaluations
      {
        path: 'evaluations',
        name: 'guardstack-evaluations',
        component: EvaluationsList,
        meta: {
          title: 'Evaluations',
          icon: 'check-circle',
        },
      },
      {
        path: 'evaluations/create',
        name: 'guardstack-evaluation-create',
        component: EvaluationCreate,
        meta: {
          title: 'Create Evaluation',
          parent: 'guardstack-evaluations',
        },
      },
      {
        path: 'evaluations/:id',
        name: 'guardstack-evaluation-detail',
        component: EvaluationDetail,
        meta: {
          title: 'Evaluation Details',
          parent: 'guardstack-evaluations',
        },
        props: true,
      },
      
      // Compliance
      {
        path: 'compliance',
        name: 'guardstack-compliance',
        redirect: '/guardstack/compliance/eu-ai-act',
        meta: {
          title: 'Compliance',
          icon: 'clipboard-check',
        },
        children: [
          {
            path: 'eu-ai-act',
            name: 'guardstack-compliance-eu-ai-act',
            component: ComplianceEuAiAct,
            meta: {
              title: 'EU AI Act',
              parent: 'guardstack-compliance',
            },
          },
          {
            path: 'reports',
            name: 'guardstack-compliance-reports',
            component: ComplianceReports,
            meta: {
              title: 'Reports',
              parent: 'guardstack-compliance',
            },
          },
        ],
      },
      
      // Settings
      {
        path: 'settings',
        name: 'guardstack-settings',
        redirect: '/guardstack/settings/connectors',
        meta: {
          title: 'Settings',
          icon: 'cog',
        },
        children: [
          {
            path: 'connectors',
            name: 'guardstack-settings-connectors',
            component: SettingsConnectors,
            meta: {
              title: 'Connectors',
              parent: 'guardstack-settings',
            },
          },
          {
            path: 'guardrails',
            name: 'guardstack-settings-guardrails',
            component: SettingsGuardrails,
            meta: {
              title: 'Guardrails',
              parent: 'guardstack-settings',
            },
          },
        ],
      },
    ],
  },
];

// Navigation items for sidebar
export const navigation = [
  {
    name: 'dashboard',
    label: 'Dashboard',
    icon: 'dashboard',
    route: { name: 'guardstack-dashboard' },
  },
  {
    name: 'models',
    label: 'Models',
    icon: 'box',
    route: { name: 'guardstack-models' },
  },
  {
    name: 'evaluations',
    label: 'Evaluations',
    icon: 'check-circle',
    route: { name: 'guardstack-evaluations' },
  },
  {
    name: 'compliance',
    label: 'Compliance',
    icon: 'clipboard-check',
    children: [
      {
        name: 'eu-ai-act',
        label: 'EU AI Act',
        route: { name: 'guardstack-compliance-eu-ai-act' },
      },
      {
        name: 'reports',
        label: 'Reports',
        route: { name: 'guardstack-compliance-reports' },
      },
    ],
  },
  {
    name: 'settings',
    label: 'Settings',
    icon: 'cog',
    children: [
      {
        name: 'connectors',
        label: 'Connectors',
        route: { name: 'guardstack-settings-connectors' },
      },
      {
        name: 'guardrails',
        label: 'Guardrails',
        route: { name: 'guardstack-settings-guardrails' },
      },
    ],
  },
];

export default routes;
