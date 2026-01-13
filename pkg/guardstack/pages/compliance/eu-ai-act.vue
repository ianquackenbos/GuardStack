<script lang="ts" setup>
/**
 * Compliance - EU AI Act Page
 * EU AI Act compliance assessment and reporting
 */
import { ref, computed, onMounted } from 'vue';
import ComplianceStatus from '../../components/ComplianceStatus.vue';
import StatusBadge from '../../components/StatusBadge.vue';
import TrendChart from '../../components/TrendChart.vue';

interface Requirement {
  id: string;
  name: string;
  description: string;
  article: string;
  status: 'compliant' | 'partial' | 'non_compliant' | 'not_applicable';
  evidence?: string;
  lastAssessed?: string;
}

interface RiskCategory {
  id: string;
  name: string;
  description: string;
  requirements: Requirement[];
}

const loading = ref(true);
const selectedCategory = ref<string | null>(null);
const showRequirementModal = ref(false);
const selectedRequirement = ref<Requirement | null>(null);

const riskCategories = ref<RiskCategory[]>([
  {
    id: 'prohibited',
    name: 'Prohibited Practices',
    description: 'AI systems that are prohibited under the EU AI Act (Article 5)',
    requirements: [
      {
        id: 'ART5-1A',
        name: 'Subliminal manipulation',
        description: 'AI systems that deploy subliminal techniques to materially distort behavior',
        article: 'Article 5(1)(a)',
        status: 'compliant',
        evidence: 'System does not use subliminal techniques',
      },
      {
        id: 'ART5-1B',
        name: 'Vulnerability exploitation',
        description: 'AI systems that exploit vulnerabilities of specific groups',
        article: 'Article 5(1)(b)',
        status: 'compliant',
        evidence: 'No targeting of vulnerable groups detected',
      },
      {
        id: 'ART5-1C',
        name: 'Social scoring',
        description: 'AI systems for social scoring by public authorities',
        article: 'Article 5(1)(c)',
        status: 'not_applicable',
        evidence: 'System is not used for social scoring',
      },
    ],
  },
  {
    id: 'high-risk',
    name: 'High-Risk Requirements',
    description: 'Requirements for high-risk AI systems (Articles 8-15)',
    requirements: [
      {
        id: 'ART9',
        name: 'Risk Management System',
        description: 'Establish, implement, document and maintain a risk management system',
        article: 'Article 9',
        status: 'partial',
        evidence: 'Risk management system in place, continuous monitoring needed',
      },
      {
        id: 'ART10',
        name: 'Data Governance',
        description: 'Training, validation and testing data shall be subject to appropriate data governance',
        article: 'Article 10',
        status: 'compliant',
        evidence: 'Data governance policies implemented',
      },
      {
        id: 'ART11',
        name: 'Technical Documentation',
        description: 'Technical documentation shall be drawn up before the system is placed on the market',
        article: 'Article 11',
        status: 'compliant',
        evidence: 'Full technical documentation available',
      },
      {
        id: 'ART12',
        name: 'Record-keeping',
        description: 'AI systems shall be designed to automatically record events (logs)',
        article: 'Article 12',
        status: 'compliant',
        evidence: 'Comprehensive logging implemented',
      },
      {
        id: 'ART13',
        name: 'Transparency',
        description: 'AI systems shall be designed to enable users to interpret the output',
        article: 'Article 13',
        status: 'partial',
        evidence: 'Explainability features implemented, user documentation in progress',
      },
      {
        id: 'ART14',
        name: 'Human Oversight',
        description: 'AI systems shall be designed to allow effective human oversight',
        article: 'Article 14',
        status: 'compliant',
        evidence: 'Human-in-the-loop mechanisms implemented',
      },
      {
        id: 'ART15',
        name: 'Accuracy & Robustness',
        description: 'AI systems shall achieve appropriate levels of accuracy, robustness and cybersecurity',
        article: 'Article 15',
        status: 'partial',
        evidence: 'Performance meets thresholds, robustness testing ongoing',
      },
    ],
  },
  {
    id: 'transparency',
    name: 'Transparency Obligations',
    description: 'Transparency requirements for certain AI systems (Article 52)',
    requirements: [
      {
        id: 'ART52-1',
        name: 'Human Interaction Disclosure',
        description: 'Persons interacting with AI system shall be informed',
        article: 'Article 52(1)',
        status: 'compliant',
        evidence: 'AI interaction disclosure implemented',
      },
      {
        id: 'ART52-2',
        name: 'Emotion Recognition Disclosure',
        description: 'Users of emotion recognition systems shall be informed',
        article: 'Article 52(2)',
        status: 'not_applicable',
        evidence: 'System does not perform emotion recognition',
      },
      {
        id: 'ART52-3',
        name: 'Deep Fake Disclosure',
        description: 'Users generating deep fakes shall disclose artificial nature',
        article: 'Article 52(3)',
        status: 'not_applicable',
        evidence: 'System does not generate deep fakes',
      },
    ],
  },
]);

const overallStatus = computed(() => {
  const allRequirements = riskCategories.value.flatMap(c => c.requirements);
  const applicable = allRequirements.filter(r => r.status !== 'not_applicable');
  const compliant = applicable.filter(r => r.status === 'compliant').length;
  const partial = applicable.filter(r => r.status === 'partial').length;
  
  if (compliant === applicable.length) return 'compliant';
  if (compliant + partial === applicable.length) return 'partial';
  return 'non_compliant';
});

const complianceScore = computed(() => {
  const allRequirements = riskCategories.value.flatMap(c => c.requirements);
  const applicable = allRequirements.filter(r => r.status !== 'not_applicable');
  if (applicable.length === 0) return 100;
  
  let score = 0;
  applicable.forEach(r => {
    if (r.status === 'compliant') score += 100;
    else if (r.status === 'partial') score += 50;
  });
  
  return Math.round(score / applicable.length);
});

const trendData = computed(() => [
  { date: '2024-01-01', value: 65 },
  { date: '2024-02-01', value: 68 },
  { date: '2024-03-01', value: 72 },
  { date: '2024-04-01', value: 75 },
  { date: '2024-05-01', value: 78 },
  { date: '2024-06-01', value: complianceScore.value },
]);

function viewRequirement(requirement: Requirement) {
  selectedRequirement.value = requirement;
  showRequirementModal.value = true;
}

function generateReport() {
  console.log('Generating EU AI Act compliance report');
}

onMounted(() => {
  loading.value = false;
});
</script>

<template>
  <div class="eu-ai-act-compliance p-6">
    <!-- Header -->
    <div class="flex items-start justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-gray-100">
          EU AI Act Compliance
        </h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">
          Assessment against Regulation (EU) 2024/1689
        </p>
      </div>
      <button
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        @click="generateReport"
      >
        Generate Report
      </button>
    </div>
    
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
    
    <template v-else>
      <!-- Overview cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <!-- Overall status -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
            Overall Status
          </h3>
          <div class="flex items-center gap-4">
            <span class="text-4xl">🇪🇺</span>
            <div>
              <StatusBadge
                :status="overallStatus === 'compliant' ? 'pass' : 
                         overallStatus === 'partial' ? 'warn' : 'fail'"
                :label="overallStatus === 'compliant' ? 'Compliant' : 
                        overallStatus === 'partial' ? 'Partially Compliant' : 'Non-Compliant'"
                size="lg"
              />
              <p class="text-sm text-gray-500 mt-2">
                Last assessed: {{ new Date().toLocaleDateString() }}
              </p>
            </div>
          </div>
        </div>
        
        <!-- Compliance score -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
            Compliance Score
          </h3>
          <div class="flex items-end gap-2">
            <span :class="[
              'text-4xl font-bold',
              complianceScore >= 80 ? 'text-green-600' :
              complianceScore >= 60 ? 'text-yellow-600' : 'text-red-600'
            ]">
              {{ complianceScore }}%
            </span>
            <span class="text-sm text-gray-500 mb-1">out of 100%</span>
          </div>
          <div class="mt-3 h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
            <div
              :class="[
                'h-full rounded-full transition-all',
                complianceScore >= 80 ? 'bg-green-500' :
                complianceScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
              ]"
              :style="{ width: `${complianceScore}%` }"
            ></div>
          </div>
        </div>
        
        <!-- Compliance trend -->
        <div class="bg-white dark:bg-gray-800 rounded-lg border p-6">
          <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
            Compliance Trend
          </h3>
          <TrendChart
            :data="trendData"
            :height="100"
            :show-grid="false"
            :show-dots="false"
            :show-labels="false"
            color="#3b82f6"
          />
        </div>
      </div>
      
      <!-- Risk categories -->
      <div class="space-y-6">
        <div
          v-for="category in riskCategories"
          :key="category.id"
          class="bg-white dark:bg-gray-800 rounded-lg border"
        >
          <!-- Category header -->
          <div
            class="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
            @click="selectedCategory = selectedCategory === category.id ? null : category.id"
          >
            <div class="flex items-center gap-3">
              <span class="text-xl">
                {{ category.id === 'prohibited' ? '🚫' : 
                   category.id === 'high-risk' ? '⚠️' : '👁️' }}
              </span>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-gray-100">
                  {{ category.name }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ category.description }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-sm text-gray-500">
                {{ category.requirements.filter(r => r.status === 'compliant').length }}/{{ category.requirements.length }} compliant
              </div>
              <span class="text-gray-400">
                {{ selectedCategory === category.id ? '▼' : '▶' }}
              </span>
            </div>
          </div>
          
          <!-- Requirements list -->
          <div v-if="selectedCategory === category.id" class="border-t">
            <table class="w-full">
              <thead class="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th class="px-4 py-2 text-left text-sm font-medium text-gray-500">ID</th>
                  <th class="px-4 py-2 text-left text-sm font-medium text-gray-500">Requirement</th>
                  <th class="px-4 py-2 text-left text-sm font-medium text-gray-500">Article</th>
                  <th class="px-4 py-2 text-left text-sm font-medium text-gray-500">Status</th>
                  <th class="px-4 py-2 text-left text-sm font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="req in category.requirements"
                  :key="req.id"
                  class="border-t hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <td class="px-4 py-3 text-sm text-gray-500">{{ req.id }}</td>
                  <td class="px-4 py-3">
                    <div class="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {{ req.name }}
                    </div>
                    <div class="text-xs text-gray-500 line-clamp-1">
                      {{ req.description }}
                    </div>
                  </td>
                  <td class="px-4 py-3 text-sm text-gray-500">{{ req.article }}</td>
                  <td class="px-4 py-3">
                    <StatusBadge
                      :status="req.status === 'compliant' ? 'pass' :
                               req.status === 'partial' ? 'warn' :
                               req.status === 'non_compliant' ? 'fail' : 'pending'"
                      :label="req.status.replace('_', ' ')"
                    />
                  </td>
                  <td class="px-4 py-3">
                    <button
                      class="text-sm text-blue-600 hover:underline"
                      @click="viewRequirement(req)"
                    >
                      View
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <!-- Requirement modal -->
      <div
        v-if="showRequirementModal && selectedRequirement"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        @click.self="showRequirementModal = false"
      >
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
          <div class="flex items-start justify-between mb-4">
            <div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {{ selectedRequirement.name }}
              </h3>
              <p class="text-sm text-gray-500">{{ selectedRequirement.id }} • {{ selectedRequirement.article }}</p>
            </div>
            <button
              class="text-gray-400 hover:text-gray-600"
              @click="showRequirementModal = false"
            >
              ✕
            </button>
          </div>
          
          <div class="space-y-4">
            <div>
              <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</h4>
              <p class="text-sm text-gray-600 dark:text-gray-400">{{ selectedRequirement.description }}</p>
            </div>
            
            <div>
              <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</h4>
              <StatusBadge
                :status="selectedRequirement.status === 'compliant' ? 'pass' :
                         selectedRequirement.status === 'partial' ? 'warn' :
                         selectedRequirement.status === 'non_compliant' ? 'fail' : 'pending'"
                :label="selectedRequirement.status.replace('_', ' ')"
              />
            </div>
            
            <div v-if="selectedRequirement.evidence">
              <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Evidence</h4>
              <p class="text-sm text-gray-600 dark:text-gray-400">{{ selectedRequirement.evidence }}</p>
            </div>
          </div>
          
          <div class="flex justify-end gap-3 mt-6">
            <button
              class="px-4 py-2 border rounded-lg hover:bg-gray-50"
              @click="showRequirementModal = false"
            >
              Close
            </button>
            <button class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Update Evidence
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
