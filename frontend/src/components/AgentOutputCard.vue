<script setup lang="ts">
import IconPending from './icons/IconPending.vue'
import IconComplete from './icons/IconComplete.vue'
import IconError from './icons/IconError.vue'

defineProps<{
  name: string
  status: 'pending' | 'running' | 'complete' | 'error'
  output: string | null
  error?: string
  streamingMessage?: string | null
}>()
</script>

<template>
  <article
    class="agent-card"
    :class="status"
  >
    <header class="agent-header">
      <h3 class="agent-name">
        {{ name }}
      </h3>
      <div class="status-indicator">
        <IconPending v-if="status === 'pending'" />
        <div
          v-else-if="status === 'running'"
          class="spinner"
        />
        <IconComplete v-else-if="status === 'complete'" />
        <IconError v-else-if="status === 'error'" />
      </div>
    </header>

    <div class="agent-content">
      <p
        v-if="status === 'pending'"
        class="status-text muted"
      >
        Waiting...
      </p>
      <p
        v-else-if="status === 'running'"
        class="status-text streaming-text"
      >
        {{ streamingMessage || 'Processing...' }}
      </p>
      <p
        v-else-if="status === 'error'"
        class="status-text error-text"
      >
        {{ error || 'An error occurred' }}
      </p>
      <p
        v-else-if="status === 'complete' && output"
        class="output-text"
      >
        {{ output }}
      </p>
    </div>
  </article>
</template>

<style scoped src="./AgentOutputCard.styles.css"></style>
