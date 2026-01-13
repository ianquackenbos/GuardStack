<script lang="ts" setup>
/**
 * ComplianceStatus Component
 * Displays compliance framework status with requirements
 */
import { computed } from 'vue';

interface Requirement {
  id: string;
  name: string;
  status: 'compliant' | 'partial' | 'non_compliant' | 'not_applicable';
  evidence?: string;
  lastAssessed?: string;
}

interface Framework {
  id: string;
  name: string;
  version?: string;
  requirements: Requirement[];
  overallStatus: 'compliant' | 'partial' | 'non_compliant';
  score?: number;
}

const props = defineProps<{
  framework: Framework;
  showDetails?: boolean;
  compact?: boolean;
}>();

const emit = defineEmits<{
  (e: 'view-details', framework: Framework): void;
  (e: 'view-requirement', requirement: Requirement): void;
}>();

const statusConfig = {
  compliant: {
    label: 'Compliant',
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
    icon: '✓',
  },
  partial: {
    label: 'Partial',
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
    icon: '◐',
  },
  non_compliant: {
    label: 'Non-Compliant',
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
    icon: '✗',
  },
  not_applicable: {
    label: 'N/A',
    color: 'text-gray-500 dark:text-gray-400',
    bg: 'bg-gray-100 dark:bg-gray-800',
    icon: '—',
  },
};

const statusCounts = computed(() => {
  const counts = {
    compliant: 0,
    partial: 0,
    non_compliant: 0,
    not_applicable: 0,
  };
  
  props.framework.requirements.forEach(req => {
    counts[req.status]++;
  });
  
  return counts;
});

const compliancePercentage = computed(() => {
  const applicable = props.framework.requirements.filter(r => r.status !== 'not_applicable');
  if (applicable.length === 0) return 100;
  
  const compliant = applicable.filter(r => r.status === 'compliant').length;
  return Math.round((compliant / applicable.length) * 100);
});

const frameworkIcon = computed(() => {
  const id = props.framework.id.toLowerCase();
  if (id.includes('eu') || id.includes('ai-act')) return '🇪🇺';
  if (id.includes('soc2')) return '🔒';
  if (id.includes('nist')) return '🏛️';
  if (id.includes('hipaa')) return '🏥';
  if (id.includes('gdpr')) return '🛡️';
  if (id.includes('iso')) return '📋';
  return '📜';
});
</script>

<template>
  <div
    :class="[
      'rounded-lg border p-4',
      compact ? 'p-3' : 'p-4',
    ]"
  >
    <!-- Header -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-3">
        <span class="text-2xl">{{ frameworkIcon }}</span>
        <div>
          <h4 class="font-semibold text-gray-900 dark:text-gray-100">
            {{ framework.name }}
          </h4>
          <p v-if="framework.version" class="text-xs text-gray-500 dark:text-gray-400">
            Version {{ framework.version }}
          </p>
        </div>
      </div>
      
      <!-- Status badge -->
      <span
        :class="[
          'px-2 py-1 rounded-full text-xs font-medium',
          statusConfig[framework.overallStatus].color,
          statusConfig[framework.overallStatus].bg,
        ]"
      >
        {{ statusConfig[framework.overallStatus].icon }}
        {{ statusConfig[framework.overallStatus].label }}
      </span>
    </div>
    
    <!-- Progress bar -->
    <div class="mb-3">
      <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
        <span>Compliance Score</span>
        <span>{{ compliancePercentage }}%</span>
      </div>
      <div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div class="h-full flex">
          <div
            class="bg-green-500 transition-all"
            :style="{ width: `${(statusCounts.compliant / framework.requirements.length) * 100}%` }"
          ></div>
          <div
            class="bg-yellow-500 transition-all"
            :style="{ width: `${(statusCounts.partial / framework.requirements.length) * 100}%` }"
          ></div>
          <div
            class="bg-red-500 transition-all"
            :style="{ width: `${(statusCounts.non_compliant / framework.requirements.length) * 100}%` }"
          ></div>
        </div>
      </div>
    </div>
    
    <!-- Status summary -->
    <div class="grid grid-cols-4 gap-2 text-center text-xs mb-3">
      <div>
        <div class="font-semibold text-green-600 dark:text-green-400">
          {{ statusCounts.compliant }}
        </div>
        <div class="text-gray-500 dark:text-gray-400">Compliant</div>
      </div>
      <div>
        <div class="font-semibold text-yellow-600 dark:text-yellow-400">
          {{ statusCounts.partial }}
        </div>
        <div class="text-gray-500 dark:text-gray-400">Partial</div>
      </div>
      <div>
        <div class="font-semibold text-red-600 dark:text-red-400">
          {{ statusCounts.non_compliant }}
        </div>
        <div class="text-gray-500 dark:text-gray-400">Non-Compliant</div>
      </div>
      <div>
        <div class="font-semibold text-gray-500 dark:text-gray-400">
          {{ statusCounts.not_applicable }}
        </div>
        <div class="text-gray-500 dark:text-gray-400">N/A</div>
      </div>
    </div>
    
    <!-- Requirements list (if showDetails) -->
    <div v-if="showDetails && framework.requirements.length > 0" class="border-t pt-3 mt-3">
      <h5 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Requirements
      </h5>
      <div class="space-y-2 max-h-48 overflow-y-auto">
        <div
          v-for="req in framework.requirements"
          :key="req.id"
          class="flex items-center justify-between p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
          @click="emit('view-requirement', req)"
        >
          <div class="flex items-center gap-2">
            <span :class="statusConfig[req.status].color">
              {{ statusConfig[req.status].icon }}
            </span>
            <span class="text-sm text-gray-700 dark:text-gray-300">
              {{ req.name }}
            </span>
          </div>
          <span class="text-xs text-gray-400">
            {{ req.id }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- Actions -->
    <div class="flex justify-end mt-3 pt-3 border-t">
      <button
        class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
        @click="emit('view-details', framework)"
      >
        View Full Report →
      </button>
    </div>
  </div>
</template>
