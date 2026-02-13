<script setup lang="ts">
import type { Drill } from '@/services/types'
import { useHints } from '@/composables/usePractice'

defineProps<{
  drill: Drill
  solution: string
  isEvaluating: boolean
  evaluationError: string | null
}>()

const emit = defineEmits<{
  (e: 'update:solution', value: string): void
  (e: 'submit'): void
}>()

const { toggleHint, isHintExpanded } = useHints()

function formatDrillType(type: string): string {
  return type.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>

<template>
  <div class="drill-card">
    <h1>{{ drill.title }}</h1>

    <div class="meta">
      <span class="type">{{ formatDrillType(drill.type) }}</span>
      <span
        class="difficulty"
        :class="drill.difficulty"
      >{{ drill.difficulty }}</span>
      <span class="time">{{ drill.expected_time_minutes }} min</span>
    </div>

    <p class="description">
      {{ drill.description }}
    </p>

    <section
      v-if="drill.company_context"
      class="section"
    >
      <h3>Company Context</h3>
      <p>{{ drill.company_context }}</p>
    </section>

    <section class="section">
      <h3>Requirements</h3>
      <ul class="requirements">
        <li
          v-for="(r, idx) in drill.requirements"
          :key="idx"
        >
          {{ r }}
        </li>
      </ul>
    </section>

    <section
      v-if="drill.tech_stack.length"
      class="section"
    >
      <h3>Tech Stack</h3>
      <div class="tags">
        <span
          v-for="(t, idx) in drill.tech_stack"
          :key="idx"
          class="tag"
        >{{ t }}</span>
      </div>
    </section>

    <section
      v-if="drill.starter_code"
      class="section"
    >
      <h3>Starter Code</h3>
      <pre class="code-block"><code>{{ drill.starter_code }}</code></pre>
    </section>

    <section
      v-if="drill.hints.length"
      class="hints-section"
    >
      <h3>Hints ({{ drill.hints.length }} available)</h3>
      <div class="hints-list">
        <div
          v-for="(hint, idx) in drill.hints"
          :key="idx"
          class="hint-item"
        >
          <button
            type="button"
            class="hint-toggle"
            :class="{ expanded: isHintExpanded(idx) }"
            @click="toggleHint(idx)"
          >
            <span class="hint-label">Hint {{ idx + 1 }}</span>
            <span class="hint-chevron">{{ isHintExpanded(idx) ? '\u25BC' : '\u25B6' }}</span>
          </button>
          <div
            v-show="isHintExpanded(idx)"
            class="hint-content"
          >
            {{ hint }}
          </div>
        </div>
      </div>
    </section>

    <section class="section solution-section">
      <h3>Your Solution</h3>
      <textarea
        :value="solution"
        class="solution-input"
        placeholder="Paste or type your solution here..."
        rows="12"
        spellcheck="false"
        :disabled="isEvaluating"
        @input="emit('update:solution', ($event.target as HTMLTextAreaElement).value)"
      />

      <p
        v-if="evaluationError"
        class="evaluation-error"
      >
        {{ evaluationError }}
      </p>

      <button
        type="button"
        class="btn btn-primary submit-solution-btn"
        :disabled="!solution.trim() || isEvaluating"
        @click="emit('submit')"
      >
        {{ isEvaluating ? 'Evaluating...' : 'Submit Solution' }}
      </button>
    </section>
  </div>
</template>

<style scoped src="./DrillCard.styles.css"></style>
