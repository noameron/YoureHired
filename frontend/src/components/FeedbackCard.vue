<script setup lang="ts">
import { ref } from 'vue'
import type { SolutionFeedback } from '@/services/types'

defineProps<{
  feedback: SolutionFeedback
  isLoading?: boolean
}>()

const emit = defineEmits<{
  (e: 'practice-weak-areas'): void
}>()

const expandedStrengths = ref<number[]>([])
const expandedImprovements = ref<number[]>([])

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
    <template v-else>
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
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-top: 2rem;
}

.loading-state {
  text-align: center;
  padding: 3rem 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top-color: #0066ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-state p {
  color: #6c757d;
  font-size: 1rem;
}

.score-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.score-header h2 {
  margin: 0;
  color: #1a1a2e;
  font-size: 1.5rem;
}

.score-badge {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  padding: 0.75rem 1.25rem;
  border-radius: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

.score-badge.good {
  background: #d4edda;
  color: #155724;
}

.score-badge.adequate {
  background: #fff3cd;
  color: #856404;
}

.score-badge.needs-work {
  background: #f8d7da;
  color: #721c24;
}

.score-value {
  font-size: 2rem;
  font-weight: 700;
  line-height: 1;
}

.score-max {
  font-size: 1rem;
  opacity: 0.7;
}

.score-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  width: 100%;
  text-align: center;
  margin-top: 0.25rem;
}

.feedback-section {
  margin-top: 1.5rem;
}

.section-title {
  font-size: 1.1rem;
  margin: 0 0 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.strengths-title {
  color: #155724;
}

.improvements-title {
  color: #856404;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.feedback-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.item-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
  text-align: left;
}

.item-toggle:hover {
  background: #f0f2f5;
}

.item-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  flex-shrink: 0;
}

.strengths-icon {
  background: #d4edda;
  color: #155724;
}

.improvements-icon {
  background: #fff3cd;
  color: #856404;
}

.item-title {
  flex: 1;
  font-weight: 600;
  color: #1a1a2e;
}

.item-chevron {
  font-size: 0.75rem;
  color: #6c757d;
}

.item-toggle.expanded .item-chevron {
  color: #0066ff;
}

.item-content {
  padding: 1rem;
  color: #4a5568;
  line-height: 1.6;
  background: #ffffff;
  border-top: 1px solid #e0e0e0;
}

.item-description {
  margin: 0 0 0.75rem;
}

.suggestion-box {
  background: #f0f7ff;
  border-left: 3px solid #0066ff;
  padding: 0.75rem 1rem;
  border-radius: 0 8px 8px 0;
  color: #1a1a2e;
}

.practice-button-container {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
  text-align: center;
}

.practice-weak-areas-btn {
  background: linear-gradient(135deg, #0066ff 0%, #0052cc 100%);
  color: white;
  border: none;
  padding: 1rem 2.5rem;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0, 102, 255, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
}

.practice-weak-areas-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 102, 255, 0.4);
}

.practice-weak-areas-btn:active {
  transform: translateY(0);
}

.practice-hint {
  color: #6c757d;
  font-size: 0.875rem;
  margin: 0.75rem 0 0;
}
</style>
