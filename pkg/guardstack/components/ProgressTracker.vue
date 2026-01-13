<script lang="ts" setup>
/**
 * ProgressTracker Component
 * Displays evaluation progress with stages
 */
import { computed } from 'vue';

interface Stage {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress?: number;
  message?: string;
  startedAt?: string;
  completedAt?: string;
  duration?: number;
}

const props = defineProps<{
  stages: Stage[];
  currentStage?: string;
  showDuration?: boolean;
  compact?: boolean;
}>();

const statusConfig = {
  pending: {
    icon: '○',
    color: 'text-gray-400',
    bgColor: 'bg-gray-200 dark:bg-gray-700',
    label: 'Pending',
  },
  running: {
    icon: '◐',
    color: 'text-blue-500',
    bgColor: 'bg-blue-500',
    label: 'Running',
  },
  completed: {
    icon: '✓',
    color: 'text-green-500',
    bgColor: 'bg-green-500',
    label: 'Completed',
  },
  failed: {
    icon: '✗',
    color: 'text-red-500',
    bgColor: 'bg-red-500',
    label: 'Failed',
  },
  skipped: {
    icon: '—',
    color: 'text-gray-400',
    bgColor: 'bg-gray-300 dark:bg-gray-600',
    label: 'Skipped',
  },
};

const overallProgress = computed(() => {
  const completed = props.stages.filter(s => 
    s.status === 'completed' || s.status === 'skipped'
  ).length;
  return Math.round((completed / props.stages.length) * 100);
});

const totalDuration = computed(() => {
  return props.stages.reduce((sum, stage) => sum + (stage.duration || 0), 0);
});

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.round((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}
</script>

<template>
  <div class="progress-tracker">
    <!-- Overall progress bar -->
    <div v-if="!compact" class="mb-4">
      <div class="flex justify-between text-sm mb-1">
        <span class="text-gray-700 dark:text-gray-300">Overall Progress</span>
        <span class="text-gray-500 dark:text-gray-400">{{ overallProgress }}%</span>
      </div>
      <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          class="h-full bg-blue-500 transition-all duration-500"
          :style="{ width: `${overallProgress}%` }"
        ></div>
      </div>
      <div v-if="showDuration && totalDuration > 0" class="text-xs text-gray-500 dark:text-gray-400 mt-1">
        Total: {{ formatDuration(totalDuration) }}
      </div>
    </div>
    
    <!-- Stages -->
    <div :class="compact ? 'flex items-center gap-2' : 'space-y-3'">
      <template v-for="(stage, index) in stages" :key="stage.id">
        <!-- Connector line (vertical layout) -->
        <div
          v-if="!compact && index > 0"
          class="ml-3 h-4 w-0.5"
          :class="[
            stages[index - 1].status === 'completed' ? 'bg-green-500' :
            stages[index - 1].status === 'failed' ? 'bg-red-500' : 
            'bg-gray-300 dark:bg-gray-600'
          ]"
        ></div>
        
        <!-- Stage item -->
        <div
          :class="[
            compact ? 'flex items-center gap-1' : 'flex items-start gap-3',
            stage.id === currentStage ? 'ring-2 ring-blue-300 rounded-lg p-2 -m-2' : '',
          ]"
        >
          <!-- Status icon -->
          <div
            :class="[
              'flex-shrink-0 flex items-center justify-center rounded-full',
              compact ? 'w-6 h-6 text-xs' : 'w-8 h-8 text-sm',
              stage.status === 'running' ? 'animate-pulse' : '',
              statusConfig[stage.status].bgColor,
              stage.status === 'pending' || stage.status === 'skipped' ? '' : 'text-white',
            ]"
          >
            <span v-if="stage.status !== 'running'">
              {{ statusConfig[stage.status].icon }}
            </span>
            <svg
              v-else
              class="animate-spin h-4 w-4 text-white"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          </div>
          
          <!-- Stage info -->
          <div v-if="!compact" class="flex-grow">
            <div class="flex items-center justify-between">
              <span class="font-medium text-gray-900 dark:text-gray-100">
                {{ stage.name }}
              </span>
              <span v-if="showDuration && stage.duration" class="text-xs text-gray-500 dark:text-gray-400">
                {{ formatDuration(stage.duration) }}
              </span>
            </div>
            
            <!-- Progress bar for running stage -->
            <div v-if="stage.status === 'running' && stage.progress !== undefined" class="mt-1">
              <div class="h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-blue-500 transition-all"
                  :style="{ width: `${stage.progress}%` }"
                ></div>
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {{ stage.progress }}%
              </div>
            </div>
            
            <!-- Message -->
            <div
              v-if="stage.message"
              :class="[
                'text-xs mt-1',
                stage.status === 'failed' ? 'text-red-500' : 'text-gray-500 dark:text-gray-400',
              ]"
            >
              {{ stage.message }}
            </div>
          </div>
          
          <!-- Compact tooltip -->
          <span
            v-if="compact"
            :class="['text-xs', statusConfig[stage.status].color]"
            :title="stage.name"
          >
            {{ stage.name.substring(0, 10) }}{{ stage.name.length > 10 ? '...' : '' }}
          </span>
        </div>
        
        <!-- Connector (horizontal/compact layout) -->
        <div
          v-if="compact && index < stages.length - 1"
          class="w-4 h-0.5"
          :class="[
            stage.status === 'completed' ? 'bg-green-500' :
            stage.status === 'failed' ? 'bg-red-500' : 
            'bg-gray-300 dark:bg-gray-600'
          ]"
        ></div>
      </template>
    </div>
  </div>
</template>
