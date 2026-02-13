<script setup lang="ts">
import AgentOutputCard from './AgentOutputCard.vue'
import IconArrowDown from './icons/IconArrowDown.vue'

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
          greyed:
            agent.status === 'pending' ||
            agent.status === 'running' ||
            agents[index + 1]?.status === 'error',
          loading: agent.status === 'complete' && agents[index + 1]?.status === 'running',
          complete:
            agent.status === 'complete' &&
            agents[index + 1]?.status !== 'running' &&
            agents[index + 1]?.status !== 'error'
        }"
      >
        <div class="connector-line" />
        <div class="connector-arrow">
          <IconArrowDown />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped src="./AgentFlowchart.styles.css"></style>
