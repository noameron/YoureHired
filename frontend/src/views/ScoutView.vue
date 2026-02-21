<script setup lang="ts">
import { ref, computed } from 'vue'
import { useScoutStore } from '@/stores/scout'
import {
  startSearch,
  streamSearchProgress,
  cancelSearch,
} from '@/services/scout'
import { parseCommaSeparated } from '@/utils/string'
import type { AnalysisResult, RepoMetadata } from '@/types/scout'
import ScoutResultCard from '@/components/ScoutResultCard.vue'

const store = useScoutStore()

// Filter form state
const filterLanguages = ref('')
const filterTopics = ref('')
const filterMinStars = ref(10)
const filterMaxStars = ref(500000)
const filterActivityDate = ref('')
const filterLicense = ref('')
const filterQuery = ref('')

let abortController: AbortController | null = null

const searchCompleted = computed(() => store.searchStatus !== null && !store.isSearching)

const resultPairs = computed(() => {
  const repoMap = new Map(store.repos.map(r => [`${r.owner}/${r.name}`, r]))
  const pairs: Array<{ result: AnalysisResult; repo: RepoMetadata }> = []
  for (const result of store.results) {
    const repo = repoMap.get(result.repo)
    if (repo) pairs.push({ result, repo })
  }
  return pairs
})

async function handleSearch() {
  store.resetSearch()
  store.isSearching = true
  store.error = null
  abortController = new AbortController()

  store.filters = {
    languages: parseCommaSeparated(filterLanguages.value),
    min_stars: filterMinStars.value,
    max_stars: filterMaxStars.value,
    topics: parseCommaSeparated(filterTopics.value),
    min_activity_date: filterActivityDate.value || null,
    license: filterLicense.value || null,
    query: filterQuery.value,
  }

  try {
    const { run_id } = await startSearch(store.filters)
    store.currentRunId = run_id

    for await (const event of streamSearchProgress(run_id, abortController.signal)) {
      if (event.type === 'status') {
        store.statusMessage = event.message
        store.searchPhase = event.phase ?? null
      } else if (event.type === 'complete') {
        store.setSearchResult(event.data)
      } else if (event.type === 'error') {
        store.error = event.message
      }
    }
  } catch (err) {
    if (err instanceof Error && err.name !== 'AbortError') {
      store.error = err.message
    }
  } finally {
    store.isSearching = false
    abortController = null
  }
}

function handleCancel() {
  const runId = store.currentRunId
  abortController?.abort()
  if (runId) cancelSearch(runId)
  store.resetSearch()
}
</script>

<template>
  <div class="scout-view">
    <h1 class="page-title">
      GitHub Scout
    </h1>

    <!-- Filter Form -->
    <form
      data-testid="filter-form"
      class="filter-section card"
      @submit.prevent="handleSearch"
    >
      <h2>Search Filters</h2>
      <div class="form-group">
        <label for="filter-languages">Languages</label>
        <input
          id="filter-languages"
          v-model="filterLanguages"
          name="filter-languages"
          type="text"
          class="input"
          placeholder="Python, Go"
        >
      </div>
      <div class="form-row">
        <div class="form-group">
          <label for="filter-min-stars">Min Stars</label>
          <input
            id="filter-min-stars"
            v-model.number="filterMinStars"
            name="min-stars"
            type="number"
            class="input"
          >
        </div>
        <div class="form-group">
          <label for="filter-max-stars">Max Stars</label>
          <input
            id="filter-max-stars"
            v-model.number="filterMaxStars"
            name="max-stars"
            type="number"
            class="input"
          >
        </div>
      </div>
      <div class="form-group">
        <label for="filter-topics">Topics</label>
        <input
          id="filter-topics"
          v-model="filterTopics"
          name="filter-topics"
          type="text"
          class="input"
          placeholder="fastapi, web"
        >
      </div>
      <div class="form-group">
        <label for="filter-activity">Recent Activity Since</label>
        <input
          id="filter-activity"
          v-model="filterActivityDate"
          name="activity-date"
          type="date"
          class="input"
        >
      </div>
      <div class="form-group">
        <label for="filter-license">License</label>
        <select
          id="filter-license"
          v-model="filterLicense"
          name="license"
          class="input"
        >
          <option value="">
            Any
          </option>
          <option value="mit">
            MIT
          </option>
          <option value="apache-2.0">
            Apache 2.0
          </option>
          <option value="gpl-3.0">
            GPL 3.0
          </option>
          <option value="bsd-2-clause">
            BSD 2-Clause
          </option>
          <option value="bsd-3-clause">
            BSD 3-Clause
          </option>
        </select>
      </div>
      <div class="form-group">
        <label for="filter-query">What kind of repos are you looking for?</label>
        <textarea
          id="filter-query"
          v-model="filterQuery"
          name="query"
          class="input"
          placeholder="e.g. Beginner-friendly Python web frameworks with good documentation"
          rows="2"
        />
      </div>
      <button
        v-if="!store.isSearching"
        type="submit"
        class="btn btn-primary"
      >
        Search Repos
      </button>
      <button
        v-else
        type="button"
        data-testid="cancel-search"
        class="btn btn-danger"
        @click="handleCancel"
      >
        Cancel Search
      </button>
    </form>

    <!-- Search Progress -->
    <div
      v-if="store.statusMessage || store.isSearching"
      data-testid="search-progress"
      class="search-progress"
    >
      <div class="spinner" />
      <p
        v-if="store.searchPhase"
        class="phase-indicator"
      >
        {{ store.searchPhase }}
      </p>
      <p class="status-message">
        {{ store.statusMessage }}
      </p>
    </div>

    <!-- Error State -->
    <div
      v-if="store.error"
      data-testid="search-error"
      class="error-state"
    >
      <p class="error-message">
        {{ store.error }}
      </p>
    </div>

    <!-- Warnings Banner -->
    <div
      v-if="store.warnings.length > 0"
      data-testid="warnings-banner"
      class="warnings-banner"
    >
      <p
        v-for="(warning, idx) in store.warnings"
        :key="idx"
      >
        {{ warning }}
      </p>
    </div>

    <!-- Empty Results -->
    <p
      v-if="searchCompleted && !store.hasResults"
      class="empty-results"
    >
      No matching repos found
    </p>

    <!-- Results Grid -->
    <div
      v-if="store.hasResults"
      class="results-grid"
    >
      <ScoutResultCard
        v-for="pair in resultPairs"
        :key="pair.result.repo"
        :result="pair.result"
        :repo="pair.repo"
      />
    </div>
  </div>
</template>

<style scoped src="./ScoutView.styles.css"></style>
