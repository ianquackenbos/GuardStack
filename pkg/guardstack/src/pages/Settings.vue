<template>
  <div class="guardstack-settings">
    <header class="page-header">
      <h1>Settings</h1>
    </header>

    <div class="settings-sections">
      <section class="settings-section">
        <h2>General</h2>
        <div class="setting-item">
          <label>API Base URL</label>
          <input v-model="settings.apiBaseUrl" type="text" />
        </div>
        <div class="setting-item">
          <label>Default Evaluation Timeout (seconds)</label>
          <input v-model.number="settings.evaluationTimeout" type="number" />
        </div>
      </section>

      <section class="settings-section">
        <h2>Notifications</h2>
        <div class="setting-item">
          <label class="toggle-label">
            <span>Email notifications</span>
            <input v-model="settings.emailNotifications" type="checkbox" />
          </label>
        </div>
        <div class="setting-item">
          <label class="toggle-label">
            <span>Slack notifications</span>
            <input v-model="settings.slackNotifications" type="checkbox" />
          </label>
        </div>
      </section>

      <section class="settings-section">
        <h2>Thresholds</h2>
        <div class="setting-item">
          <label>Risk Score Threshold</label>
          <input v-model.number="settings.riskThreshold" type="number" min="0" max="100" />
        </div>
        <div class="setting-item">
          <label>Compliance Score Threshold</label>
          <input v-model.number="settings.complianceThreshold" type="number" min="0" max="100" />
        </div>
      </section>

      <div class="settings-actions">
        <button class="btn btn-primary" @click="saveSettings">Save Settings</button>
        <button class="btn btn-outline" @click="resetSettings">Reset to Defaults</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue';

const settings = reactive({
  apiBaseUrl: '/api/v1',
  evaluationTimeout: 3600,
  emailNotifications: true,
  slackNotifications: false,
  riskThreshold: 70,
  complianceThreshold: 80,
});

function saveSettings() {
  localStorage.setItem('guardstack-settings', JSON.stringify(settings));
  alert('Settings saved!');
}

function resetSettings() {
  settings.apiBaseUrl = '/api/v1';
  settings.evaluationTimeout = 3600;
  settings.emailNotifications = true;
  settings.slackNotifications = false;
  settings.riskThreshold = 70;
  settings.complianceThreshold = 80;
}
</script>

<style lang="scss" scoped>
.guardstack-settings {
  padding: 20px;
  max-width: 800px;
}

.page-header {
  margin-bottom: 24px;
}

.settings-section {
  margin-bottom: 32px;
  padding: 20px;
  background: var(--card-bg, #fff);
  border-radius: 8px;

  h2 {
    margin: 0 0 16px;
    font-size: 18px;
  }
}

.setting-item {
  margin-bottom: 16px;

  label {
    display: block;
    margin-bottom: 4px;
    font-weight: 500;
  }

  input[type="text"],
  input[type="number"] {
    width: 100%;
    max-width: 400px;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 4px;
  }

  .toggle-label {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 400px;

    input[type="checkbox"] {
      width: 20px;
      height: 20px;
    }
  }
}

.settings-actions {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;

  &.btn-primary {
    background: var(--primary);
    color: #fff;
  }

  &.btn-outline {
    background: transparent;
    border: 1px solid var(--border);
  }
}
</style>
