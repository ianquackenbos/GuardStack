<script lang="ts" setup>
/**
 * PillarScoreCard Component
 * Displays individual pillar score with details
 */
import { computed } from 'vue';
import type { RiskLevel } from '../types';

const props = defineProps<{
  pillar: string;
  score: number;
  riskLevel?: RiskLevel;
  confidence?: number;
  trend?: 'up' | 'down' | 'stable';
  previousScore?: number;
  recommendations?: string[];
  expandable?: boolean;
}>();

const emit = defineEmits<{
  (e: 'expand', pillar: string): void;
}>();

// Pillar info mapping
const pillarInfo: Record<string, { label: string; icon: string; description: string }> = {
  explain: {
    label: 'Explainability',
    icon: '🔍',
    description: 'Model interpretability using SHAP/LIME',
  },
  actions: {
    label: 'Adversarial',
    icon: '⚔️',
    description: 'Resistance to adversarial attacks',
  },
  fairness: {
    label: 'Fairness',
    icon: '⚖️',
    description: 'Bias detection across demographics',
  },
  robustness: {
    label: 'Robustness',
    icon: '🛡️',
    description: 'Stability under perturbations',
  },
  trace: {
    label: 'Data Lineage',
    icon: '📊',
    description: 'Train/test data similarity',
  },
  testing: {
    label: 'Testing',
    icon: '✅',
    description: 'Performance metrics & QoS',
  },
  imitation: {
    label: 'IP Protection',
    icon: '🔒',
    description: 'Model extraction defense',
  },
  privacy: {
    label: 'Privacy',
    icon: '🔐',
    description: 'PII & membership inference risks',
  },
  toxicity: {
    label: 'Toxicity',
    icon: '⚠️',
    description: 'Harmful content detection',
  },
  security: {
    label: 'Security',
    icon: '🛡️',
    description: 'Prompt injection & jailbreak',
  },
};

const info = computed(() => {
  const key = props.pillar.toLowerCase();
  return pillarInfo[key] || {
    label: props.pillar,
    icon: '📈',
    description: 'Evaluation metric',
  };
});

const scoreColor = computed(() => {
  if (props.score >= 80) return 'text-green-600 dark:text-green-400';
  if (props.score >= 60) return 'text-yellow-600 dark:text-yellow-400';
  if (props.score >= 40) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
});

const bgColor = computed(() => {
  if (props.score >= 80) return 'bg-green-50 dark:bg-green-900/20';
  if (props.score >= 60) return 'bg-yellow-50 dark:bg-yellow-900/20';
  if (props.score >= 40) return 'bg-orange-50 dark:bg-orange-900/20';
  return 'bg-red-50 dark:bg-red-900/20';
});

const progressColor = computed(() => {
  if (props.score >= 80) return 'bg-green-500';
  if (props.score >= 60) return 'bg-yellow-500';
  if (props.score >= 40) return 'bg-orange-500';
  return 'bg-red-500';
});

const trendIcon = computed(() => {
  if (props.trend === 'up') return '↑';
  if (props.trend === 'down') return '↓';
  return '→';
});

const trendColor = computed(() => {
  if (props.trend === 'up') return 'text-green-500';
  if (props.trend === 'down') return 'text-red-500';
  return 'text-gray-400';
});

const scoreDiff = computed(() => {
  if (props.previousScore === undefined) return null;
  return props.score - props.previousScore;
});
</script>

<template>
  <div
    :class="[
      'rounded-lg border p-4 transition-all',
      bgColor,
      expandable ? 'cursor-pointer hover:shadow-md' : '',
    ]"
    @click="expandable && emit('expand', pillar)"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <span class="text-2xl">{{ info.icon }}</span>
        <div>
          <h4 class="font-semibold text-gray-900 dark:text-gray-100">
            {{ info.label }}
          </h4>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            {{ info.description }}
          </p>
        </div>
      </div>
      
      <!-- Score -->
      <div class="text-right">
        <div :class="['text-2xl font-bold', scoreColor]">
          {{ Math.round(score) }}
        </div>
        <div v-if="trend" :class="['text-sm', trendColor]">
          {{ trendIcon }}
          <span v-if="scoreDiff !== null" class="ml-1">
            {{ scoreDiff > 0 ? '+' : '' }}{{ Math.round(scoreDiff) }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- Progress bar -->
    <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden mb-3">
      <div
        :class="['h-full rounded-full transition-all duration-500', progressColor]"
        :style="{ width: `${score}%` }"
      ></div>
    </div>
    
    <!-- Metadata -->
    <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
      <span v-if="confidence !== undefined">
        Confidence: {{ Math.round(confidence * 100) }}%
      </span>
      <span v-if="riskLevel" class="capitalize">
        {{ riskLevel }} Risk
      </span>
    </div>
    
    <!-- Recommendations preview -->
    <div v-if="recommendations && recommendations.length > 0" class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">
        {{ recommendations.length }} recommendation{{ recommendations.length > 1 ? 's' : '' }}
      </p>
      <p class="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
        {{ recommendations[0] }}
      </p>
    </div>
  </div>
</template>
