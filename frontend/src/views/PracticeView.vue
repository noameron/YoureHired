<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserSelectionStore } from '@/stores/userSelection'
import { streamDrillGeneration } from '@/services/api'
import type { Drill, DrillStreamCandidateEvent } from '@/services/types'
import { useHints, useSolution } from './practice/usePractice'
import FeedbackCard from '@/components/FeedbackCard.vue'

const router = useRouter()
const store = useUserSelectionStore()

const { toggleHint, isHintExpanded } = useHints()
const {
  solution,
  feedback,
  isEvaluating,
  evaluationError,
  submitSolution,
  clearFeedback
} = useSolution(() => store.sessionId)

const currentStatus = ref<string>('Connecting...')
const drill = ref<Drill | null>(null)
const drillCandidates = ref<DrillStreamCandidateEvent[]>([])
const error = ref<string | null>(null)

async function startDrillGeneration() {
  if (!store.sessionId) {
    router.push('/')
    return
  }

  error.value = null
  drill.value = null
  drillCandidates.value = []
  currentStatus.value = 'Starting...'
  // Clear previous feedback when generating new drill
  clearFeedback()
  solution.value = ''

  try {
    for await (const event of streamDrillGeneration(store.sessionId)) {
      if (event.type === 'status') {
        currentStatus.value = event.message
      } else if (event.type === 'candidate') {
        drillCandidates.value.push(event)
      } else if (event.type === 'complete') {
        drill.value = event.data
      } else if (event.type === 'error') {
        error.value = event.message
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Connection failed'
  }
}

function retry() {
  startDrillGeneration()
}

function practiceWeakAreas() {
  // Trigger new drill generation (feedback summary is already stored in session)
  startDrillGeneration()
}

function formatDrillType(type: string): string {
  return type.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

onMounted(() => {
  startDrillGeneration()
})
</script>

<template>
  <div class="practice-view">
    <div class="content">
      <!-- Loading state -->
      <div
        v-if="!drill && !error"
        class="loading-state"
      >
        <div class="spinner" />
        <p class="status">
          {{ currentStatus }}
        </p>
        <p class="context">
          Preparing drill for {{ store.companyName }} {{ store.role }}
        </p>

        <!-- Show candidates as they're generated -->
        <ul
          v-if="drillCandidates.length"
          class="candidates-preview"
        >
          <li
            v-for="(c, idx) in drillCandidates"
            :key="idx"
            class="candidate-item"
          >
            <span class="candidate-type">{{ formatDrillType(c.generator) }}</span>
            <span class="candidate-title">{{ c.title }}</span>
          </li>
        </ul>
      </div>

      <!-- Error state -->
      <div
        v-else-if="error"
        class="error-state"
      >
        <p class="error-message">
          {{ error }}
        </p>
        <button
          class="retry-button"
          @click="retry"
        >
          Try Again
        </button>
      </div>

      <!-- Complete state - show drill -->
      <div
        v-else-if="drill"
        class="drill-card"
      >
        <h1>{{ drill.title }}</h1>

        <div class="meta">
          <span class="type">{{ formatDrillType(drill.type) }}</span>
          <span
            class="difficulty"
            :class="drill.difficulty"
          >{{ drill.difficulty }}</span>
          <span class="time">{{ drill.expected_time_minutes }} min</span>
        </div>

        <p class="description">
          {{ drill.description }}
        </p>

        <section
          v-if="drill.company_context"
          class="section"
        >
          <h3>Company Context</h3>
          <p>{{ drill.company_context }}</p>
        </section>

        <section class="section">
          <h3>Requirements</h3>
          <ul class="requirements">
            <li
              v-for="(r, idx) in drill.requirements"
              :key="idx"
            >
              {{ r }}
            </li>
          </ul>
        </section>

        <section
          v-if="drill.tech_stack.length"
          class="section"
        >
          <h3>Tech Stack</h3>
          <div class="tags">
            <span
              v-for="(t, idx) in drill.tech_stack"
              :key="idx"
              class="tag"
            >{{ t }}</span>
          </div>
        </section>

        <section
          v-if="drill.starter_code"
          class="section"
        >
          <h3>Starter Code</h3>
          <pre class="code-block"><code>{{ drill.starter_code }}</code></pre>
        </section>

        <section
          v-if="drill.hints.length"
          class="hints-section"
        >
          <h3>Hints ({{ drill.hints.length }} available)</h3>
          <div class="hints-list">
            <div
              v-for="(hint, idx) in drill.hints"
              :key="idx"
              class="hint-item"
            >
              <button
                type="button"
                class="hint-toggle"
                :class="{ expanded: isHintExpanded(idx) }"
                @click="toggleHint(idx)"
              >
                <span class="hint-label">Hint {{ idx + 1 }}</span>
                <span class="hint-chevron">{{ isHintExpanded(idx) ? '\u25BC' : '\u25B6' }}</span>
              </button>
              <div
                v-show="isHintExpanded(idx)"
                class="hint-content"
              >
                {{ hint }}
              </div>
            </div>
          </div>
        </section>

        <section class="section solution-section">
          <h3>Your Solution</h3>
          <textarea
            v-model="solution"
            class="solution-input"
            placeholder="Paste or type your solution here..."
            rows="12"
            spellcheck="false"
            :disabled="isEvaluating"
          />

          <!-- Evaluation error -->
          <p
            v-if="evaluationError"
            class="evaluation-error"
          >
            {{ evaluationError }}
          </p>

          <button
            type="button"
            class="submit-solution-btn"
            :disabled="!solution.trim() || isEvaluating"
            @click="submitSolution"
          >
            {{ isEvaluating ? 'Evaluating...' : 'Submit Solution' }}
          </button>
        </section>
      </div>

      <!-- Feedback Card -->
      <FeedbackCard
        v-if="feedback || isEvaluating"
        :feedback="feedback!"
        :is-loading="isEvaluating"
        @practice-weak-areas="practiceWeakAreas"
      />
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
  to {
    transform: rotate(360deg);
  }
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

.candidates-preview {
  list-style: none;
  padding: 0;
  margin-top: 2rem;
  text-align: left;
  background: white;
  border-radius: 8px;
  padding: 1rem;
}

.candidate-item {
  padding: 0.5rem 0;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.candidate-item:last-child {
  border-bottom: none;
}

.candidate-type {
  background: #e0e0e0;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  text-transform: uppercase;
  font-weight: 600;
  color: #4a5568;
}

.candidate-title {
  color: #1a1a2e;
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

.drill-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.drill-card h1 {
  margin: 0 0 1rem;
  color: #1a1a2e;
}

.meta {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.meta span {
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
}

.type {
  background: #e8f4ff;
  color: #0066ff;
}

.difficulty {
  text-transform: capitalize;
}

.difficulty.easy {
  background: #d4edda;
  color: #155724;
}

.difficulty.medium {
  background: #fff3cd;
  color: #856404;
}

.difficulty.hard {
  background: #f8d7da;
  color: #721c24;
}

.time {
  background: #f0f0f0;
  color: #4a5568;
}

.description {
  color: #4a5568;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.drill-card h3 {
  color: #1a1a2e;
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
}

.drill-card p {
  color: #4a5568;
  margin: 0.5rem 0;
}

.requirements {
  color: #4a5568;
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.requirements li {
  margin: 0.5rem 0;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  background: #f0f0f0;
  color: #4a5568;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.code-block {
  background: #1a1a2e;
  color: #f0f0f0;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
}

.hints-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.hints-section h3 {
  color: #1a1a2e;
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
}

.hints-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.hint-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.hint-toggle {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  color: #0066ff;
  text-align: left;
}

.hint-toggle:hover {
  background: #f0f2f5;
}

.hint-chevron {
  font-size: 0.75rem;
  color: #6c757d;
}

.hint-toggle.expanded .hint-chevron {
  color: #0066ff;
}

.hint-content {
  padding: 0.75rem 1rem;
  color: #4a5568;
  line-height: 1.6;
  background: #ffffff;
  border-top: 1px solid #e0e0e0;
}

.solution-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.solution-input {
  width: 100%;
  min-height: 200px;
  padding: 1rem;
  background: #1a1a2e;
  color: #f0f0f0;
  border: 1px solid #2d2d44;
  border-radius: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  resize: vertical;
  box-sizing: border-box;
}

.solution-input::placeholder {
  color: #6b7280;
}

.solution-input:focus {
  outline: none;
  border-color: #0066ff;
  box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.2);
}

.solution-input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.evaluation-error {
  color: #dc3545;
  margin: 0.75rem 0;
  font-size: 0.9rem;
}

.submit-solution-btn {
  margin-top: 1rem;
  background: #0066ff;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 600;
}

.submit-solution-btn:hover:not(:disabled) {
  background: #0052cc;
}

.submit-solution-btn:disabled {
  background: #a0aec0;
  cursor: not-allowed;
}
</style>
