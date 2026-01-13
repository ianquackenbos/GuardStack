<script setup lang="ts">
/**
 * EvaluationTimeline Component
 * 
 * Displays a chronological timeline of evaluation runs.
 */
import { computed } from 'vue';

interface Evaluation {
  id: string;
  created_at: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  evaluation_type: string;
  results?: {
    overall_score?: number;
  };
  duration?: number;
}

const props = defineProps<{
  evaluations: Evaluation[];
  showDetails?: boolean;
}>();

const sortedEvaluations = computed(() => {
  return [...props.evaluations].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
});

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getStatusIcon(status: string): string {
  const icons: Record<string, string> = {
    pending: 'icon-clock',
    running: 'icon-loader',
    completed: 'icon-check-circle',
    failed: 'icon-x-circle',
  };
  return icons[status] || 'icon-circle';
}

function getScoreClass(score: number): string {
  if (score >= 80) return 'score-high';
  if (score >= 60) return 'score-medium';
  if (score >= 40) return 'score-low';
  return 'score-critical';
}
</script>

<template>
  <div class="evaluation-timeline">
    <div v-if="sortedEvaluations.length === 0" class="empty-state">
      <i class="icon icon-clock" />
      <p>No evaluations yet</p>
    </div>
    
    <div v-else class="timeline">
      <div 
        v-for="evaluation in sortedEvaluations" 
        :key="evaluation.id"
        :class="['timeline-item', evaluation.status]"
      >
        <div class="timeline-marker">
          <i :class="['icon', getStatusIcon(evaluation.status)]" />
        </div>
        
        <div class="timeline-content">
          <div class="timeline-header">
            <span class="timeline-date">{{ formatDate(evaluation.created_at) }}</span>
            <span class="timeline-time">{{ formatTime(evaluation.created_at) }}</span>
          </div>
          
          <div class="timeline-body">
            <div class="evaluation-info">
              <span class="evaluation-type">{{ evaluation.evaluation_type }}</span>
              <span :class="['status-badge', evaluation.status]">
                {{ evaluation.status }}
              </span>
            </div>
            
            <div v-if="showDetails && evaluation.results?.overall_score !== undefined" class="evaluation-score">
              <span class="score-label">Score:</span>
              <span :class="['score-value', getScoreClass(evaluation.results.overall_score)]">
                {{ evaluation.results.overall_score.toFixed(0) }}%
              </span>
            </div>
            
            <div v-if="showDetails && evaluation.duration" class="evaluation-duration">
              <i class="icon icon-clock" />
              {{ evaluation.duration }}s
            </div>
          </div>
          
          <div v-if="showDetails" class="timeline-actions">
            <router-link :to="`/c/local/guardstack/evaluations/${evaluation.id}`" class="view-link">
              View Details →
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.evaluation-timeline {
  position: relative;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--body-text);
  opacity: 0.7;
  
  i {
    font-size: 32px;
    margin-bottom: 10px;
  }
  
  p {
    margin: 0;
  }
}

.timeline {
  position: relative;
  padding-left: 30px;
  
  &::before {
    content: '';
    position: absolute;
    left: 10px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--border);
  }
}

.timeline-item {
  position: relative;
  padding-bottom: 20px;
  
  &:last-child {
    padding-bottom: 0;
  }
  
  .timeline-marker {
    position: absolute;
    left: -30px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--box-bg);
    border: 2px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1;
    
    i {
      font-size: 12px;
      color: var(--body-text);
    }
  }
  
  &.completed .timeline-marker {
    border-color: #10B981;
    background: rgba(16, 185, 129, 0.1);
    
    i { color: #10B981; }
  }
  
  &.failed .timeline-marker {
    border-color: #EF4444;
    background: rgba(239, 68, 68, 0.1);
    
    i { color: #EF4444; }
  }
  
  &.running .timeline-marker {
    border-color: #3B82F6;
    background: rgba(59, 130, 246, 0.1);
    
    i { 
      color: #3B82F6;
      animation: spin 1s linear infinite;
    }
  }
  
  &.pending .timeline-marker {
    border-color: #F59E0B;
    background: rgba(245, 158, 11, 0.1);
    
    i { color: #F59E0B; }
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.timeline-content {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 15px;
}

.timeline-header {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  
  .timeline-date {
    font-weight: 600;
  }
  
  .timeline-time {
    color: var(--body-text);
    opacity: 0.7;
  }
}

.timeline-body {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
  
  .evaluation-info {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .evaluation-type {
      text-transform: capitalize;
      font-weight: 500;
    }
    
    .status-badge {
      padding: 3px 10px;
      border-radius: 10px;
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 600;
      
      &.completed {
        background: rgba(16, 185, 129, 0.1);
        color: #10B981;
      }
      
      &.failed {
        background: rgba(239, 68, 68, 0.1);
        color: #EF4444;
      }
      
      &.running {
        background: rgba(59, 130, 246, 0.1);
        color: #3B82F6;
      }
      
      &.pending {
        background: rgba(245, 158, 11, 0.1);
        color: #F59E0B;
      }
    }
  }
  
  .evaluation-score {
    display: flex;
    align-items: center;
    gap: 5px;
    
    .score-label {
      color: var(--body-text);
      opacity: 0.7;
    }
    
    .score-value {
      font-weight: 600;
      
      &.score-high { color: #10B981; }
      &.score-medium { color: #F59E0B; }
      &.score-low { color: #EF4444; }
      &.score-critical { color: #7F1D1D; }
    }
  }
  
  .evaluation-duration {
    display: flex;
    align-items: center;
    gap: 5px;
    color: var(--body-text);
    opacity: 0.7;
    font-size: 13px;
    
    i { font-size: 12px; }
  }
}

.timeline-actions {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
  
  .view-link {
    color: var(--link);
    font-size: 13px;
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
