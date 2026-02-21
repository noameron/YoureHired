<script setup lang="ts">
import type { AnalysisResult, RepoMetadata } from '@/types/scout'

defineProps<{
  result: AnalysisResult
  repo: RepoMetadata
}>()

function scoreClass(score: number): string {
  if (score >= 8) return 'score-green'
  if (score >= 5) return 'score-yellow'
  return 'score-red'
}
</script>

<template>
  <div class="scout-result-card card">
    <div class="card-header">
      <a
        :href="repo.url"
        target="_blank"
        rel="noopener noreferrer"
        class="repo-link"
      >
        {{ repo.owner }}/{{ repo.name }}
      </a>
      <span
        data-testid="score-badge"
        class="score-badge badge"
        :class="scoreClass(result.fit_score)"
      >
        {{ result.fit_score }}
      </span>
    </div>

    <p
      v-if="repo.description"
      class="repo-description"
    >
      {{ repo.description }}
    </p>

    <p class="reason">
      {{ result.reason }}
    </p>

    <ul
      v-if="result.contributions.length"
      class="contributions"
    >
      <li
        v-for="(contribution, idx) in result.contributions"
        :key="idx"
      >
        {{ contribution }}
      </li>
    </ul>

    <div class="metadata-row">
      <span
        class="meta-item tag"
        aria-label="Stars"
      >★ {{ repo.star_count.toLocaleString() }}</span>
      <span
        v-if="repo.primary_language"
        class="meta-item tag"
        aria-label="Primary language"
      >{{ repo.primary_language }}</span>
      <span
        class="meta-item tag"
        aria-label="Open issues"
      >{{ repo.open_issue_count }} issues</span>
      <span
        v-if="repo.license"
        class="meta-item tag"
        aria-label="License"
      >{{ repo.license }}</span>
    </div>
  </div>
</template>

<style scoped>
.scout-result-card {
  padding: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.repo-link {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  color: var(--accent-primary);
}

.repo-link:hover {
  color: var(--accent-hover);
}

.score-badge {
  font-size: var(--text-lg);
  min-width: 2.5rem;
  text-align: center;
}

.score-green {
  background-color: var(--color-success-bg);
  color: var(--color-success-text);
  border-color: rgba(90, 138, 90, 0.3);
}

.score-yellow {
  background-color: var(--color-warning-bg);
  color: var(--color-warning-text);
  border-color: rgba(196, 154, 60, 0.3);
}

.score-red {
  background-color: var(--color-error-bg);
  color: var(--color-error-text);
  border-color: rgba(160, 64, 48, 0.3);
}

.repo-description {
  margin-bottom: var(--space-3);
}

.reason {
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
  line-height: var(--leading-relaxed);
}

.contributions {
  color: var(--text-secondary);
  padding-left: var(--space-6);
  margin-bottom: var(--space-4);
}

.contributions li {
  margin: var(--space-2) 0;
}

.metadata-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-primary);
}
</style>
