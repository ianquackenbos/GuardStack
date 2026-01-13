<script lang="ts" setup>
/**
 * PillarRadar Component
 * Radar chart for displaying 8-pillar or 4-pillar scores
 */
import { computed, onMounted, ref, watch } from 'vue';

interface PillarScore {
  pillar: string;
  score: number;
  label?: string;
}

const props = defineProps<{
  scores: PillarScore[];
  previousScores?: PillarScore[];
  size?: number;
  showLabels?: boolean;
  animated?: boolean;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);
const size = computed(() => props.size || 300);

// Pillar labels mapping
const pillarLabels: Record<string, string> = {
  explain: 'Explainability',
  actions: 'Adversarial',
  fairness: 'Fairness',
  robustness: 'Robustness',
  trace: 'Data Lineage',
  testing: 'Testing',
  imitation: 'IP Protection',
  privacy: 'Privacy',
  toxicity: 'Toxicity',
  security: 'Security',
};

const getLabel = (pillar: string): string => {
  return pillarLabels[pillar.toLowerCase()] || pillar;
};

const drawRadar = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const centerX = size.value / 2;
  const centerY = size.value / 2;
  const maxRadius = (size.value / 2) - 40;

  // Clear canvas
  ctx.clearRect(0, 0, size.value, size.value);

  const numPillars = props.scores.length;
  if (numPillars === 0) return;

  const angleStep = (2 * Math.PI) / numPillars;
  const startAngle = -Math.PI / 2; // Start from top

  // Draw grid circles
  const gridLevels = 5;
  ctx.strokeStyle = '#e5e7eb';
  ctx.lineWidth = 1;

  for (let i = 1; i <= gridLevels; i++) {
    const radius = (maxRadius / gridLevels) * i;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.stroke();
  }

  // Draw grid lines
  for (let i = 0; i < numPillars; i++) {
    const angle = startAngle + i * angleStep;
    const x = centerX + maxRadius * Math.cos(angle);
    const y = centerY + maxRadius * Math.sin(angle);

    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(x, y);
    ctx.stroke();
  }

  // Draw previous scores (if provided)
  if (props.previousScores && props.previousScores.length === numPillars) {
    ctx.fillStyle = 'rgba(156, 163, 175, 0.2)';
    ctx.strokeStyle = 'rgba(156, 163, 175, 0.5)';
    ctx.lineWidth = 2;
    ctx.beginPath();

    props.previousScores.forEach((score, i) => {
      const angle = startAngle + i * angleStep;
      const radius = (score.score / 100) * maxRadius;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }

  // Draw current scores
  const getScoreColor = (avgScore: number): string => {
    if (avgScore >= 80) return 'rgba(16, 185, 129, 0.7)';  // green
    if (avgScore >= 60) return 'rgba(234, 179, 8, 0.7)';   // yellow
    if (avgScore >= 40) return 'rgba(249, 115, 22, 0.7)';  // orange
    return 'rgba(239, 68, 68, 0.7)';  // red
  };

  const avgScore = props.scores.reduce((sum, s) => sum + s.score, 0) / numPillars;
  ctx.fillStyle = getScoreColor(avgScore).replace('0.7', '0.3');
  ctx.strokeStyle = getScoreColor(avgScore);
  ctx.lineWidth = 3;
  ctx.beginPath();

  props.scores.forEach((score, i) => {
    const angle = startAngle + i * angleStep;
    const radius = (score.score / 100) * maxRadius;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    if (i === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });

  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // Draw points
  props.scores.forEach((score, i) => {
    const angle = startAngle + i * angleStep;
    const radius = (score.score / 100) * maxRadius;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.fillStyle = getScoreColor(score.score);
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
  });

  // Draw labels
  if (props.showLabels !== false) {
    ctx.fillStyle = '#374151';
    ctx.font = '12px Inter, system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    props.scores.forEach((score, i) => {
      const angle = startAngle + i * angleStep;
      const labelRadius = maxRadius + 25;
      const x = centerX + labelRadius * Math.cos(angle);
      const y = centerY + labelRadius * Math.sin(angle);

      const label = score.label || getLabel(score.pillar);
      ctx.fillText(label, x, y);
      
      // Draw score below label
      ctx.font = 'bold 11px Inter, system-ui, sans-serif';
      ctx.fillStyle = getScoreColor(score.score);
      ctx.fillText(`${Math.round(score.score)}`, x, y + 14);
      ctx.fillStyle = '#374151';
      ctx.font = '12px Inter, system-ui, sans-serif';
    });
  }
};

onMounted(() => {
  drawRadar();
});

watch(() => props.scores, () => {
  drawRadar();
}, { deep: true });
</script>

<template>
  <div class="flex items-center justify-center">
    <canvas
      ref="canvasRef"
      :width="size"
      :height="size"
      class="max-w-full"
    ></canvas>
  </div>
</template>
