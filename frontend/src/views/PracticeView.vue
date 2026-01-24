<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserSelectionStore } from '@/stores/userSelection'
import { streamCompanyResearch } from '@/services/api'
import type { CompanySummary } from '@/types/api'

const router = useRouter()
const store = useUserSelectionStore()

const currentStatus = ref<string>('Connecting...')
const summary = ref<CompanySummary | null>(null)
const error = ref<string | null>(null)
const isComplete = ref(false)

async function startResearch() {
  if (!store.sessionId) {
    router.push('/')
    return
  }

  error.value = null
  isComplete.value = false
  currentStatus.value = 'Starting research...'

  try {
    for await (const event of streamCompanyResearch(store.sessionId)) {
      if (event.type === 'status') {
        currentStatus.value = event.message
      } else if (event.type === 'complete') {
        summary.value = event.data
        isComplete.value = true
      } else if (event.type === 'error') {
        error.value = event.message
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Connection failed'
  }
}

function retry() {
  startResearch()
}

onMounted(() => {
  startResearch()
})
</script>

<template>
  <div class="practice-view">
    <div class="content">
      <!-- Loading state -->
      <div v-if="!isComplete && !error" class="loading-state">
        <div class="spinner"></div>
        <p class="status">{{ currentStatus }}</p>
        <p class="context">Researching {{ store.companyName }} for {{ store.role }}</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <p class="error-message">{{ error }}</p>
        <button @click="retry" class="retry-button">Try Again</button>
      </div>

      <!-- Complete state - show summary -->
      <div v-else-if="summary" class="summary-state">
        <h1>{{ summary.name }}</h1>
        <p class="description">{{ summary.description }}</p>

        <div v-if="summary.tech_stack" class="section">
          <h3>Tech Stack</h3>
          <p v-if="summary.tech_stack.languages.length">
            <strong>Languages:</strong> {{ summary.tech_stack.languages.join(', ') }}
          </p>
          <p v-if="summary.tech_stack.frameworks.length">
            <strong>Frameworks:</strong> {{ summary.tech_stack.frameworks.join(', ') }}
          </p>
          <p v-if="summary.tech_stack.tools.length">
            <strong>Tools:</strong> {{ summary.tech_stack.tools.join(', ') }}
          </p>
        </div>

        <div v-if="summary.engineering_culture" class="section">
          <h3>Engineering Culture</h3>
          <p>{{ summary.engineering_culture }}</p>
        </div>

        <div v-if="summary.interview_tips" class="section">
          <h3>Interview Tips</h3>
          <p>{{ summary.interview_tips }}</p>
        </div>

        <div v-if="summary.recent_news.length" class="section">
          <h3>Recent News</h3>
          <ul>
            <li v-for="(news, idx) in summary.recent_news" :key="idx">{{ news }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.practice-view {
  min-height: 100vh;
  background: #f0f2f5;
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.content {
  max-width: 700px;
  width: 100%;
}

.loading-state {
  text-align: center;
  padding: 4rem 2rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e0e0e0;
  border-top-color: #0066ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status {
  font-size: 1.25rem;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
}

.context {
  color: #6c757d;
  font-size: 0.9rem;
}

.error-state {
  text-align: center;
  padding: 4rem 2rem;
}

.error-message {
  color: #dc3545;
  margin-bottom: 1.5rem;
}

.retry-button {
  background: #0066ff;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
}

.retry-button:hover {
  background: #0052cc;
}

.summary-state {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.summary-state h1 {
  margin: 0 0 1rem;
  color: #1a1a2e;
}

.description {
  color: #4a5568;
  line-height: 1.6;
  margin-bottom: 2rem;
}

.section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.summary-state h3 {
  color: #1a1a2e;
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
}

.summary-state p {
  color: #4a5568;
  margin: 0.5rem 0;
}

.summary-state ul {
  color: #4a5568;
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}
</style>
