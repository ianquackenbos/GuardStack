<script lang="ts" setup>
/**
 * TrendChart Component
 * Displays score trends over time using Canvas
 */
import { ref, onMounted, watch, computed } from 'vue';

interface DataPoint {
  date: string | Date;
  value: number;
  label?: string;
}

const props = withDefaults(defineProps<{
  data: DataPoint[];
  title?: string;
  color?: string;
  fillColor?: string;
  height?: number;
  showGrid?: boolean;
  showDots?: boolean;
  showLabels?: boolean;
  thresholds?: { value: number; color: string; label?: string }[];
}>(), {
  color: '#3b82f6',
  fillColor: 'rgba(59, 130, 246, 0.1)',
  height: 200,
  showGrid: true,
  showDots: true,
  showLabels: true,
});

const canvasRef = ref<HTMLCanvasElement | null>(null);
const containerRef = ref<HTMLDivElement | null>(null);

const sortedData = computed(() => {
  return [...props.data].sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return dateA - dateB;
  });
});

const stats = computed(() => {
  if (sortedData.value.length === 0) return null;
  
  const values = sortedData.value.map(d => d.value);
  const current = values[values.length - 1];
  const previous = values.length > 1 ? values[values.length - 2] : current;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  const change = current - previous;
  const changePercent = previous !== 0 ? (change / previous) * 100 : 0;
  
  return { current, previous, min, max, avg, change, changePercent };
});

function draw() {
  const canvas = canvasRef.value;
  const container = containerRef.value;
  if (!canvas || !container) return;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  // Get container dimensions
  const rect = container.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  
  canvas.width = rect.width * dpr;
  canvas.height = props.height * dpr;
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${props.height}px`;
  
  ctx.scale(dpr, dpr);
  
  const width = rect.width;
  const height = props.height;
  const padding = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  
  // Clear canvas
  ctx.clearRect(0, 0, width, height);
  
  if (sortedData.value.length === 0) {
    ctx.fillStyle = '#9ca3af';
    ctx.font = '14px system-ui';
    ctx.textAlign = 'center';
    ctx.fillText('No data available', width / 2, height / 2);
    return;
  }
  
  // Calculate ranges
  const values = sortedData.value.map(d => d.value);
  const minValue = Math.min(...values) * 0.9;
  const maxValue = Math.max(...values) * 1.1;
  const valueRange = maxValue - minValue || 1;
  
  // Helper functions
  const getX = (index: number) => padding.left + (index / (sortedData.value.length - 1 || 1)) * chartWidth;
  const getY = (value: number) => padding.top + chartHeight - ((value - minValue) / valueRange) * chartHeight;
  
  // Draw grid
  if (props.showGrid) {
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines
    const gridLines = 5;
    for (let i = 0; i <= gridLines; i++) {
      const y = padding.top + (i / gridLines) * chartHeight;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();
      
      // Y-axis labels
      if (props.showLabels) {
        const value = maxValue - (i / gridLines) * valueRange;
        ctx.fillStyle = '#9ca3af';
        ctx.font = '11px system-ui';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(value).toString(), padding.left - 8, y + 4);
      }
    }
  }
  
  // Draw threshold lines
  if (props.thresholds) {
    props.thresholds.forEach(threshold => {
      const y = getY(threshold.value);
      ctx.strokeStyle = threshold.color;
      ctx.setLineDash([5, 5]);
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();
      ctx.setLineDash([]);
      
      if (threshold.label) {
        ctx.fillStyle = threshold.color;
        ctx.font = '10px system-ui';
        ctx.textAlign = 'left';
        ctx.fillText(threshold.label, width - padding.right + 4, y + 3);
      }
    });
  }
  
  // Draw filled area
  ctx.beginPath();
  ctx.moveTo(getX(0), getY(sortedData.value[0].value));
  sortedData.value.forEach((point, i) => {
    ctx.lineTo(getX(i), getY(point.value));
  });
  ctx.lineTo(getX(sortedData.value.length - 1), padding.top + chartHeight);
  ctx.lineTo(getX(0), padding.top + chartHeight);
  ctx.closePath();
  ctx.fillStyle = props.fillColor;
  ctx.fill();
  
  // Draw line
  ctx.beginPath();
  ctx.moveTo(getX(0), getY(sortedData.value[0].value));
  sortedData.value.forEach((point, i) => {
    ctx.lineTo(getX(i), getY(point.value));
  });
  ctx.strokeStyle = props.color;
  ctx.lineWidth = 2;
  ctx.stroke();
  
  // Draw dots
  if (props.showDots) {
    sortedData.value.forEach((point, i) => {
      ctx.beginPath();
      ctx.arc(getX(i), getY(point.value), 4, 0, Math.PI * 2);
      ctx.fillStyle = props.color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }
  
  // Draw X-axis labels
  if (props.showLabels) {
    ctx.fillStyle = '#9ca3af';
    ctx.font = '10px system-ui';
    ctx.textAlign = 'center';
    
    const labelCount = Math.min(sortedData.value.length, 6);
    const step = Math.floor(sortedData.value.length / labelCount) || 1;
    
    sortedData.value.forEach((point, i) => {
      if (i % step === 0 || i === sortedData.value.length - 1) {
        const date = new Date(point.date);
        const label = point.label || date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        ctx.fillText(label, getX(i), height - padding.bottom + 20);
      }
    });
  }
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
  <div class="trend-chart">
    <!-- Header -->
    <div v-if="title || stats" class="flex items-center justify-between mb-4">
      <h4 v-if="title" class="font-semibold text-gray-900 dark:text-gray-100">
        {{ title }}
      </h4>
      <div v-if="stats" class="flex items-center gap-4 text-sm">
        <span class="text-gray-500 dark:text-gray-400">
          Current: <span class="font-semibold text-gray-900 dark:text-gray-100">{{ Math.round(stats.current) }}</span>
        </span>
        <span
          :class="[
            'flex items-center gap-1',
            stats.change > 0 ? 'text-green-600' : stats.change < 0 ? 'text-red-600' : 'text-gray-400',
          ]"
        >
          <span>{{ stats.change > 0 ? '↑' : stats.change < 0 ? '↓' : '→' }}</span>
          <span>{{ Math.abs(Math.round(stats.changePercent)) }}%</span>
        </span>
      </div>
    </div>
    
    <!-- Chart -->
    <div ref="containerRef" class="relative w-full">
      <canvas ref="canvasRef" class="w-full"></canvas>
    </div>
    
    <!-- Stats footer -->
    <div v-if="stats" class="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
      <span>Min: {{ Math.round(stats.min) }}</span>
      <span>Avg: {{ Math.round(stats.avg) }}</span>
      <span>Max: {{ Math.round(stats.max) }}</span>
    </div>
  </div>
</template>
