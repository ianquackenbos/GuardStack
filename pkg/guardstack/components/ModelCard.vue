<script lang="ts" setup>
/**
 * ModelCard Component
 * Displays model summary in a card format
 */
import { computed } from 'vue';
import type { Model, RiskLevel } from '../types';

const props = defineProps<{
  model: Model;
  showActions?: boolean;
  compact?: boolean;
}>();

const emit = defineEmits<{
  (e: 'view', model: Model): void;
  (e: 'evaluate', model: Model): void;
  (e: 'delete', model: Model): void;
}>();

const modelTypeIcons: Record<string, string> = {
  predictive: '📊',
  genai: '🤖',
  spm: '💭',
  agentic: '🦾',
};

const riskColors: Record<RiskLevel, { text: string; bg: string }> = {
  minimal: { text: 'text-green-600', bg: 'bg-green-100 dark:bg-green-900/30' },
  low: { text: 'text-blue-600', bg: 'bg-blue-100 dark:bg-blue-900/30' },
  medium: { text: 'text-yellow-600', bg: 'bg-yellow-100 dark:bg-yellow-900/30' },
  high: { text: 'text-orange-600', bg: 'bg-orange-100 dark:bg-orange-900/30' },
  critical: { text: 'text-red-600', bg: 'bg-red-100 dark:bg-red-900/30' },
};

const scoreColor = computed(() => {
  const score = props.model.lastScore || 0;
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-yellow-600';
  if (score >= 40) return 'text-orange-600';
  return 'text-red-600';
});

const lastEvalDate = computed(() => {
  if (!props.model.lastEvaluatedAt) return 'Never';
  const date = new Date(props.model.lastEvaluatedAt);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days} days ago`;
  return date.toLocaleDateString();
});
</script>

<template>
  <div
    :class="[
      'border rounded-lg transition-shadow hover:shadow-md',
      compact ? 'p-3' : 'p-4',
    ]"
  >
    <!-- Header -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-3">
        <span class="text-2xl">{{ modelTypeIcons[model.modelType] || '📦' }}</span>
        <div>
          <h4 class="font-semibold text-gray-900 dark:text-gray-100 line-clamp-1">
            {{ model.name }}
          </h4>
          <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span class="capitalize">{{ model.modelType }}</span>
            <span>•</span>
            <span>v{{ model.version }}</span>
          </div>
        </div>
      </div>
      
      <!-- Score badge -->
      <div
        v-if="model.lastScore !== undefined"
        :class="['text-2xl font-bold', scoreColor]"
      >
        {{ Math.round(model.lastScore) }}
      </div>
    </div>
    
    <!-- Description -->
    <p
      v-if="!compact && model.description"
      class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3"
    >
      {{ model.description }}
    </p>
    
    <!-- Metadata -->
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <!-- Risk level -->
      <span
        v-if="model.riskLevel"
        :class="[
          'px-2 py-0.5 rounded-full text-xs font-medium capitalize',
          riskColors[model.riskLevel].text,
          riskColors[model.riskLevel].bg,
        ]"
      >
        {{ model.riskLevel }} Risk
      </span>
      
      <!-- Framework -->
      <span
        v-if="model.framework"
        class="px-2 py-0.5 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
      >
        {{ model.framework }}
      </span>
      
      <!-- Tags -->
      <span
        v-for="tag in (model.tags || []).slice(0, 3)"
        :key="tag"
        class="px-2 py-0.5 rounded-full text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"
      >
        {{ tag }}
      </span>
    </div>
    
    <!-- Footer -->
    <div class="flex items-center justify-between pt-3 border-t">
      <div class="text-xs text-gray-500 dark:text-gray-400">
        Last evaluated: {{ lastEvalDate }}
      </div>
      
      <!-- Actions -->
      <div v-if="showActions" class="flex items-center gap-2">
        <button
          class="text-xs text-blue-600 hover:underline"
          @click="emit('view', model)"
        >
          View
        </button>
        <button
          class="text-xs text-green-600 hover:underline"
          @click="emit('evaluate', model)"
        >
          Evaluate
        </button>
        <button
          class="text-xs text-red-600 hover:underline"
          @click="emit('delete', model)"
        >
          Delete
        </button>
      </div>
    </div>
  </div>
</template>
