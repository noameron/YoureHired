<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'

const { theme, toggleTheme } = useTheme()
</script>

<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="toggleTheme"
  >
    <!-- Sun icon (shown in dark mode, click to switch to light) -->
    <svg
      v-if="theme === 'dark'"
      class="theme-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <circle
        cx="12"
        cy="12"
        r="5"
      />
      <line
        x1="12"
        y1="1"
        x2="12"
        y2="3"
      />
      <line
        x1="12"
        y1="21"
        x2="12"
        y2="23"
      />
      <line
        x1="4.22"
        y1="4.22"
        x2="5.64"
        y2="5.64"
      />
      <line
        x1="18.36"
        y1="18.36"
        x2="19.78"
        y2="19.78"
      />
      <line
        x1="1"
        y1="12"
        x2="3"
        y2="12"
      />
      <line
        x1="21"
        y1="12"
        x2="23"
        y2="12"
      />
      <line
        x1="4.22"
        y1="19.78"
        x2="5.64"
        y2="18.36"
      />
      <line
        x1="18.36"
        y1="5.64"
        x2="19.78"
        y2="4.22"
      />
    </svg>

    <!-- Moon icon (shown in light mode, click to switch to dark) -->
    <svg
      v-else
      class="theme-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  </button>
</template>

<style scoped>
.theme-toggle {
  position: fixed;
  top: var(--space-4, 1rem);
  right: var(--space-4, 1rem);
  z-index: var(--z-fixed, 300);

  display: flex;
  align-items: center;
  justify-content: center;

  width: 48px;
  height: 48px;
  padding: 0;

  background-color: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-full);
  cursor: pointer;

  color: var(--text-secondary);
  transition:
    background-color var(--transition-fast),
    border-color var(--transition-fast),
    color var(--transition-fast),
    box-shadow var(--transition-fast),
    transform var(--transition-fast);

  box-shadow: var(--shadow-md);
}

.theme-toggle:hover {
  color: var(--accent-primary);
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow);
  transform: scale(1.05);
}

.theme-toggle:focus-visible {
  outline: none;
  box-shadow:
    var(--shadow-glow),
    0 0 0 3px var(--accent-light);
}

.theme-toggle:active {
  transform: scale(0.95);
}

.theme-icon {
  width: 24px;
  height: 24px;
}

/* Reduce motion for accessibility */
@media (prefers-reduced-motion: reduce) {
  .theme-toggle {
    transition: none;
  }

  .theme-toggle:hover,
  .theme-toggle:active {
    transform: none;
  }
}
</style>
