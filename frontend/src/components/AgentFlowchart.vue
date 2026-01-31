<script setup lang="ts">
import AgentOutputCard from './AgentOutputCard.vue'

export interface FlowchartAgent {
  id: number
  name: string
  status: 'pending' | 'running' | 'complete' | 'error'
  output: string | null
  streamingMessage?: string | null
  error?: string
}

defineProps<{
  agents: FlowchartAgent[]
}>()
</script>

<template>
  <div class="flowchart-container">
    <div
      v-for="(agent, index) in agents"
      :key="agent.id"
      class="flowchart-step"
    >
      <!-- Agent Card -->
      <AgentOutputCard
        :name="agent.name"
        :status="agent.status"
        :output="agent.output"
        :error="agent.error"
        :streaming-message="agent.streamingMessage"
      />

      <!-- Connector (between agents, not after last one) -->
      <div
        v-if="index < agents.length - 1"
        class="connector"
        :class="{
          active: agent.status === 'complete' || agents[index + 1]?.status === 'running'
        }"
      >
        <div class="connector-line" />
        <div class="connector-arrow">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M12 5v14M19 12l-7 7-7-7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.flowchart-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
}

.flowchart-step {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.flowchart-step :deep(.agent-card) {
  width: 100%;
}

/* Connector between cards */
.connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-2) 0;
  transition: all var(--transition-base);
}

.connector-line {
  width: 2px;
  height: 24px;
  background: var(--border-secondary);
  border-style: dashed;
  transition: background var(--transition-base);
}

.connector.active .connector-line {
  background: var(--accent-primary);
  animation: lineGlow 0.5s ease-out;
}

.connector-arrow {
  width: 20px;
  height: 20px;
  color: var(--text-muted);
  transition: color var(--transition-base);
}

.connector.active .connector-arrow {
  color: var(--accent-primary);
  animation: arrowPulse 0.5s ease-out;
}

.connector-arrow svg {
  width: 100%;
  height: 100%;
}

@keyframes lineGlow {
  0% {
    box-shadow: 0 0 0 var(--accent-glow);
  }
  50% {
    box-shadow: 0 0 8px var(--accent-glow);
  }
  100% {
    box-shadow: 0 0 0 transparent;
  }
}

@keyframes arrowPulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}
</style>
