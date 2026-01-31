<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserSelectionStore } from '@/stores/userSelection'
import { streamDrillGeneration } from '@/services/api'
import type { Drill, DrillStreamCandidateEvent } from '@/services/types'
import { useHints, useSolution } from './practice/usePractice'
import FeedbackCard from '@/components/FeedbackCard.vue'
import AgentFlowchart from '@/components/AgentFlowchart.vue'
import type { FlowchartAgent } from '@/components/AgentFlowchart.vue'

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

// Research agents for flowchart (2 agents matching backend phases)
const researchAgents = ref<FlowchartAgent[]>([
  { id: 1, name: 'Company Research', status: 'pending', output: null, streamingMessage: null },
  { id: 2, name: 'Drill Generation', status: 'pending', output: null, streamingMessage: null }
])

const allResearchComplete = computed(() =>
  researchAgents.value.every((a) => a.status === 'complete')
)

function resetAgents() {
  researchAgents.value = [
    { id: 1, name: 'Company Research', status: 'pending', output: null, streamingMessage: null },
    { id: 2, name: 'Drill Generation', status: 'pending', output: null, streamingMessage: null }
  ]
}

function updateAgentFromStatus(message: string) {
  const lowerMsg = message.toLowerCase()

  // Company Research agent keywords
  const isCompanyResearch =
    lowerMsg.includes('research') ||
    lowerMsg.includes('company') ||
    lowerMsg.includes('planning') ||
    lowerMsg.includes('found') ||
    lowerMsg.includes('completed') ||
    lowerMsg.includes('analyzing')

  // Drill Generation agent keywords
  const isDrillGeneration =
    lowerMsg.includes('drill') ||
    lowerMsg.includes('generat') ||
    lowerMsg.includes('candidate') ||
    lowerMsg.includes('evaluat') ||
    lowerMsg.includes('selected')

  if (isDrillGeneration) {
    // Drill generation starting means company research is complete
    const companyAgent = researchAgents.value[0]
    if (companyAgent && companyAgent.status === 'running') {
      companyAgent.status = 'complete'
      companyAgent.output = 'Research complete'
      companyAgent.streamingMessage = null
    }

    const drillAgent = researchAgents.value[1]
    if (drillAgent) {
      if (drillAgent.status === 'pending') {
        drillAgent.status = 'running'
      }
      drillAgent.streamingMessage = message
    }
  } else if (isCompanyResearch) {
    const agent = researchAgents.value[0]
    if (agent) {
      if (agent.status === 'pending') {
        agent.status = 'running'
      }
      agent.streamingMessage = message
    }
  }
}

function updateAgentFromCandidate(candidate: DrillStreamCandidateEvent) {
  // Ensure company research is complete when we get candidates
  const companyAgent = researchAgents.value[0]
  if (companyAgent && companyAgent.status !== 'complete') {
    companyAgent.status = 'complete'
    companyAgent.output = 'Research complete'
    companyAgent.streamingMessage = null
  }

  const drillAgent = researchAgents.value[1]
  if (drillAgent) {
    drillAgent.status = 'running'
    drillAgent.streamingMessage = `Generated: ${candidate.title}`
  }
}

function markAllAgentsComplete() {
  researchAgents.value.forEach((agent, index) => {
    if (agent.status !== 'error') {
      agent.status = 'complete'
      agent.streamingMessage = null
      // Set completion output text
      if (index === 0) {
        agent.output = 'Research complete'
      } else if (index === 1) {
        agent.output = 'Drill generated'
      }
    }
  })
}

function scrollToDrill() {
  const drillCard = document.querySelector('.drill-card')
  if (drillCard) {
    drillCard.scrollIntoView({ behavior: 'smooth' })
  }
}

async function startDrillGeneration() {
  if (!store.sessionId) {
    router.push('/')
    return
  }

  error.value = null
  drill.value = null
  drillCandidates.value = []
  currentStatus.value = 'Starting...'
  resetAgents()
  // Clear previous feedback when generating new drill
  clearFeedback()
  solution.value = ''

  try {
    for await (const event of streamDrillGeneration(store.sessionId)) {
      if (event.type === 'status') {
        currentStatus.value = event.message
        updateAgentFromStatus(event.message)
      } else if (event.type === 'candidate') {
        drillCandidates.value.push(event)
        updateAgentFromCandidate(event)
      } else if (event.type === 'complete') {
        markAllAgentsComplete()
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
      <!-- Loading state with agent carousel -->
      <div
        v-if="!drill && !error"
        class="loading-state"
      >
        <h2 class="loading-title">
          Preparing Your Drill
        </h2>
        <p class="context">
          {{ store.companyName }} - {{ store.role }}
        </p>

        <!-- Agent Flowchart -->
        <AgentFlowchart :agents="researchAgents" />

        <!-- Transition arrow (appears when all research complete) -->
        <div
          v-if="allResearchComplete"
          class="transition-arrow"
        >
          <button
            class="arrow-button"
            aria-label="Scroll to drill"
            @click="scrollToDrill"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M19 14l-7 7m0 0l-7-7m7 7V3"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>
        </div>
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
        :feedback="feedback"
        :is-loading="isEvaluating"
        @practice-weak-areas="practiceWeakAreas"
      />
    </div>
  </div>
</template>

<style scoped>
.practice-view {
  min-height: 100vh;
  background: var(--bg-primary);
  display: flex;
  justify-content: center;
  padding: var(--space-8);
}

.content {
  max-width: 700px;
  width: 100%;
}

.loading-state {
  text-align: center;
  padding: var(--space-8) var(--space-4);
}

.loading-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-2);
}

.context {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  margin-bottom: var(--space-6);
}


/* Transition Arrow */
.transition-arrow {
  display: flex;
  justify-content: center;
  padding: var(--space-8) 0;
  animation: fadeIn 0.5s ease;
}

.arrow-button {
  background: transparent;
  border: 2px solid var(--accent-primary);
  border-radius: var(--radius-full);
  width: 48px;
  height: 48px;
  color: var(--accent-primary);
  cursor: pointer;
  animation: bounce 2s infinite;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.arrow-button:hover {
  background: var(--accent-primary);
  color: white;
  animation: none;
}

.arrow-button svg {
  width: 24px;
  height: 24px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(8px);
  }
}

.error-state {
  text-align: center;
  padding: var(--space-16) var(--space-8);
}

.error-message {
  color: var(--color-error-text);
  margin-bottom: var(--space-6);
}

.retry-button {
  background: var(--accent-primary);
  color: white;
  border: none;
  padding: var(--space-3) var(--space-8);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  transition:
    background var(--transition-fast),
    box-shadow var(--transition-fast);
  box-shadow: 0 2px 8px var(--accent-glow);
}

.retry-button:hover {
  background: var(--accent-hover);
  box-shadow: var(--shadow-glow);
}

.drill-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-2xl);
  padding: var(--space-8);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-subtle);
}

.drill-card h1 {
  margin: 0 0 var(--space-4);
  color: var(--text-primary);
}

.meta {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
  flex-wrap: wrap;
}

.meta span {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.type {
  background: var(--accent-light);
  color: var(--accent-primary);
}

.difficulty {
  text-transform: capitalize;
}

.difficulty.easy {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.difficulty.medium {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.difficulty.hard {
  background: var(--color-error-bg);
  color: var(--color-error-text);
}

.time {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.description {
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-6);
}

.section {
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-primary);
}

.drill-card h3 {
  color: var(--text-primary);
  margin: 0 0 var(--space-3);
  font-size: var(--text-lg);
}

.drill-card p {
  color: var(--text-secondary);
  margin: var(--space-2) 0;
}

.requirements {
  color: var(--text-secondary);
  margin: var(--space-2) 0;
  padding-left: var(--space-6);
}

.requirements li {
  margin: var(--space-2) 0;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.tag {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.code-block {
  background: var(--code-bg);
  color: var(--code-text);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--code-border);
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

.hints-section {
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-primary);
}

.hints-section h3 {
  color: var(--text-primary);
  margin: 0 0 var(--space-3);
  font-size: var(--text-lg);
}

.hints-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.hint-item {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.hint-toggle {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: var(--bg-tertiary);
  border: none;
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--accent-primary);
  text-align: left;
  transition: background var(--transition-fast);
}

.hint-toggle:hover {
  background: var(--bg-hover);
}

.hint-chevron {
  font-size: var(--text-xs);
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.hint-toggle.expanded .hint-chevron {
  color: var(--accent-primary);
}

.hint-content {
  padding: var(--space-3) var(--space-4);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
}

.solution-section {
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-primary);
}

.solution-input {
  width: 100%;
  min-height: 200px;
  padding: var(--space-4);
  background: var(--code-bg);
  color: var(--code-text);
  border: 1px solid var(--code-border);
  border-radius: var(--radius-lg);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  resize: vertical;
  box-sizing: border-box;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.solution-input::placeholder {
  color: var(--text-muted);
}

.solution-input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px var(--accent-light);
}

.solution-input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.evaluation-error {
  color: var(--color-error-text);
  margin: var(--space-3) 0;
  font-size: var(--text-sm);
}

.submit-solution-btn {
  margin-top: var(--space-4);
  background: var(--accent-primary);
  color: white;
  border: none;
  padding: var(--space-3) var(--space-8);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  transition:
    background var(--transition-fast),
    box-shadow var(--transition-fast);
  box-shadow: 0 2px 8px var(--accent-glow);
}

.submit-solution-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  box-shadow: var(--shadow-glow);
}

.submit-solution-btn:disabled {
  background: var(--text-muted);
  cursor: not-allowed;
  box-shadow: none;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .practice-view {
    padding: var(--space-4);
  }

  .drill-card {
    padding: var(--space-5);
  }
}
</style>
