<script setup lang="ts">
import { ref, watch, toRef } from 'vue'
import type { SolutionFeedback } from '@/services/types'

const props = defineProps<{
  feedback?: SolutionFeedback | null
  isLoading?: boolean
}>()

const emit = defineEmits<{
  (e: 'practice-weak-areas'): void
}>()

const expandedStrengths = ref<number[]>([])
const expandedImprovements = ref<number[]>([])

// Reset expanded state when feedback changes to prevent stale indices
watch(toRef(props, 'feedback'), () => {
  expandedStrengths.value = []
  expandedImprovements.value = []
})

function toggleStrength(index: number) {
  const idx = expandedStrengths.value.indexOf(index)
  if (idx > -1) {
    expandedStrengths.value.splice(idx, 1)
  } else {
    expandedStrengths.value.push(index)
  }
}

function toggleImprovement(index: number) {
  const idx = expandedImprovements.value.indexOf(index)
  if (idx > -1) {
    expandedImprovements.value.splice(idx, 1)
  } else {
    expandedImprovements.value.push(index)
  }
}

function isStrengthExpanded(index: number): boolean {
  return expandedStrengths.value.includes(index)
}

function isImprovementExpanded(index: number): boolean {
  return expandedImprovements.value.includes(index)
}

function getScoreColor(score: number): string {
  if (score >= 7) return 'good'
  if (score >= 5) return 'adequate'
  return 'needs-work'
}

function getScoreLabel(score: number): string {
  if (score >= 9) return 'Exceptional'
  if (score >= 7) return 'Good'
  if (score >= 5) return 'Adequate'
  if (score >= 3) return 'Needs Work'
  return 'Incomplete'
}
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
          class="practice-weak-areas-btn"
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

<style scoped>
.feedback-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-2xl);
  padding: var(--space-8);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-subtle);
  margin-top: var(--space-8);
}

.loading-state {
  text-align: center;
  padding: var(--space-12) var(--space-8);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--border-primary);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto var(--space-4);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state p {
  color: var(--text-secondary);
  font-size: var(--text-base);
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--border-primary);
}

.score-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--text-2xl);
}

.score-badge {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-xl);
  flex-wrap: wrap;
  justify-content: center;
}

.score-badge.good {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.score-badge.adequate {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.score-badge.needs-work {
  background: var(--color-error-bg);
  color: var(--color-error-text);
}

.score-value {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  line-height: 1;
}

.score-max {
  font-size: var(--text-base);
  opacity: 0.7;
}

.score-label {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  width: 100%;
  text-align: center;
  margin-top: var(--space-1);
}

.feedback-section {
  margin-top: var(--space-6);
}

.section-title {
  font-size: var(--text-lg);
  margin: 0 0 var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.strengths-title {
  color: var(--color-success-text);
}

.improvements-title {
  color: var(--color-warning-text);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.feedback-item {
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.item-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-tertiary);
  border: none;
  cursor: pointer;
  font-size: var(--text-sm);
  text-align: left;
  transition: background var(--transition-fast);
}

.item-toggle:hover {
  background: var(--bg-hover);
}

.item-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-bold);
  font-size: var(--text-base);
  flex-shrink: 0;
}

.strengths-icon {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.improvements-icon {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.item-title {
  flex: 1;
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.item-chevron {
  font-size: var(--text-xs);
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.item-toggle.expanded .item-chevron {
  color: var(--accent-primary);
}

.item-content {
  padding: var(--space-4);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-primary);
}

.item-description {
  margin: 0 0 var(--space-3);
}

.suggestion-box {
  background: var(--accent-light);
  border-left: 3px solid var(--accent-primary);
  padding: var(--space-3) var(--space-4);
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
  color: var(--text-primary);
}

.practice-button-container {
  margin-top: var(--space-8);
  padding-top: var(--space-6);
  border-top: 1px solid var(--border-primary);
  text-align: center;
}

.practice-weak-areas-btn {
  background: var(--accent-primary);
  color: white;
  border: none;
  padding: var(--space-4) var(--space-10);
  border-radius: var(--radius-xl);
  cursor: pointer;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  box-shadow: var(--shadow-glow);
  transition:
    transform var(--transition-fast),
    box-shadow var(--transition-fast),
    background var(--transition-fast);
}

.practice-weak-areas-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow-lg);
}

.practice-weak-areas-btn:active {
  transform: translateY(0);
}

.practice-hint {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  margin: var(--space-3) 0 0;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .feedback-card {
    padding: var(--space-5);
  }

  .score-header {
    flex-direction: column;
    gap: var(--space-4);
    text-align: center;
  }
}
</style>
