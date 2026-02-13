<script setup lang="ts">
import { useTheme } from '@/composables/useTheme'
import IconSun from './icons/IconSun.vue'
import IconMoon from './icons/IconMoon.vue'

const { theme, toggleTheme } = useTheme()
</script>

<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="toggleTheme"
  >
    <IconSun v-if="theme === 'dark'" />
    <IconMoon v-else />
  </button>
</template>

<style scoped src="./ThemeToggle.styles.css"></style>
