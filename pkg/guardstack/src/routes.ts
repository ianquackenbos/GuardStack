/**
 * GuardStack Routes
 */

import type { RouteRecordRaw } from 'vue-router';

export const routes: RouteRecordRaw[] = [
  {
    path: '/guardstack',
    name: 'guardstack',
    redirect: '/guardstack/dashboard',
    meta: {
      title: 'GuardStack',
      icon: 'shield-check',
    },
    children: [
      {
        path: 'dashboard',
        name: 'guardstack-dashboard',
        component: () => import('./pages/Dashboard.vue'),
        meta: {
          title: 'Dashboard',
          icon: 'home',
        },
      },
      {
        path: 'models',
        name: 'guardstack-models',
        component: () => import('./pages/Models.vue'),
        meta: {
          title: 'Models',
          icon: 'cube',
        },
      },
      {
        path: 'models/:id',
        name: 'guardstack-model-detail',
        component: () => import('./pages/ModelDetail.vue'),
        meta: {
          title: 'Model Details',
          icon: 'cube',
        },
        props: true,
      },
      {
        path: 'evaluations',
        name: 'guardstack-evaluations',
        component: () => import('./pages/Evaluations.vue'),
        meta: {
          title: 'Evaluations',
          icon: 'clipboard-check',
        },
      },
      {
        path: 'evaluations/:id',
        name: 'guardstack-evaluation-detail',
        component: () => import('./pages/EvaluationDetail.vue'),
        meta: {
          title: 'Evaluation Details',
          icon: 'clipboard-check',
        },
        props: true,
      },
      {
        path: 'compliance',
        name: 'guardstack-compliance',
        component: () => import('./pages/Compliance.vue'),
        meta: {
          title: 'Compliance',
          icon: 'shield',
        },
      },
      {
        path: 'guardrails',
        name: 'guardstack-guardrails',
        component: () => import('./pages/Guardrails.vue'),
        meta: {
          title: 'Guardrails',
          icon: 'ban',
        },
      },
      {
        path: 'connectors',
        name: 'guardstack-connectors',
        component: () => import('./pages/Connectors.vue'),
        meta: {
          title: 'Connectors',
          icon: 'plug',
        },
      },
      {
        path: 'settings',
        name: 'guardstack-settings',
        component: () => import('./pages/Settings.vue'),
        meta: {
          title: 'Settings',
          icon: 'cog',
        },
      },
    ],
  },
];

export default routes;
