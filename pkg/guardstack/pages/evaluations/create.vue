<script setup lang="ts">
/**
 * Create Evaluation Page
 * 
 * Form for creating new model evaluations with configuration options.
 */
import { computed, ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useModelsStore } from '../../store/models';
import { useEvaluationsStore } from '../../store/evaluations';

const router = useRouter();
const modelsStore = useModelsStore();
const evaluationsStore = useEvaluationsStore();

const loading = ref(false);
const currentStep = ref(1);

// Form state
const form = reactive({
  model_id: '',
  evaluation_type: 'predictive' as 'predictive' | 'genai' | 'spm' | 'agentic',
  name: '',
  description: '',
  // Predictive options
  predictive_pillars: [
    'fairness', 'explainability', 'robustness', 'transparency',
    'privacy', 'accountability', 'safety', 'human_oversight'
  ],
  dataset_path: '',
  // GenAI options
  genai_pillars: ['content_safety', 'prompt_injection', 'hallucination', 'bias_toxicity'],
  include_garak: true,
  garak_probes: [] as string[],
  // SPM options
  scan_types: ['model_artifacts', 'dependencies', 'configurations', 'infrastructure'],
  // Agentic options
  scenarios: [] as string[],
  sandbox_enabled: true,
  // Scheduling
  schedule_type: 'now' as 'now' | 'scheduled' | 'recurring',
  scheduled_time: '',
  recurring_cron: '',
});

const evaluationTypes = [
  {
    id: 'predictive',
    name: 'Predictive ML',
    icon: 'icon-cpu',
    description: '8-pillar evaluation for traditional ML models',
  },
  {
    id: 'genai',
    name: 'Generative AI',
    icon: 'icon-message-square',
    description: '4-pillar evaluation with Garak security probes',
  },
  {
    id: 'spm',
    name: 'Security Posture',
    icon: 'icon-shield',
    description: 'Security scanning of model artifacts and infrastructure',
  },
  {
    id: 'agentic',
    name: 'Agentic AI',
    icon: 'icon-zap',
    description: 'Sandboxed evaluation of autonomous agents',
  },
];

const predictivePillars = [
  { id: 'fairness', name: 'Fairness', description: 'Bias and discrimination analysis' },
  { id: 'explainability', name: 'Explainability', description: 'Model interpretability' },
  { id: 'robustness', name: 'Robustness', description: 'Adversarial resistance' },
  { id: 'transparency', name: 'Transparency', description: 'Model documentation' },
  { id: 'privacy', name: 'Privacy', description: 'Data protection measures' },
  { id: 'accountability', name: 'Accountability', description: 'Audit trails' },
  { id: 'safety', name: 'Safety', description: 'Operational safety' },
  { id: 'human_oversight', name: 'Human Oversight', description: 'Human-in-the-loop' },
];

const genaiPillars = [
  { id: 'content_safety', name: 'Content Safety', description: 'Harmful content detection' },
  { id: 'prompt_injection', name: 'Prompt Injection', description: 'Injection attack resistance' },
  { id: 'hallucination', name: 'Hallucination', description: 'Factual accuracy' },
  { id: 'bias_toxicity', name: 'Bias & Toxicity', description: 'Harmful bias detection' },
];

const garakProbeCategories = [
  { id: 'dan', name: 'DAN Jailbreaks' },
  { id: 'encoding', name: 'Encoding Attacks' },
  { id: 'glitch', name: 'Glitch Tokens' },
  { id: 'knownbadsignatures', name: 'Known Bad Signatures' },
  { id: 'misleading', name: 'Misleading Prompts' },
  { id: 'packagehallucination', name: 'Package Hallucination' },
  { id: 'promptinject', name: 'Prompt Injection' },
  { id: 'realtoxicityprompts', name: 'Toxicity Prompts' },
];

const spmScanTypes = [
  { id: 'model_artifacts', name: 'Model Artifacts', description: 'Scan model files for vulnerabilities' },
  { id: 'dependencies', name: 'Dependencies', description: 'Dependency vulnerability scanning' },
  { id: 'configurations', name: 'Configurations', description: 'Configuration security audit' },
  { id: 'infrastructure', name: 'Infrastructure', description: 'Infrastructure security check' },
  { id: 'secrets', name: 'Secrets', description: 'Secret detection and management' },
];

const agenticScenarios = [
  { id: 'file_access', name: 'File System Access', risk: 'medium' },
  { id: 'network_requests', name: 'Network Requests', risk: 'high' },
  { id: 'code_execution', name: 'Code Execution', risk: 'critical' },
  { id: 'data_exfiltration', name: 'Data Exfiltration', risk: 'critical' },
  { id: 'resource_consumption', name: 'Resource Consumption', risk: 'medium' },
  { id: 'loop_detection', name: 'Infinite Loop Detection', risk: 'high' },
  { id: 'permission_escalation', name: 'Permission Escalation', risk: 'critical' },
];

const models = computed(() => modelsStore.models);
const selectedModel = computed(() => models.value.find(m => m.id === form.model_id));

const totalSteps = computed(() => {
  return 4; // Type -> Model -> Options -> Review
});

const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1:
      return !!form.evaluation_type;
    case 2:
      return !!form.model_id;
    case 3:
      return validateOptions();
    default:
      return true;
  }
});

function validateOptions(): boolean {
  switch (form.evaluation_type) {
    case 'predictive':
      return form.predictive_pillars.length > 0;
    case 'genai':
      return form.genai_pillars.length > 0;
    case 'spm':
      return form.scan_types.length > 0;
    case 'agentic':
      return form.scenarios.length > 0;
    default:
      return false;
  }
}

function nextStep() {
  if (canProceed.value && currentStep.value < totalSteps.value) {
    currentStep.value++;
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--;
  }
}

function togglePillar(list: string[], id: string) {
  const idx = list.indexOf(id);
  if (idx === -1) {
    list.push(id);
  } else {
    list.splice(idx, 1);
  }
}

async function submitEvaluation() {
  loading.value = true;
  
  try {
    const payload: any = {
      model_id: form.model_id,
      evaluation_type: form.evaluation_type,
      name: form.name || `${form.evaluation_type} evaluation`,
      description: form.description,
    };
    
    switch (form.evaluation_type) {
      case 'predictive':
        payload.pillars = form.predictive_pillars;
        payload.dataset_path = form.dataset_path;
        break;
      case 'genai':
        payload.pillars = form.genai_pillars;
        payload.include_garak = form.include_garak;
        payload.garak_probes = form.garak_probes;
        break;
      case 'spm':
        payload.scan_types = form.scan_types;
        break;
      case 'agentic':
        payload.scenarios = form.scenarios;
        payload.sandbox_enabled = form.sandbox_enabled;
        break;
    }
    
    if (form.schedule_type === 'scheduled') {
      payload.scheduled_time = form.scheduled_time;
    } else if (form.schedule_type === 'recurring') {
      payload.recurring_cron = form.recurring_cron;
    }
    
    const evaluation = await evaluationsStore.startEvaluation(payload);
    router.push(`/c/local/guardstack/evaluations/${evaluation.id}`);
  } catch (error) {
    console.error('Failed to start evaluation:', error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="create-evaluation-page">
    <header class="page-header">
      <h1>Create Evaluation</h1>
      <p>Configure and run a new model evaluation</p>
    </header>
    
    <!-- Progress Steps -->
    <div class="step-progress">
      <div 
        v-for="step in totalSteps" 
        :key="step"
        :class="['step', { active: currentStep === step, completed: currentStep > step }]"
      >
        <div class="step-number">{{ step }}</div>
        <span class="step-label">
          {{ step === 1 ? 'Type' : step === 2 ? 'Model' : step === 3 ? 'Options' : 'Review' }}
        </span>
      </div>
    </div>
    
    <div class="step-content">
      <!-- Step 1: Select Evaluation Type -->
      <div v-if="currentStep === 1" class="step-panel">
        <h2>Select Evaluation Type</h2>
        <p class="step-description">Choose the type of evaluation based on your model</p>
        
        <div class="type-grid">
          <div 
            v-for="type in evaluationTypes"
            :key="type.id"
            :class="['type-card', { selected: form.evaluation_type === type.id }]"
            @click="form.evaluation_type = type.id as any"
          >
            <i :class="['icon', type.icon]" />
            <h3>{{ type.name }}</h3>
            <p>{{ type.description }}</p>
            <div class="check-indicator" v-if="form.evaluation_type === type.id">
              <i class="icon icon-check" />
            </div>
          </div>
        </div>
      </div>
      
      <!-- Step 2: Select Model -->
      <div v-if="currentStep === 2" class="step-panel">
        <h2>Select Model</h2>
        <p class="step-description">Choose the model to evaluate</p>
        
        <div class="model-search">
          <input type="text" placeholder="Search models..." class="search-input" />
        </div>
        
        <div class="model-list">
          <div 
            v-for="model in models"
            :key="model.id"
            :class="['model-card', { selected: form.model_id === model.id }]"
            @click="form.model_id = model.id"
          >
            <div class="model-icon">
              <i class="icon icon-box" />
            </div>
            <div class="model-info">
              <h4>{{ model.name }}</h4>
              <p>{{ model.type }} · {{ model.version || 'v1.0' }}</p>
            </div>
            <div class="model-select">
              <i v-if="form.model_id === model.id" class="icon icon-check-circle" />
            </div>
          </div>
        </div>
        
        <div class="form-group">
          <label>Evaluation Name (optional)</label>
          <input v-model="form.name" type="text" placeholder="Enter evaluation name" />
        </div>
        
        <div class="form-group">
          <label>Description (optional)</label>
          <textarea v-model="form.description" placeholder="Describe the purpose of this evaluation" rows="3" />
        </div>
      </div>
      
      <!-- Step 3: Evaluation Options -->
      <div v-if="currentStep === 3" class="step-panel">
        <h2>Evaluation Options</h2>
        
        <!-- Predictive Options -->
        <div v-if="form.evaluation_type === 'predictive'" class="options-section">
          <h3>Select Pillars to Evaluate</h3>
          <div class="pillar-grid">
            <div 
              v-for="pillar in predictivePillars"
              :key="pillar.id"
              :class="['pillar-option', { selected: form.predictive_pillars.includes(pillar.id) }]"
              @click="togglePillar(form.predictive_pillars, pillar.id)"
            >
              <div class="pillar-check">
                <i v-if="form.predictive_pillars.includes(pillar.id)" class="icon icon-check" />
              </div>
              <div class="pillar-content">
                <h4>{{ pillar.name }}</h4>
                <p>{{ pillar.description }}</p>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label>Dataset Path</label>
            <input v-model="form.dataset_path" type="text" placeholder="s3://bucket/dataset.csv or local path" />
          </div>
        </div>
        
        <!-- GenAI Options -->
        <div v-if="form.evaluation_type === 'genai'" class="options-section">
          <h3>Select Pillars to Evaluate</h3>
          <div class="pillar-grid">
            <div 
              v-for="pillar in genaiPillars"
              :key="pillar.id"
              :class="['pillar-option', { selected: form.genai_pillars.includes(pillar.id) }]"
              @click="togglePillar(form.genai_pillars, pillar.id)"
            >
              <div class="pillar-check">
                <i v-if="form.genai_pillars.includes(pillar.id)" class="icon icon-check" />
              </div>
              <div class="pillar-content">
                <h4>{{ pillar.name }}</h4>
                <p>{{ pillar.description }}</p>
              </div>
            </div>
          </div>
          
          <div class="form-group checkbox-group">
            <label>
              <input type="checkbox" v-model="form.include_garak" />
              Include Garak Security Probes
            </label>
          </div>
          
          <div v-if="form.include_garak" class="garak-probes">
            <h4>Select Garak Probe Categories</h4>
            <div class="probe-grid">
              <div 
                v-for="probe in garakProbeCategories"
                :key="probe.id"
                :class="['probe-option', { selected: form.garak_probes.includes(probe.id) }]"
                @click="togglePillar(form.garak_probes, probe.id)"
              >
                <i v-if="form.garak_probes.includes(probe.id)" class="icon icon-check" />
                {{ probe.name }}
              </div>
            </div>
          </div>
        </div>
        
        <!-- SPM Options -->
        <div v-if="form.evaluation_type === 'spm'" class="options-section">
          <h3>Select Scan Types</h3>
          <div class="pillar-grid">
            <div 
              v-for="scan in spmScanTypes"
              :key="scan.id"
              :class="['pillar-option', { selected: form.scan_types.includes(scan.id) }]"
              @click="togglePillar(form.scan_types, scan.id)"
            >
              <div class="pillar-check">
                <i v-if="form.scan_types.includes(scan.id)" class="icon icon-check" />
              </div>
              <div class="pillar-content">
                <h4>{{ scan.name }}</h4>
                <p>{{ scan.description }}</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Agentic Options -->
        <div v-if="form.evaluation_type === 'agentic'" class="options-section">
          <h3>Select Test Scenarios</h3>
          <div class="scenario-list">
            <div 
              v-for="scenario in agenticScenarios"
              :key="scenario.id"
              :class="['scenario-option', { selected: form.scenarios.includes(scenario.id) }]"
              @click="togglePillar(form.scenarios, scenario.id)"
            >
              <div class="scenario-check">
                <i v-if="form.scenarios.includes(scenario.id)" class="icon icon-check" />
              </div>
              <span class="scenario-name">{{ scenario.name }}</span>
              <span :class="['risk-badge', scenario.risk]">{{ scenario.risk }}</span>
            </div>
          </div>
          
          <div class="form-group checkbox-group">
            <label>
              <input type="checkbox" v-model="form.sandbox_enabled" />
              Enable Sandbox Environment (recommended)
            </label>
          </div>
        </div>
        
        <!-- Scheduling -->
        <div class="scheduling-section">
          <h3>Schedule</h3>
          <div class="schedule-options">
            <label :class="['schedule-option', { selected: form.schedule_type === 'now' }]">
              <input type="radio" v-model="form.schedule_type" value="now" />
              <span>Run Now</span>
            </label>
            <label :class="['schedule-option', { selected: form.schedule_type === 'scheduled' }]">
              <input type="radio" v-model="form.schedule_type" value="scheduled" />
              <span>Schedule for Later</span>
            </label>
            <label :class="['schedule-option', { selected: form.schedule_type === 'recurring' }]">
              <input type="radio" v-model="form.schedule_type" value="recurring" />
              <span>Recurring</span>
            </label>
          </div>
          
          <div v-if="form.schedule_type === 'scheduled'" class="form-group">
            <label>Scheduled Time</label>
            <input type="datetime-local" v-model="form.scheduled_time" />
          </div>
          
          <div v-if="form.schedule_type === 'recurring'" class="form-group">
            <label>Cron Expression</label>
            <input type="text" v-model="form.recurring_cron" placeholder="0 0 * * *" />
          </div>
        </div>
      </div>
      
      <!-- Step 4: Review -->
      <div v-if="currentStep === 4" class="step-panel">
        <h2>Review & Submit</h2>
        
        <div class="review-section">
          <div class="review-group">
            <h4>Evaluation Type</h4>
            <p>{{ evaluationTypes.find(t => t.id === form.evaluation_type)?.name }}</p>
          </div>
          
          <div class="review-group">
            <h4>Model</h4>
            <p>{{ selectedModel?.name }}</p>
          </div>
          
          <div class="review-group" v-if="form.name">
            <h4>Name</h4>
            <p>{{ form.name }}</p>
          </div>
          
          <div class="review-group" v-if="form.evaluation_type === 'predictive'">
            <h4>Pillars</h4>
            <div class="tag-list">
              <span v-for="p in form.predictive_pillars" :key="p" class="tag">{{ p }}</span>
            </div>
          </div>
          
          <div class="review-group" v-if="form.evaluation_type === 'genai'">
            <h4>Pillars</h4>
            <div class="tag-list">
              <span v-for="p in form.genai_pillars" :key="p" class="tag">{{ p }}</span>
            </div>
            <p v-if="form.include_garak">+ Garak Security Probes</p>
          </div>
          
          <div class="review-group" v-if="form.evaluation_type === 'spm'">
            <h4>Scan Types</h4>
            <div class="tag-list">
              <span v-for="s in form.scan_types" :key="s" class="tag">{{ s }}</span>
            </div>
          </div>
          
          <div class="review-group" v-if="form.evaluation_type === 'agentic'">
            <h4>Scenarios</h4>
            <div class="tag-list">
              <span v-for="s in form.scenarios" :key="s" class="tag">{{ s }}</span>
            </div>
            <p v-if="form.sandbox_enabled">Sandbox Enabled</p>
          </div>
          
          <div class="review-group">
            <h4>Schedule</h4>
            <p>{{ form.schedule_type === 'now' ? 'Run Immediately' : form.schedule_type === 'scheduled' ? `Scheduled: ${form.scheduled_time}` : `Recurring: ${form.recurring_cron}` }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Navigation Buttons -->
    <div class="step-navigation">
      <button 
        class="btn" 
        @click="prevStep" 
        :disabled="currentStep === 1"
      >
        <i class="icon icon-chevron-left" />
        Back
      </button>
      
      <div class="nav-spacer" />
      
      <button 
        v-if="currentStep < totalSteps"
        class="btn role-primary" 
        @click="nextStep"
        :disabled="!canProceed"
      >
        Continue
        <i class="icon icon-chevron-right" />
      </button>
      
      <button 
        v-else
        class="btn role-primary" 
        @click="submitEvaluation"
        :disabled="loading"
      >
        <i v-if="loading" class="icon icon-spinner icon-spin" />
        <template v-else>
          <i class="icon icon-play" />
          Start Evaluation
        </template>
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.create-evaluation-page {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
  
  h1 { margin: 0 0 5px 0; }
  p { color: var(--body-text); opacity: 0.7; margin: 0; }
}

.step-progress {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 15px;
    left: 30px;
    right: 30px;
    height: 2px;
    background: var(--border);
    z-index: 0;
  }
  
  .step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    z-index: 1;
    
    .step-number {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--box-bg);
      border: 2px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 600;
    }
    
    .step-label {
      font-size: 12px;
      color: var(--body-text);
    }
    
    &.active .step-number {
      background: var(--link);
      border-color: var(--link);
      color: white;
    }
    
    &.completed .step-number {
      background: #10B981;
      border-color: #10B981;
      color: white;
    }
  }
}

.step-content {
  background: var(--box-bg);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  padding: 30px;
  margin-bottom: 20px;
}

.step-panel {
  h2 { margin: 0 0 10px 0; }
  .step-description { color: var(--body-text); opacity: 0.8; margin-bottom: 20px; }
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.type-card {
  padding: 20px;
  border: 2px solid var(--border);
  border-radius: var(--border-radius);
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
  
  &:hover {
    border-color: var(--link);
  }
  
  &.selected {
    border-color: var(--link);
    background: rgba(59, 130, 246, 0.05);
  }
  
  i {
    font-size: 32px;
    color: var(--link);
    margin-bottom: 10px;
  }
  
  h3 { margin: 0 0 5px 0; }
  p { margin: 0; font-size: 13px; color: var(--body-text); opacity: 0.8; }
  
  .check-indicator {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: var(--link);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.model-search {
  margin-bottom: 15px;
  
  .search-input {
    width: 100%;
    padding: 10px 15px;
    border: 1px solid var(--border);
    border-radius: var(--border-radius);
    background: var(--body-bg);
    color: var(--body-text);
  }
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
  max-height: 300px;
  overflow-y: auto;
}

.model-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover { border-color: var(--link); }
  &.selected { border-color: var(--link); background: rgba(59, 130, 246, 0.05); }
  
  .model-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    background: var(--body-bg);
    display: flex;
    align-items: center;
    justify-content: center;
    
    i { font-size: 20px; }
  }
  
  .model-info {
    flex: 1;
    
    h4 { margin: 0 0 3px 0; }
    p { margin: 0; font-size: 12px; color: var(--body-text); opacity: 0.7; }
  }
  
  .model-select i {
    color: var(--link);
    font-size: 20px;
  }
}

.form-group {
  margin-bottom: 15px;
  
  label {
    display: block;
    margin-bottom: 5px;
    font-weight: 500;
  }
  
  input, textarea {
    width: 100%;
    padding: 10px 15px;
    border: 1px solid var(--border);
    border-radius: var(--border-radius);
    background: var(--body-bg);
    color: var(--body-text);
    
    &:focus {
      border-color: var(--link);
      outline: none;
    }
  }
  
  &.checkbox-group label {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
  }
}

.pillar-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.pillar-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 15px;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover { border-color: var(--link); }
  &.selected { border-color: var(--link); background: rgba(59, 130, 246, 0.05); }
  
  .pillar-check {
    width: 20px;
    height: 20px;
    border: 2px solid var(--border);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    
    i { font-size: 12px; color: var(--link); }
  }
  
  &.selected .pillar-check {
    background: var(--link);
    border-color: var(--link);
    
    i { color: white; }
  }
  
  .pillar-content {
    h4 { margin: 0 0 3px 0; font-size: 14px; }
    p { margin: 0; font-size: 12px; color: var(--body-text); opacity: 0.7; }
  }
}

.probe-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.probe-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 15px;
  border: 1px solid var(--border);
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  
  &:hover { border-color: var(--link); }
  &.selected { border-color: var(--link); background: var(--link); color: white; }
  
  i { font-size: 12px; }
}

.scenario-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.scenario-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover { border-color: var(--link); }
  &.selected { border-color: var(--link); background: rgba(59, 130, 246, 0.05); }
  
  .scenario-check {
    width: 20px;
    height: 20px;
    border: 2px solid var(--border);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    
    i { font-size: 12px; }
  }
  
  &.selected .scenario-check {
    background: var(--link);
    border-color: var(--link);
    color: white;
  }
  
  .scenario-name { flex: 1; }
  
  .risk-badge {
    padding: 3px 10px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    
    &.critical { background: rgba(127, 29, 29, 0.1); color: #7F1D1D; }
    &.high { background: rgba(239, 68, 68, 0.1); color: #EF4444; }
    &.medium { background: rgba(245, 158, 11, 0.1); color: #F59E0B; }
    &.low { background: rgba(16, 185, 129, 0.1); color: #10B981; }
  }
}

.scheduling-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  
  h3 { margin: 0 0 15px 0; }
}

.schedule-options {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.schedule-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  cursor: pointer;
  
  &.selected {
    border-color: var(--link);
    background: rgba(59, 130, 246, 0.05);
  }
  
  input { display: none; }
}

.review-section {
  .review-group {
    margin-bottom: 20px;
    
    h4 {
      margin: 0 0 5px 0;
      color: var(--body-text);
      opacity: 0.7;
      font-size: 12px;
      text-transform: uppercase;
    }
    
    p { margin: 0; font-size: 16px; }
  }
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  
  .tag {
    padding: 5px 12px;
    background: var(--body-bg);
    border: 1px solid var(--border);
    border-radius: 15px;
    font-size: 13px;
    text-transform: capitalize;
  }
}

.step-navigation {
  display: flex;
  align-items: center;
  
  .nav-spacer { flex: 1; }
  
  .btn {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}
</style>
