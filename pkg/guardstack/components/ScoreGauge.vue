<script lang="ts" setup>
/**
 * ScoreGauge Component
 * Displays a circular gauge for 0-100 scores
 */
import { computed } from 'vue';

const props = defineProps<{
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  label?: string;
  animated?: boolean;
}>();

const normalizedScore = computed(() => Math.min(100, Math.max(0, props.score)));

const sizeConfig = computed(() => {
  switch (props.size || 'md') {
    case 'sm':
      return { size: 80, stroke: 8, fontSize: 'text-lg' };
    case 'lg':
      return { size: 160, stroke: 12, fontSize: 'text-4xl' };
    default:
      return { size: 120, stroke: 10, fontSize: 'text-2xl' };
  }
});

const radius = computed(
  () => (sizeConfig.value.size - sizeConfig.value.stroke) / 2
);
const circumference = computed(() => 2 * Math.PI * radius.value);
const offset = computed(
  () => circumference.value - (normalizedScore.value / 100) * circumference.value
);

const scoreColor = computed(() => {
  if (normalizedScore.value >= 80) return '#10b981'; // green
  if (normalizedScore.value >= 60) return '#22c55e'; // light green
  if (normalizedScore.value >= 40) return '#eab308'; // yellow
  if (normalizedScore.value >= 20) return '#f97316'; // orange
  return '#ef4444'; // red
});

const riskLevel = computed(() => {
  if (normalizedScore.value >= 85) return 'Minimal Risk';
  if (normalizedScore.value >= 70) return 'Low Risk';
  if (normalizedScore.value >= 50) return 'Medium Risk';
  if (normalizedScore.value >= 30) return 'High Risk';
  return 'Critical Risk';
});
</script>

<template>
  <div class="flex flex-col items-center">
    <div class="relative" :style="{ width: `${sizeConfig.size}px`, height: `${sizeConfig.size}px` }">
      <!-- Background circle -->
      <svg
        :width="sizeConfig.size"
        :height="sizeConfig.size"
        class="transform -rotate-90"
      >
        <circle
          :cx="sizeConfig.size / 2"
          :cy="sizeConfig.size / 2"
          :r="radius"
          :stroke-width="sizeConfig.stroke"
          fill="none"
          class="stroke-gray-200 dark:stroke-gray-700"
        />
        <!-- Score arc -->
        <circle
          :cx="sizeConfig.size / 2"
          :cy="sizeConfig.size / 2"
          :r="radius"
          :stroke-width="sizeConfig.stroke"
          fill="none"
          :stroke="scoreColor"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="offset"
          stroke-linecap="round"
          :class="{ 'transition-all duration-1000 ease-out': animated }"
        />
      </svg>
      <!-- Score text -->
      <div
        class="absolute inset-0 flex flex-col items-center justify-center"
      >
        <span :class="['font-bold', sizeConfig.fontSize]" :style="{ color: scoreColor }">
          {{ Math.round(normalizedScore) }}
        </span>
        <span v-if="size !== 'sm'" class="text-xs text-gray-500 dark:text-gray-400">
          / 100
        </span>
      </div>
    </div>
    <!-- Label -->
    <div v-if="showLabel" class="mt-2 text-center">
      <div class="text-sm font-medium text-gray-900 dark:text-gray-100">
        {{ label || riskLevel }}
      </div>
    </div>
  </div>
</template>
