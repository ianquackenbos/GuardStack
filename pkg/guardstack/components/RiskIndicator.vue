<script setup lang="ts">
/**
 * RiskIndicator Component
 * 
 * Visual indicator for risk levels with color coding and animations.
 */
import { computed } from 'vue';

const props = defineProps<{
  level: 'critical' | 'high' | 'medium' | 'low' | 'none';
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
}>();

const riskConfig = {
  critical: {
    color: '#7F1D1D',
    bgColor: 'rgba(127, 29, 29, 0.1)',
    label: 'Critical',
    icon: 'icon-alert-octagon',
  },
  high: {
    color: '#EF4444',
    bgColor: 'rgba(239, 68, 68, 0.1)',
    label: 'High',
    icon: 'icon-alert-triangle',
  },
  medium: {
    color: '#F59E0B',
    bgColor: 'rgba(245, 158, 11, 0.1)',
    label: 'Medium',
    icon: 'icon-alert-circle',
  },
  low: {
    color: '#10B981',
    bgColor: 'rgba(16, 185, 129, 0.1)',
    label: 'Low',
    icon: 'icon-check-circle',
  },
  none: {
    color: '#6B7280',
    bgColor: 'rgba(107, 114, 128, 0.1)',
    label: 'None',
    icon: 'icon-minus-circle',
  },
};

const config = computed(() => riskConfig[props.level] || riskConfig.none);

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'risk-sm',
    md: 'risk-md',
    lg: 'risk-lg',
  };
  return sizes[props.size || 'md'];
});
</script>

<template>
  <div 
    :class="['risk-indicator', sizeClasses, level, { animated }]"
    :style="{ 
      '--risk-color': config.color,
      '--risk-bg': config.bgColor,
    }"
  >
    <div class="risk-dot" :class="{ pulse: animated && (level === 'critical' || level === 'high') }">
      <i :class="['icon', config.icon]" />
    </div>
    <span v-if="showLabel" class="risk-label">{{ config.label }}</span>
  </div>
</template>

<style lang="scss" scoped>
.risk-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  
  .risk-dot {
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: var(--risk-bg);
    color: var(--risk-color);
    
    i {
      line-height: 1;
    }
    
    &.pulse {
      animation: pulse 2s ease-in-out infinite;
    }
  }
  
  .risk-label {
    font-weight: 600;
    color: var(--risk-color);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  // Size variants
  &.risk-sm {
    .risk-dot {
      width: 20px;
      height: 20px;
      
      i { font-size: 12px; }
    }
    
    .risk-label {
      font-size: 10px;
    }
  }
  
  &.risk-md {
    .risk-dot {
      width: 32px;
      height: 32px;
      
      i { font-size: 16px; }
    }
    
    .risk-label {
      font-size: 12px;
    }
  }
  
  &.risk-lg {
    .risk-dot {
      width: 48px;
      height: 48px;
      
      i { font-size: 24px; }
    }
    
    .risk-label {
      font-size: 14px;
    }
  }
  
  // Level-specific styles
  &.critical {
    .risk-dot {
      box-shadow: 0 0 0 3px rgba(127, 29, 29, 0.2);
    }
  }
  
  &.high {
    .risk-dot {
      box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
    }
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.8;
  }
}
</style>
