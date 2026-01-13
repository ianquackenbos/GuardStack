<script lang="ts" setup>
/**
 * StatusBadge Component
 * Displays Pass/Warn/Fail status badges
 */
import { computed } from 'vue';

const props = defineProps<{
  status: 'pass' | 'warn' | 'fail' | 'unknown' | 'running';
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}>();

const sizeClasses = computed(() => {
  switch (props.size || 'md') {
    case 'sm':
      return 'px-2 py-0.5 text-xs';
    case 'lg':
      return 'px-4 py-2 text-base';
    default:
      return 'px-3 py-1 text-sm';
  }
});

const statusConfig = computed(() => {
  switch (props.status) {
    case 'pass':
      return {
        label: 'Pass',
        bgClass: 'bg-green-100 dark:bg-green-900',
        textClass: 'text-green-800 dark:text-green-200',
        dotClass: 'bg-green-500',
      };
    case 'warn':
      return {
        label: 'Warning',
        bgClass: 'bg-yellow-100 dark:bg-yellow-900',
        textClass: 'text-yellow-800 dark:text-yellow-200',
        dotClass: 'bg-yellow-500',
      };
    case 'fail':
      return {
        label: 'Fail',
        bgClass: 'bg-red-100 dark:bg-red-900',
        textClass: 'text-red-800 dark:text-red-200',
        dotClass: 'bg-red-500',
      };
    case 'running':
      return {
        label: 'Running',
        bgClass: 'bg-blue-100 dark:bg-blue-900',
        textClass: 'text-blue-800 dark:text-blue-200',
        dotClass: 'bg-blue-500 animate-pulse',
      };
    default:
      return {
        label: 'Unknown',
        bgClass: 'bg-gray-100 dark:bg-gray-800',
        textClass: 'text-gray-600 dark:text-gray-400',
        dotClass: 'bg-gray-400',
      };
  }
});
</script>

<template>
  <span
    :class="[
      'inline-flex items-center rounded-full font-medium',
      sizeClasses,
      statusConfig.bgClass,
      statusConfig.textClass,
    ]"
  >
    <span :class="['w-2 h-2 rounded-full mr-2', statusConfig.dotClass]"></span>
    <span v-if="showLabel !== false">{{ statusConfig.label }}</span>
  </span>
</template>
