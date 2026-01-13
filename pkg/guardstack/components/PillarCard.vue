<script setup lang="ts">
/**
 * PillarCard Component
 * 
 * Displays a single evaluation pillar with score and details.
 */
import { computed } from 'vue';
import ScoreGauge from './ScoreGauge.vue';

const props = defineProps<{
  name: string;
  icon: string;
  color: string;
  score: number;
  details?: Record<string, any>;
}>();

const riskLevel = computed(() => {
  if (props.score >= 80) return 'low';
  if (props.score >= 60) return 'medium';
  if (props.score >= 40) return 'high';
  return 'critical';
});
</script>

<template>
  <div class="pillar-card" :style="{ '--pillar-color': color }">
    <div class="pillar-header">
      <div class="pillar-icon">
        <i :class="['icon', icon]" />
      </div>
      <div class="pillar-title">
        <h4>{{ name }}</h4>
        <span :class="['risk-level', riskLevel]">{{ riskLevel }} risk</span>
      </div>
      <div class="pillar-score">
        <ScoreGauge :score="score" :size="60" />
      </div>
    </div>
    
    <div class="pillar-details" v-if="details">
      <div 
        v-for="(value, key) in details" 
        :key="key"
        class="detail-row"
      >
        <span class="detail-label">{{ key }}</span>
        <span class="detail-value">
          {{ typeof value === 'number' ? (value * 100).toFixed(1) + '%' : value }}
        </span>
      </div>
    </div>
    
    <div class="pillar-progress">
      <div 
        class="progress-bar"
        :style="{ width: `${score}%`, backgroundColor: color }"
      />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.pillar-card {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 15px;
  border-left: 4px solid var(--pillar-color);
}

.pillar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.pillar-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--body-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  
  i {
    font-size: 20px;
    color: var(--pillar-color);
  }
}

.pillar-title {
  flex: 1;
  
  h4 {
    margin: 0 0 3px 0;
    font-size: 15px;
  }
  
  .risk-level {
    font-size: 11px;
    text-transform: uppercase;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    
    &.low {
      background: rgba(16, 185, 129, 0.1);
      color: #10B981;
    }
    
    &.medium {
      background: rgba(245, 158, 11, 0.1);
      color: #F59E0B;
    }
    
    &.high {
      background: rgba(239, 68, 68, 0.1);
      color: #EF4444;
    }
    
    &.critical {
      background: rgba(127, 29, 29, 0.1);
      color: #7F1D1D;
    }
  }
}

.pillar-details {
  margin-bottom: 12px;
  
  .detail-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    font-size: 13px;
    border-bottom: 1px solid var(--border);
    
    &:last-child {
      border-bottom: none;
    }
    
    .detail-label {
      color: var(--body-text);
      opacity: 0.8;
      text-transform: capitalize;
    }
    
    .detail-value {
      font-weight: 600;
    }
  }
}

.pillar-progress {
  height: 4px;
  background: var(--disabled-bg);
  border-radius: 2px;
  overflow: hidden;
  
  .progress-bar {
    height: 100%;
    border-radius: 2px;
    transition: width 0.5s ease;
  }
}
</style>
