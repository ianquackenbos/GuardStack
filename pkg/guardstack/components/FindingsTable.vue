<script lang="ts" setup>
/**
 * FindingsTable Component
 * Displays evaluation findings in a sortable table
 */
import { ref, computed } from 'vue';

interface Finding {
  id: string;
  pillar: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  recommendation?: string;
  status: 'open' | 'acknowledged' | 'resolved' | 'false_positive';
  createdAt: string;
  evidence?: Record<string, unknown>;
}

const props = withDefaults(defineProps<{
  findings: Finding[];
  showPagination?: boolean;
  pageSize?: number;
  selectable?: boolean;
}>(), {
  showPagination: true,
  pageSize: 10,
  selectable: false,
});

const emit = defineEmits<{
  (e: 'view', finding: Finding): void;
  (e: 'acknowledge', finding: Finding): void;
  (e: 'resolve', finding: Finding): void;
  (e: 'select', findings: Finding[]): void;
}>();

const currentPage = ref(1);
const sortField = ref<keyof Finding>('severity');
const sortOrder = ref<'asc' | 'desc'>('desc');
const selectedIds = ref<Set<string>>(new Set());
const filterSeverity = ref<string>('all');
const filterStatus = ref<string>('all');

const severityConfig = {
  critical: { label: 'Critical', color: 'bg-red-600 text-white', priority: 5 },
  high: { label: 'High', color: 'bg-orange-500 text-white', priority: 4 },
  medium: { label: 'Medium', color: 'bg-yellow-500 text-black', priority: 3 },
  low: { label: 'Low', color: 'bg-blue-500 text-white', priority: 2 },
  info: { label: 'Info', color: 'bg-gray-400 text-white', priority: 1 },
};

const statusConfig = {
  open: { label: 'Open', color: 'text-red-600 dark:text-red-400' },
  acknowledged: { label: 'Acknowledged', color: 'text-yellow-600 dark:text-yellow-400' },
  resolved: { label: 'Resolved', color: 'text-green-600 dark:text-green-400' },
  false_positive: { label: 'False Positive', color: 'text-gray-500 dark:text-gray-400' },
};

const filteredFindings = computed(() => {
  let result = [...props.findings];
  
  if (filterSeverity.value !== 'all') {
    result = result.filter(f => f.severity === filterSeverity.value);
  }
  
  if (filterStatus.value !== 'all') {
    result = result.filter(f => f.status === filterStatus.value);
  }
  
  return result;
});

const sortedFindings = computed(() => {
  const result = [...filteredFindings.value];
  
  result.sort((a, b) => {
    let comparison = 0;
    
    if (sortField.value === 'severity') {
      comparison = severityConfig[a.severity].priority - severityConfig[b.severity].priority;
    } else if (sortField.value === 'createdAt') {
      comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
    } else {
      const aVal = String(a[sortField.value]);
      const bVal = String(b[sortField.value]);
      comparison = aVal.localeCompare(bVal);
    }
    
    return sortOrder.value === 'asc' ? comparison : -comparison;
  });
  
  return result;
});

const paginatedFindings = computed(() => {
  if (!props.showPagination) return sortedFindings.value;
  
  const start = (currentPage.value - 1) * props.pageSize;
  return sortedFindings.value.slice(start, start + props.pageSize);
});

const totalPages = computed(() => 
  Math.ceil(sortedFindings.value.length / props.pageSize)
);

const allSelected = computed(() => 
  paginatedFindings.value.length > 0 && 
  paginatedFindings.value.every(f => selectedIds.value.has(f.id))
);

function toggleSort(field: keyof Finding) {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortField.value = field;
    sortOrder.value = 'desc';
  }
}

function toggleSelect(finding: Finding) {
  if (selectedIds.value.has(finding.id)) {
    selectedIds.value.delete(finding.id);
  } else {
    selectedIds.value.add(finding.id);
  }
  emit('select', props.findings.filter(f => selectedIds.value.has(f.id)));
}

function toggleSelectAll() {
  if (allSelected.value) {
    paginatedFindings.value.forEach(f => selectedIds.value.delete(f.id));
  } else {
    paginatedFindings.value.forEach(f => selectedIds.value.add(f.id));
  }
  emit('select', props.findings.filter(f => selectedIds.value.has(f.id)));
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>

<template>
  <div class="findings-table">
    <!-- Filters -->
    <div class="flex items-center gap-4 mb-4">
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-500 dark:text-gray-400">Severity:</label>
        <select
          v-model="filterSeverity"
          class="text-sm border rounded px-2 py-1 bg-white dark:bg-gray-800"
        >
          <option value="all">All</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="info">Info</option>
        </select>
      </div>
      
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-500 dark:text-gray-400">Status:</label>
        <select
          v-model="filterStatus"
          class="text-sm border rounded px-2 py-1 bg-white dark:bg-gray-800"
        >
          <option value="all">All</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
          <option value="false_positive">False Positive</option>
        </select>
      </div>
      
      <div class="text-sm text-gray-500 dark:text-gray-400 ml-auto">
        {{ filteredFindings.length }} findings
      </div>
    </div>
    
    <!-- Table -->
    <div class="overflow-x-auto border rounded-lg">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th v-if="selectable" class="px-3 py-2 text-left">
              <input
                type="checkbox"
                :checked="allSelected"
                @change="toggleSelectAll"
              />
            </th>
            <th
              class="px-3 py-2 text-left cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
              @click="toggleSort('severity')"
            >
              <div class="flex items-center gap-1">
                Severity
                <span v-if="sortField === 'severity'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
            <th
              class="px-3 py-2 text-left cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
              @click="toggleSort('pillar')"
            >
              <div class="flex items-center gap-1">
                Pillar
                <span v-if="sortField === 'pillar'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
            <th
              class="px-3 py-2 text-left cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
              @click="toggleSort('title')"
            >
              <div class="flex items-center gap-1">
                Finding
                <span v-if="sortField === 'title'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
            <th
              class="px-3 py-2 text-left cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
              @click="toggleSort('status')"
            >
              <div class="flex items-center gap-1">
                Status
                <span v-if="sortField === 'status'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
            <th
              class="px-3 py-2 text-left cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700"
              @click="toggleSort('createdAt')"
            >
              <div class="flex items-center gap-1">
                Date
                <span v-if="sortField === 'createdAt'">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
            <th class="px-3 py-2 text-left">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="finding in paginatedFindings"
            :key="finding.id"
            class="border-t hover:bg-gray-50 dark:hover:bg-gray-800/50"
          >
            <td v-if="selectable" class="px-3 py-2">
              <input
                type="checkbox"
                :checked="selectedIds.has(finding.id)"
                @change="toggleSelect(finding)"
              />
            </td>
            <td class="px-3 py-2">
              <span :class="['px-2 py-0.5 rounded text-xs font-medium', severityConfig[finding.severity].color]">
                {{ severityConfig[finding.severity].label }}
              </span>
            </td>
            <td class="px-3 py-2 capitalize text-gray-700 dark:text-gray-300">
              {{ finding.pillar }}
            </td>
            <td class="px-3 py-2">
              <div class="font-medium text-gray-900 dark:text-gray-100">
                {{ finding.title }}
              </div>
              <div class="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">
                {{ finding.description }}
              </div>
            </td>
            <td class="px-3 py-2">
              <span :class="statusConfig[finding.status].color">
                {{ statusConfig[finding.status].label }}
              </span>
            </td>
            <td class="px-3 py-2 text-gray-500 dark:text-gray-400 whitespace-nowrap">
              {{ formatDate(finding.createdAt) }}
            </td>
            <td class="px-3 py-2">
              <div class="flex items-center gap-2">
                <button
                  class="text-blue-600 hover:underline"
                  @click="emit('view', finding)"
                >
                  View
                </button>
                <button
                  v-if="finding.status === 'open'"
                  class="text-yellow-600 hover:underline"
                  @click="emit('acknowledge', finding)"
                >
                  Ack
                </button>
                <button
                  v-if="finding.status !== 'resolved'"
                  class="text-green-600 hover:underline"
                  @click="emit('resolve', finding)"
                >
                  Resolve
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="paginatedFindings.length === 0">
            <td
              :colspan="selectable ? 7 : 6"
              class="px-3 py-8 text-center text-gray-500 dark:text-gray-400"
            >
              No findings match the current filters
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- Pagination -->
    <div v-if="showPagination && totalPages > 1" class="flex items-center justify-between mt-4">
      <div class="text-sm text-gray-500 dark:text-gray-400">
        Showing {{ (currentPage - 1) * pageSize + 1 }} to 
        {{ Math.min(currentPage * pageSize, filteredFindings.length) }} of 
        {{ filteredFindings.length }}
      </div>
      <div class="flex items-center gap-2">
        <button
          :disabled="currentPage === 1"
          class="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-800"
          @click="currentPage--"
        >
          Previous
        </button>
        <span class="text-sm text-gray-700 dark:text-gray-300">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        <button
          :disabled="currentPage === totalPages"
          class="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-800"
          @click="currentPage++"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>
