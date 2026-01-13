<script setup lang="ts">
/**
 * SPM (Security Posture Management) Model Detail Page
 * 
 * Displays security scan results for ML infrastructure and artifacts.
 */
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useModelsStore } from '../../../store/models';
import { useEvaluationsStore } from '../../../store/evaluations';
import { StatusBadge, ScoreGauge, FindingsTable } from '../../../components';

const route = useRoute();
const modelsStore = useModelsStore();
const evaluationsStore = useEvaluationsStore();

const modelId = computed(() => route.params.id as string);
const model = computed(() => modelsStore.models.find(m => m.id === modelId.value));
const loading = ref(true);
const activeCategory = ref('all');

// SPM scan categories
const categories = [
  { key: 'all', name: 'All Findings', icon: 'icon-list' },
  { key: 'model_artifacts', name: 'Model Artifacts', icon: 'icon-box' },
  { key: 'dependencies', name: 'Dependencies', icon: 'icon-package' },
  { key: 'configurations', name: 'Configurations', icon: 'icon-settings' },
  { key: 'infrastructure', name: 'Infrastructure', icon: 'icon-server' },
  { key: 'secrets', name: 'Secrets & Credentials', icon: 'icon-key' },
];

// Severity levels
const severityLevels = ['critical', 'high', 'medium', 'low', 'info'];

const latestScan = computed(() => {
  if (!model.value) return null;
  return evaluationsStore.getLatestEvaluation(modelId.value);
});

const scanResults = computed(() => {
  if (!latestScan.value?.results) return null;
  return latestScan.value.results;
});

const findings = computed(() => {
  if (!scanResults.value?.findings) return [];
  const allFindings = scanResults.value.findings;
  
  if (activeCategory.value === 'all') {
    return allFindings;
  }
  
  return allFindings.filter((f: any) => f.category === activeCategory.value);
});

const findingsBySeverity = computed(() => {
  const counts: Record<string, number> = {};
  severityLevels.forEach(s => counts[s] = 0);
  
  if (scanResults.value?.findings) {
    scanResults.value.findings.forEach((f: any) => {
      if (counts[f.severity] !== undefined) {
        counts[f.severity]++;
      }
    });
  }
  
  return counts;
});

const securityScore = computed(() => {
  if (!scanResults.value) return 100;
  return scanResults.value.security_score || 100;
});

const inventory = computed(() => {
  if (!scanResults.value?.inventory) return null;
  return scanResults.value.inventory;
});

onMounted(async () => {
  loading.value = true;
  await Promise.all([
    modelsStore.fetchModel(modelId.value),
    evaluationsStore.fetchModelEvaluations(modelId.value),
  ]);
  loading.value = false;
});

function startScan() {
  evaluationsStore.startEvaluation({
    model_id: modelId.value,
    evaluation_type: 'spm',
    scan_types: categories.filter(c => c.key !== 'all').map(c => c.key),
  });
}

function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: '#7F1D1D',
    high: '#EF4444',
    medium: '#F59E0B',
    low: '#3B82F6',
    info: '#6B7280',
  };
  return colors[severity] || '#6B7280';
}
</script>

<template>
  <div class="spm-model-view">
    <header class="model-header">
      <div class="model-info">
        <h1>{{ model?.name || 'Loading...' }}</h1>
        <p class="model-type">Security Posture Management</p>
        <StatusBadge v-if="model" :status="model.status" />
      </div>
      <div class="model-actions">
        <button class="btn role-primary" @click="startScan">
          <i class="icon icon-scan" />
          Run Security Scan
        </button>
      </div>
    </header>

    <div v-if="loading" class="loading-state">
      <i class="icon icon-spinner icon-spin" />
      Loading security data...
    </div>

    <template v-else>
      <!-- Security Overview -->
      <section class="security-overview">
        <div class="score-panel">
          <h2>Security Score</h2>
          <ScoreGauge :score="securityScore" :size="160" />
          <p class="last-scan" v-if="latestScan">
            Last scan: {{ new Date(latestScan.created_at).toLocaleString() }}
          </p>
        </div>
        
        <div class="severity-breakdown">
          <h3>Findings by Severity</h3>
          <div class="severity-bars">
            <div 
              v-for="severity in severityLevels" 
              :key="severity"
              class="severity-row"
            >
              <span class="severity-label" :style="{ color: getSeverityColor(severity) }">
                {{ severity.toUpperCase() }}
              </span>
              <div class="severity-bar-container">
                <div 
                  class="severity-bar"
                  :style="{ 
                    width: `${Math.min((findingsBySeverity[severity] / Math.max(...Object.values(findingsBySeverity), 1)) * 100, 100)}%`,
                    backgroundColor: getSeverityColor(severity)
                  }"
                />
              </div>
              <span class="severity-count">{{ findingsBySeverity[severity] }}</span>
            </div>
          </div>
        </div>
        
        <div class="quick-actions">
          <h3>Quick Actions</h3>
          <div class="action-buttons">
            <button class="action-btn">
              <i class="icon icon-download" />
              Export Report
            </button>
            <button class="action-btn">
              <i class="icon icon-code" />
              View SBOM
            </button>
            <button class="action-btn">
              <i class="icon icon-shield" />
              Compliance Check
            </button>
          </div>
        </div>
      </section>

      <!-- Category Tabs -->
      <nav class="category-tabs">
        <button
          v-for="cat in categories"
          :key="cat.key"
          :class="['category-tab', { active: activeCategory === cat.key }]"
          @click="activeCategory = cat.key"
        >
          <i :class="['icon', cat.icon]" />
          {{ cat.name }}
          <span class="count" v-if="cat.key !== 'all'">
            {{ scanResults?.findings?.filter((f: any) => f.category === cat.key).length || 0 }}
          </span>
          <span class="count" v-else>
            {{ scanResults?.findings?.length || 0 }}
          </span>
        </button>
      </nav>

      <!-- Findings List -->
      <section class="findings-section">
        <div v-if="findings.length === 0" class="no-findings">
          <i class="icon icon-check-circle" />
          <p>No security findings in this category</p>
        </div>
        
        <div v-else class="findings-list">
          <div 
            v-for="finding in findings" 
            :key="finding.id"
            :class="['finding-card', finding.severity]"
          >
            <div class="finding-header">
              <span :class="['severity-badge', finding.severity]">
                {{ finding.severity }}
              </span>
              <h4>{{ finding.title }}</h4>
            </div>
            
            <p class="finding-description">{{ finding.description }}</p>
            
            <div class="finding-meta">
              <span class="meta-item">
                <i class="icon icon-folder" />
                {{ finding.category }}
              </span>
              <span class="meta-item">
                <i class="icon icon-file" />
                {{ finding.location || 'N/A' }}
              </span>
              <span class="meta-item" v-if="finding.cve">
                <i class="icon icon-alert-triangle" />
                {{ finding.cve }}
              </span>
            </div>
            
            <div class="finding-remediation" v-if="finding.remediation">
              <h5>Remediation</h5>
              <p>{{ finding.remediation }}</p>
            </div>
            
            <div class="finding-actions">
              <button class="btn btn-sm">View Details</button>
              <button class="btn btn-sm">Mark Resolved</button>
              <button class="btn btn-sm">Ignore</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Inventory Section -->
      <section class="inventory-section" v-if="inventory">
        <h2>Asset Inventory</h2>
        <div class="inventory-grid">
          <div class="inventory-card">
            <h4>Model Files</h4>
            <ul>
              <li v-for="file in inventory.model_files?.slice(0, 5)" :key="file.path">
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ file.size }}</span>
              </li>
            </ul>
          </div>
          
          <div class="inventory-card">
            <h4>Dependencies</h4>
            <div class="dep-stats">
              <span>Total: {{ inventory.dependencies?.total || 0 }}</span>
              <span>Direct: {{ inventory.dependencies?.direct || 0 }}</span>
              <span>Transitive: {{ inventory.dependencies?.transitive || 0 }}</span>
            </div>
            <div class="vulnerable-deps" v-if="inventory.dependencies?.vulnerable > 0">
              <span class="warning">
                <i class="icon icon-alert-triangle" />
                {{ inventory.dependencies.vulnerable }} vulnerable
              </span>
            </div>
          </div>
          
          <div class="inventory-card">
            <h4>Configurations</h4>
            <ul>
              <li v-for="config in inventory.configurations?.slice(0, 5)" :key="config.path">
                <span class="config-name">{{ config.name }}</span>
                <span :class="['config-status', config.secure ? 'secure' : 'insecure']">
                  {{ config.secure ? 'Secure' : 'Review' }}
                </span>
              </li>
            </ul>
          </div>
          
          <div class="inventory-card">
            <h4>Infrastructure</h4>
            <div class="infra-items">
              <div v-for="item in inventory.infrastructure" :key="item.id" class="infra-item">
                <i :class="['icon', item.icon || 'icon-server']" />
                <span>{{ item.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.spm-model-view {
  padding: 20px;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
  
  .model-info {
    h1 {
      margin: 0 0 5px 0;
      font-size: 24px;
    }
    
    .model-type {
      color: var(--body-text);
      margin: 0 0 10px 0;
      opacity: 0.7;
    }
  }
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--body-text);
}

.security-overview {
  display: grid;
  grid-template-columns: 200px 1fr 250px;
  gap: 20px;
  margin-bottom: 30px;
  
  @media (max-width: 1000px) {
    grid-template-columns: 1fr;
  }
}

.score-panel {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
  text-align: center;
  
  h2 {
    margin: 0 0 15px 0;
    font-size: 16px;
  }
  
  .last-scan {
    margin-top: 15px;
    font-size: 12px;
    color: var(--body-text);
    opacity: 0.7;
  }
}

.severity-breakdown {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
  
  h3 {
    margin: 0 0 20px 0;
  }
  
  .severity-row {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    
    .severity-label {
      width: 80px;
      font-size: 11px;
      font-weight: 600;
    }
    
    .severity-bar-container {
      flex: 1;
      height: 8px;
      background: var(--disabled-bg);
      border-radius: 4px;
      margin: 0 15px;
      overflow: hidden;
      
      .severity-bar {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
      }
    }
    
    .severity-count {
      width: 40px;
      text-align: right;
      font-weight: 600;
    }
  }
}

.quick-actions {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
  
  h3 {
    margin: 0 0 15px 0;
  }
  
  .action-buttons {
    display: flex;
    flex-direction: column;
    gap: 10px;
    
    .action-btn {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 15px;
      background: var(--body-bg);
      border: 1px solid var(--border);
      border-radius: var(--border-radius);
      color: var(--body-text);
      cursor: pointer;
      transition: all 0.2s;
      
      &:hover {
        background: var(--accent-btn);
        color: white;
      }
    }
  }
}

.category-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  
  .category-tab {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 15px;
    background: var(--box-bg);
    border: 1px solid var(--border);
    border-radius: var(--border-radius);
    color: var(--body-text);
    cursor: pointer;
    transition: all 0.2s;
    
    &:hover {
      border-color: var(--link);
    }
    
    &.active {
      background: var(--link);
      color: white;
      border-color: var(--link);
    }
    
    .count {
      background: rgba(255,255,255,0.2);
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 12px;
    }
  }
}

.findings-section {
  margin-bottom: 30px;
}

.no-findings {
  text-align: center;
  padding: 60px;
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  
  i {
    font-size: 48px;
    color: #10B981;
  }
  
  p {
    margin-top: 15px;
    color: var(--body-text);
  }
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.finding-card {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
  border-left: 4px solid;
  
  &.critical { border-left-color: #7F1D1D; }
  &.high { border-left-color: #EF4444; }
  &.medium { border-left-color: #F59E0B; }
  &.low { border-left-color: #3B82F6; }
  &.info { border-left-color: #6B7280; }
  
  .finding-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 10px;
    
    h4 {
      margin: 0;
      flex: 1;
    }
  }
  
  .severity-badge {
    padding: 3px 10px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: white;
    
    &.critical { background: #7F1D1D; }
    &.high { background: #EF4444; }
    &.medium { background: #F59E0B; }
    &.low { background: #3B82F6; }
    &.info { background: #6B7280; }
  }
  
  .finding-description {
    color: var(--body-text);
    margin-bottom: 15px;
  }
  
  .finding-meta {
    display: flex;
    gap: 20px;
    margin-bottom: 15px;
    
    .meta-item {
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 13px;
      color: var(--body-text);
      opacity: 0.8;
    }
  }
  
  .finding-remediation {
    background: var(--body-bg);
    padding: 15px;
    border-radius: var(--border-radius);
    margin-bottom: 15px;
    
    h5 {
      margin: 0 0 10px 0;
      color: var(--link);
    }
    
    p {
      margin: 0;
      font-size: 14px;
    }
  }
  
  .finding-actions {
    display: flex;
    gap: 10px;
    
    .btn-sm {
      padding: 5px 12px;
      font-size: 12px;
    }
  }
}

.inventory-section {
  h2 {
    margin: 0 0 20px 0;
  }
}

.inventory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
}

.inventory-card {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 20px;
  
  h4 {
    margin: 0 0 15px 0;
    font-size: 14px;
    color: var(--link);
  }
  
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    
    li {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
      
      &:last-child {
        border-bottom: none;
      }
      
      .file-size {
        color: var(--body-text);
        opacity: 0.7;
      }
      
      .config-status {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 4px;
        
        &.secure {
          background: rgba(16, 185, 129, 0.1);
          color: #10B981;
        }
        
        &.insecure {
          background: rgba(239, 68, 68, 0.1);
          color: #EF4444;
        }
      }
    }
  }
  
  .dep-stats {
    display: flex;
    flex-direction: column;
    gap: 5px;
    margin-bottom: 10px;
    
    span {
      font-size: 14px;
    }
  }
  
  .vulnerable-deps {
    .warning {
      display: flex;
      align-items: center;
      gap: 5px;
      color: #EF4444;
      font-size: 14px;
    }
  }
  
  .infra-items {
    display: flex;
    flex-direction: column;
    gap: 10px;
    
    .infra-item {
      display: flex;
      align-items: center;
      gap: 10px;
    }
  }
}
</style>
