<script setup lang="ts">
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
        <!-- Pending -->
        <svg
          v-if="status === 'pending'"
          class="icon icon-pending"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle
            cx="12"
            cy="12"
            r="10"
          />
        </svg>

        <!-- Running spinner -->
        <div
          v-else-if="status === 'running'"
          class="spinner"
        />

        <!-- Complete checkmark -->
        <svg
          v-else-if="status === 'complete'"
          class="icon icon-complete"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path
            d="M20 6L9 17l-5-5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>

        <!-- Error X -->
        <svg
          v-else-if="status === 'error'"
          class="icon icon-error"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path
            d="M18 6L6 18M6 6l12 12"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
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

<style scoped>
.agent-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  border: 1px solid var(--border-subtle);
  min-height: 180px;
  display: flex;
  flex-direction: column;
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.agent-card.pending {
  opacity: 0.6;
}

.agent-card.running {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow-sm);
}

.agent-card.complete {
  border-color: var(--color-success);
}

.agent-card.error {
  border-color: var(--color-error);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.agent-name {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.status-indicator {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  width: 24px;
  height: 24px;
}

.icon-pending {
  color: var(--text-muted);
}

.icon-complete {
  color: var(--color-success);
}

.icon-error {
  color: var(--color-error);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-primary);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.agent-content {
  flex: 1;
  display: flex;
  align-items: flex-start;
}

.status-text {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.status-text.muted {
  color: var(--text-muted);
}

.streaming-text {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.error-text {
  color: var(--color-error-text);
}

.output-text {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
  overflow-y: auto;
  max-height: 120px;
}
</style>
