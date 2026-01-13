<script lang="ts" setup>
/**
 * RiskSummaryCard Component
 * Displays Pass/Warn/Fail counts in a summary card
 */
import { computed } from 'vue';

const props = defineProps<{
  pass: number;
  warn: number;
  fail: number;
  title?: string;
  showPercentages?: boolean;
}>();

const total = computed(() => props.pass + props.warn + props.fail);

const percentages = computed(() => {
  if (total.value === 0) return { pass: 0, warn: 0, fail: 0 };
  return {
    pass: Math.round((props.pass / total.value) * 100),
    warn: Math.round((props.warn / total.value) * 100),
    fail: Math.round((props.fail / total.value) * 100),
  };
});

const barWidths = computed(() => {
  if (total.value === 0) return { pass: '0%', warn: '0%', fail: '0%' };
  return {
    pass: `${(props.pass / total.value) * 100}%`,
    warn: `${(props.warn / total.value) * 100}%`,
    fail: `${(props.fail / total.value) * 100}%`,
  };
});
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
      {{ title || 'Risk Summary' }}
    </h3>
    
    <!-- Stats grid -->
    <div class="grid grid-cols-3 gap-4 mb-6">
      <!-- Pass -->
      <div class="text-center">
        <div class="text-3xl font-bold text-green-600 dark:text-green-400">
          {{ pass }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          Pass
          <span v-if="showPercentages" class="ml-1">({{ percentages.pass }}%)</span>
        </div>
      </div>
      
      <!-- Warn -->
      <div class="text-center">
        <div class="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
          {{ warn }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          Warning
          <span v-if="showPercentages" class="ml-1">({{ percentages.warn }}%)</span>
        </div>
      </div>
      
      <!-- Fail -->
      <div class="text-center">
        <div class="text-3xl font-bold text-red-600 dark:text-red-400">
          {{ fail }}
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400">
          Fail
          <span v-if="showPercentages" class="ml-1">({{ percentages.fail }}%)</span>
        </div>
      </div>
    </div>
    
    <!-- Progress bar -->
    <div class="h-3 rounded-full overflow-hidden flex bg-gray-200 dark:bg-gray-700">
      <div
        class="bg-green-500 transition-all duration-500"
        :style="{ width: barWidths.pass }"
      ></div>
      <div
        class="bg-yellow-500 transition-all duration-500"
        :style="{ width: barWidths.warn }"
      ></div>
      <div
        class="bg-red-500 transition-all duration-500"
        :style="{ width: barWidths.fail }"
      ></div>
    </div>
    
    <!-- Total -->
    <div class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
      Total Models: <span class="font-semibold">{{ total }}</span>
    </div>
  </div>
</template>
