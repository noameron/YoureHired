<script setup lang="ts">
import { RouterView } from 'vue-router'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useTheme } from '@/composables/useTheme'

import '@/assets/design-tokens.css'
import '@/assets/base.css'

// Sync Vue state with DOM (theme already initialized by inline script in index.html)
useTheme().syncFromDom()
</script>

<template>
  <ThemeToggle />
  <RouterView />
</template>

<style>
#app {
  min-height: 100vh;
}
</style>
