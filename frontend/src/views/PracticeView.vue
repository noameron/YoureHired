<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserSelectionStore } from '@/stores/userSelection'
import { streamDrillGeneration } from '@/services/api'
import type { Drill } from '@/services/types'
import { useSolution } from '@/composables/usePractice'
import { useAgentFlowchart } from '@/composables/useAgentFlowchart'
import FeedbackCard from '@/components/FeedbackCard.vue'
import AgentFlowchart from '@/components/AgentFlowchart.vue'
import DrillCard from '@/components/DrillCard.vue'

const router = useRouter()
const store = useUserSelectionStore()

const {
  solution,
  feedback,
  isEvaluating,
  evaluationError,
  submitSolution,
  clearFeedback
} = useSolution(() => store.sessionId)

const {
  agents: researchAgents,
  allComplete: allResearchComplete,
  reset: resetAgents,
  updateFromStatus: updateAgentFromStatus,
  updateFromCandidate: updateAgentFromCandidate,
  markAllComplete: markAllAgentsComplete
} = useAgentFlowchart()

const currentStatus = ref<string>('Connecting...')
const drill = ref<Drill | null>(null)
const drillCandidates = ref<string[]>([])
const error = ref<string | null>(null)

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
        drillCandidates.value.push(event.title)
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
      <DrillCard
        v-else-if="drill"
        v-model:solution="solution"
        :drill="drill"
        :is-evaluating="isEvaluating"
        :evaluation-error="evaluationError"
        @submit="submitSolution"
      />

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

<style scoped src="./PracticeView.styles.css"></style>
