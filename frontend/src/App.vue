<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'

import '@/assets/design-tokens.css'
import '@/assets/base.css'
</script>

<template>
  <nav class="app-nav">
    <RouterLink
      to="/"
      class="nav-link"
    >
      Practice
    </RouterLink>
    <RouterLink
      to="/scout"
      class="nav-link"
    >
      Scout
    </RouterLink>
  </nav>
  <RouterView />
</template>

<style>
#app {
  min-height: 100vh;
}

.app-nav {
  display: flex;
  gap: var(--space-4, 1rem);
  padding: var(--space-2, 0.5rem) var(--space-8, 2rem);
  border-bottom: 1px solid var(--border-primary, #e0e0e0);
}

.nav-link {
  text-decoration: none;
  font-weight: var(--font-medium, 500);
  color: var(--text-secondary);
  letter-spacing: var(--tracking-wide);
  font-size: var(--text-sm);
  text-transform: uppercase;
  padding: var(--space-2) 0;
  transition: color var(--transition-fast);
}

.nav-link:hover {
  color: var(--accent-primary);
}

.nav-link.router-link-active {
  font-weight: var(--font-bold, 700);
  color: var(--accent-primary);
  border-bottom: 2px solid var(--accent-primary);
}
</style>
