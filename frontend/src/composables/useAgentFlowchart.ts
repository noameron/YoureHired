import { ref, computed } from 'vue'
import type { Ref, ComputedRef } from 'vue'
import type { FlowchartAgent } from '@/components/AgentFlowchart.vue'
import type { DrillStreamCandidateEvent } from '@/services/types'

const COMPANY_AGENT_ID = 1
const DRILL_AGENT_ID = 2
const COMPANY_KEYWORDS = ['research', 'company', 'planning', 'found', 'completed', 'analyzing']
const DRILL_KEYWORDS = ['drill', 'generat', 'candidate', 'evaluat', 'selected']

function createInitialAgents(): FlowchartAgent[] {
  return [
    { id: COMPANY_AGENT_ID, name: 'Company Research', status: 'pending', output: null, streamingMessage: null },
    { id: DRILL_AGENT_ID, name: 'Drill Generation', status: 'pending', output: null, streamingMessage: null }
  ]
}

function findAgent(agents: FlowchartAgent[], id: number): FlowchartAgent | undefined {
  return agents.find(a => a.id === id)
}

function matchesKeywords(message: string, keywords: string[]): boolean {
  const lower = message.toLowerCase()
  return keywords.some(kw => lower.includes(kw))
}

export function useAgentFlowchart(): {
  agents: Ref<FlowchartAgent[]>
  allComplete: ComputedRef<boolean>
  reset: () => void
  updateFromStatus: (message: string) => void
  updateFromCandidate: (candidate: DrillStreamCandidateEvent) => void
  markAllComplete: () => void
} {
  const agents = ref<FlowchartAgent[]>(createInitialAgents())

  const allComplete = computed(() => agents.value.every(a => a.status === 'complete'))

  function reset(): void {
    agents.value = createInitialAgents()
  }

  function updateFromStatus(message: string): void {
    const isDrill = matchesKeywords(message, DRILL_KEYWORDS)
    const isCompany = matchesKeywords(message, COMPANY_KEYWORDS)

    if (isDrill) {
      // Drill starting means company is complete
      const companyAgent = findAgent(agents.value, COMPANY_AGENT_ID)
      if (companyAgent?.status === 'running') {
        companyAgent.status = 'complete'
        companyAgent.output = 'Research complete'
        companyAgent.streamingMessage = null
      }

      const drillAgent = findAgent(agents.value, DRILL_AGENT_ID)
      if (drillAgent) {
        if (drillAgent.status === 'pending') {
          drillAgent.status = 'running'
        }
        drillAgent.streamingMessage = message
      }
    } else if (isCompany) {
      const agent = findAgent(agents.value, COMPANY_AGENT_ID)
      if (agent) {
        if (agent.status === 'pending') {
          agent.status = 'running'
        }
        agent.streamingMessage = message
      }
    }
  }

  function updateFromCandidate(candidate: DrillStreamCandidateEvent): void {
    const companyAgent = findAgent(agents.value, COMPANY_AGENT_ID)
    if (companyAgent && companyAgent.status !== 'complete') {
      companyAgent.status = 'complete'
      companyAgent.output = 'Research complete'
      companyAgent.streamingMessage = null
    }

    const drillAgent = findAgent(agents.value, DRILL_AGENT_ID)
    if (drillAgent) {
      drillAgent.status = 'running'
      drillAgent.streamingMessage = `Generated: ${candidate.title}`
    }
  }

  function markAllComplete(): void {
    agents.value.forEach((agent) => {
      if (agent.status !== 'error') {
        agent.status = 'complete'
        agent.streamingMessage = null
        agent.output = agent.id === COMPANY_AGENT_ID ? 'Research complete' : 'Drill generated'
      }
    })
  }

  return { agents, allComplete, reset, updateFromStatus, updateFromCandidate, markAllComplete }
}
