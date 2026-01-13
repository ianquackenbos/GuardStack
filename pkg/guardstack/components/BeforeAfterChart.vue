<script lang="ts" setup>
/**
 * BeforeAfterChart Component
 * Compares scores before and after remediation
 */
import { ref, onMounted, watch, computed } from 'vue';

interface ComparisonData {
  label: string;
  before: number;
  after: number;
}

const props = withDefaults(defineProps<{
  data: ComparisonData[];
  title?: string;
  beforeLabel?: string;
  afterLabel?: string;
  height?: number;
  showDiff?: boolean;
  threshold?: number;
}>(), {
  beforeLabel: 'Before',
  afterLabel: 'After',
  height: 300,
  showDiff: true,
  threshold: 60,
});

const canvasRef = ref<HTMLCanvasElement | null>(null);
const containerRef = ref<HTMLDivElement | null>(null);

const improvements = computed(() => {
  return props.data.map(d => ({
    ...d,
    diff: d.after - d.before,
    percentChange: d.before !== 0 ? ((d.after - d.before) / d.before) * 100 : 0,
  }));
});

const summary = computed(() => {
  const improved = improvements.value.filter(d => d.diff > 0).length;
  const declined = improvements.value.filter(d => d.diff < 0).length;
  const unchanged = improvements.value.filter(d => d.diff === 0).length;
  const avgImprovement = improvements.value.reduce((sum, d) => sum + d.diff, 0) / improvements.value.length;
  
  return { improved, declined, unchanged, avgImprovement };
});

function draw() {
  const canvas = canvasRef.value;
  const container = containerRef.value;
  if (!canvas || !container) return;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  const rect = container.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  
  canvas.width = rect.width * dpr;
  canvas.height = props.height * dpr;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${props.height}px`;
  
  ctx.scale(dpr, dpr);
  
  const width = rect.width;
  const height = props.height;
  const padding = { top: 30, right: 20, bottom: 60, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  
  ctx.clearRect(0, 0, width, height);
  
  if (props.data.length === 0) {
    ctx.fillStyle = '#9ca3af';
    ctx.font = '14px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText('No comparison data', width / 2, height / 2);
    return;
  }
  
  const barWidth = Math.min(30, chartWidth / (props.data.length * 3));
  const groupWidth = barWidth * 2 + 10;
  const totalGroupWidth = groupWidth * props.data.length;
  const startX = padding.left + (chartWidth - totalGroupWidth) / 2;
  
  // Draw threshold line
  if (props.threshold) {
    const thresholdY = padding.top + chartHeight - (props.threshold / 100) * chartHeight;
    ctx.strokeStyle = '#f59e0b';
    ctx.setLineDash([5, 5]);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding.left, thresholdY);
    ctx.lineTo(width - padding.right, thresholdY);
    ctx.stroke();
    ctx.setLineDash([]);
    
    ctx.fillStyle = '#f59e0b';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'left';
    ctx.fillText(`Threshold (${props.threshold})`, width - padding.right + 5, thresholdY + 3);
  }
  
  // Draw Y-axis
  ctx.strokeStyle = '#e5e7eb';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (i / 5) * chartHeight;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    
    const value = 100 - (i / 5) * 100;
    ctx.fillStyle = '#9ca3af';
    ctx.font = '11px system-ui';
    ctx.textAlign = 'right';
    ctx.fillText(Math.round(value).toString(), padding.left - 8, y + 4);
  }
  
  // Draw bars
  props.data.forEach((item, index) => {
    const groupX = startX + index * groupWidth;
    
    // Before bar
    const beforeHeight = (item.before / 100) * chartHeight;
    const beforeY = padding.top + chartHeight - beforeHeight;
    
    ctx.fillStyle = '#94a3b8';
    ctx.fillRect(groupX, beforeY, barWidth, beforeHeight);
    
    // After bar
    const afterHeight = (item.after / 100) * chartHeight;
    const afterY = padding.top + chartHeight - afterHeight;
    
    const afterColor = item.after >= props.threshold ? '#22c55e' : 
                       item.after >= item.before ? '#3b82f6' : '#ef4444';
    ctx.fillStyle = afterColor;
    ctx.fillRect(groupX + barWidth + 10, afterY, barWidth, afterHeight);
    
    // Improvement arrow
    if (props.showDiff && item.after !== item.before) {
      const arrowX = groupX + groupWidth / 2;
      const diff = item.after - item.before;
      
      ctx.fillStyle = diff > 0 ? '#22c55e' : '#ef4444';
      ctx.font = 'bold 11px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText(
        `${diff > 0 ? '+' : ''}${Math.round(diff)}`,
        arrowX,
        Math.min(beforeY, afterY) - 8
      );
    }
    
    // X-axis label
    ctx.fillStyle = '#374151';
    ctx.font = '11px system-ui';
    ctx.textAlign = 'center';
    ctx.save();
    ctx.translate(groupX + groupWidth / 2, height - padding.bottom + 15);
    ctx.rotate(-Math.PI / 6);
    ctx.fillText(item.label, 0, 0);
    ctx.restore();
  });
  
  // Draw legend
  const legendY = padding.top - 15;
  
  ctx.fillStyle = '#94a3b8';
  ctx.fillRect(padding.left, legendY - 8, 12, 12);
  ctx.fillStyle = '#374151';
  ctx.font = '11px system-ui';
  ctx.textAlign = 'left';
  ctx.fillText(props.beforeLabel, padding.left + 16, legendY);
  
  ctx.fillStyle = '#3b82f6';
  ctx.fillRect(padding.left + 80, legendY - 8, 12, 12);
  ctx.fillStyle = '#374151';
  ctx.fillText(props.afterLabel, padding.left + 96, legendY);
}

onMounted(() => {
  draw();
  
  const resizeObserver = new ResizeObserver(() => {
    draw();
  });
  
  if (containerRef.value) {
    resizeObserver.observe(containerRef.value);
  }
});

watch(() => props.data, draw, { deep: true });
</script>

<template>
  <div class="before-after-chart">
    <!-- Header -->
    <div v-if="title" class="flex items-center justify-between mb-4">
      <h4 class="font-semibold text-gray-900 dark:text-gray-100">
        {{ title }}
      </h4>
    </div>
    
    <!-- Summary -->
    <div class="grid grid-cols-4 gap-4 mb-4 text-center">
      <div class="p-2 bg-gray-50 dark:bg-gray-800 rounded">
        <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {{ data.length }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Total</div>
      </div>
      <div class="p-2 bg-green-50 dark:bg-green-900/20 rounded">
        <div class="text-lg font-semibold text-green-600">
          {{ summary.improved }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Improved</div>
      </div>
      <div class="p-2 bg-red-50 dark:bg-red-900/20 rounded">
        <div class="text-lg font-semibold text-red-600">
          {{ summary.declined }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Declined</div>
      </div>
      <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
        <div class="text-lg font-semibold text-blue-600">
          {{ summary.avgImprovement > 0 ? '+' : '' }}{{ Math.round(summary.avgImprovement) }}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400">Avg Change</div>
      </div>
    </div>
    
    <!-- Chart -->
    <div ref="containerRef" class="relative w-full">
      <canvas ref="canvasRef" class="w-full"></canvas>
    </div>
    
    <!-- Detailed table -->
    <div v-if="showDiff" class="mt-4 overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th class="px-3 py-2 text-left">Metric</th>
            <th class="px-3 py-2 text-right">{{ beforeLabel }}</th>
            <th class="px-3 py-2 text-right">{{ afterLabel }}</th>
            <th class="px-3 py-2 text-right">Change</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in improvements"
            :key="item.label"
            class="border-t"
          >
            <td class="px-3 py-2 text-gray-700 dark:text-gray-300">
              {{ item.label }}
            </td>
            <td class="px-3 py-2 text-right text-gray-500 dark:text-gray-400">
              {{ Math.round(item.before) }}
            </td>
            <td
              class="px-3 py-2 text-right font-medium"
              :class="item.after >= threshold ? 'text-green-600' : 'text-yellow-600'"
            >
              {{ Math.round(item.after) }}
            </td>
            <td
              class="px-3 py-2 text-right font-medium"
              :class="[
                item.diff > 0 ? 'text-green-600' :
                item.diff < 0 ? 'text-red-600' : 'text-gray-400'
              ]"
            >
              {{ item.diff > 0 ? '+' : '' }}{{ Math.round(item.diff) }}
              <span class="text-xs">
                ({{ item.percentChange > 0 ? '+' : '' }}{{ Math.round(item.percentChange) }}%)
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
