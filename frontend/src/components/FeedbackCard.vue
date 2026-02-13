<script setup lang="ts">
import { watch, toRef } from 'vue'
import type { SolutionFeedback } from '@/services/types'
import { useExpandableList } from '@/composables/useExpandableList'
import { getScoreColor, getScoreLabel } from '@/composables/useScore'

const props = defineProps<{
  feedback?: SolutionFeedback | null
  isLoading?: boolean
}>()

const emit = defineEmits<{
  (e: 'practice-weak-areas'): void
}>()

const {
  toggle: toggleStrength,
  isExpanded: isStrengthExpanded,
  reset: resetStrengths
} = useExpandableList()

const {
  toggle: toggleImprovement,
  isExpanded: isImprovementExpanded,
  reset: resetImprovements
} = useExpandableList()

watch(toRef(props, 'feedback'), () => {
  resetStrengths()
  resetImprovements()
})
</script>

<template>
  <div class="feedback-card">
    <!-- Loading state -->
    <div
      v-if="isLoading"
      class="loading-state"
    >
      <div class="spinner" />
      <p>Evaluating your solution...</p>
    </div>

    <!-- Feedback content -->
    <template v-else-if="feedback">
      <!-- Score header -->
      <div class="score-header">
        <h2>Feedback</h2>
        <div
          class="score-badge"
          :class="getScoreColor(feedback.score)"
        >
          <span class="score-value">{{ feedback.score.toFixed(1) }}</span>
          <span class="score-max">/10</span>
          <span class="score-label">{{ getScoreLabel(feedback.score) }}</span>
        </div>
      </div>

      <!-- Strengths section -->
      <section
        v-if="feedback.strengths.length"
        class="feedback-section"
      >
        <h3 class="section-title strengths-title">
          Strengths ({{ feedback.strengths.length }})
        </h3>
        <div class="items-list">
          <div
            v-for="(strength, idx) in feedback.strengths"
            :key="'strength-' + idx"
            class="feedback-item"
          >
            <button
              type="button"
              class="item-toggle"
              :class="{ expanded: isStrengthExpanded(idx) }"
              @click="toggleStrength(idx)"
            >
              <span class="item-icon strengths-icon">+</span>
              <span class="item-title">{{ strength.title }}</span>
              <span class="item-chevron">{{ isStrengthExpanded(idx) ? '\u25BC' : '\u25B6' }}</span>
            </button>
            <div
              v-show="isStrengthExpanded(idx)"
              class="item-content"
            >
              {{ strength.description }}
            </div>
          </div>
        </div>
      </section>

      <!-- Improvements section -->
      <section
        v-if="feedback.improvements.length"
        class="feedback-section"
      >
        <h3 class="section-title improvements-title">
          Areas for Improvement ({{ feedback.improvements.length }})
        </h3>
        <div class="items-list">
          <div
            v-for="(improvement, idx) in feedback.improvements"
            :key="'improvement-' + idx"
            class="feedback-item"
          >
            <button
              type="button"
              class="item-toggle"
              :class="{ expanded: isImprovementExpanded(idx) }"
              @click="toggleImprovement(idx)"
            >
              <span class="item-icon improvements-icon">!</span>
              <span class="item-title">{{ improvement.title }}</span>
              <span class="item-chevron">{{ isImprovementExpanded(idx) ? '\u25BC' : '\u25B6' }}</span>
            </button>
            <div
              v-show="isImprovementExpanded(idx)"
              class="item-content"
            >
              <p class="item-description">
                {{ improvement.description }}
              </p>
              <div class="suggestion-box">
                <strong>Suggestion:</strong> {{ improvement.suggestion }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Practice weak areas button -->
      <div
        v-if="feedback.improvements.length"
        class="practice-button-container"
      >
        <button
          type="button"
          class="btn btn-primary practice-weak-areas-btn"
          @click="emit('practice-weak-areas')"
        >
          Practice Weak Areas
        </button>
        <p class="practice-hint">
          Generate a new drill focused on the areas you need to improve
        </p>
      </div>
    </template>
  </div>
</template>

<style scoped src="./FeedbackCard.styles.css"></style>
