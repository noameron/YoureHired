<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useScoutStore } from '@/stores/scout'
import {
  getProfile,
  saveProfile,
  startSearch,
  streamSearchProgress,
  cancelSearch,
} from '@/services/scout'
import { parseCommaSeparated } from '@/utils/string'
import type { DeveloperProfile, SkillLevel, AnalysisResult, RepoMetadata } from '@/types/scout'
import ScoutResultCard from '@/components/ScoutResultCard.vue'

const store = useScoutStore()

// Profile form state
const profileLanguages = ref('')
const profileTopics = ref('')
const profileSkillLevel = ref<SkillLevel>('intermediate')
const profileGoals = ref('')
const profileErrors = ref<Record<string, string>>({})
const profileSaveError = ref<string | null>(null)

// Filter form state
const filterLanguages = ref('')
const filterTopics = ref('')
const filterMinStars = ref(10)
const filterMaxStars = ref(50000)
const filterActivityDate = ref('')
const filterLicense = ref('')

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

// Clear validation errors as user fixes fields
watch(profileLanguages, (val) => {
  if (parseCommaSeparated(val).length > 0) {
    delete profileErrors.value.languages
  }
})

watch(profileGoals, (val) => {
  if (val.trim()) {
    delete profileErrors.value.goals
  }
})

onMounted(async () => {
  store.profileLoading = true
  try {
    const existing = await getProfile()
    if (existing) store.profile = existing
  } finally {
    store.profileLoading = false
  }
})

async function handleSaveProfile() {
  profileErrors.value = {}
  profileSaveError.value = null

  const languages = parseCommaSeparated(profileLanguages.value)
  const topics = parseCommaSeparated(profileTopics.value)

  if (languages.length === 0) {
    profileErrors.value.languages = 'At least one language is required'
  }
  if (!profileGoals.value.trim()) {
    profileErrors.value.goals = 'Goals are required'
  }
  if (Object.keys(profileErrors.value).length > 0) return

  const profile: DeveloperProfile = {
    languages,
    topics,
    skill_level: profileSkillLevel.value,
    goals: profileGoals.value,
  }

  try {
    await saveProfile(profile)
    const saved = await getProfile()
    if (saved) store.profile = saved
  } catch (err) {
    profileSaveError.value = err instanceof Error ? err.message : 'Failed to save profile'
  }
}

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
  abortController?.abort()
  if (store.currentRunId) cancelSearch(store.currentRunId)
  store.resetSearch()
}
</script>

<template>
  <div class="scout-view">
    <h1 class="page-title">
      GitHub Scout
    </h1>

    <!-- Profile Loading -->
    <div
      v-if="store.profileLoading"
      data-testid="profile-loading"
      class="profile-loading"
    >
      <div class="spinner" />
      <p class="status-message">
        Loading profile...
      </p>
    </div>

    <!-- Profile Form -->
    <div
      v-if="!store.hasProfile && !store.profileLoading"
      data-testid="profile-form"
      class="profile-section card"
    >
      <h2>Developer Profile</h2>
      <form @submit.prevent="handleSaveProfile">
        <div class="form-group">
          <label for="profile-languages">Languages (comma-separated)</label>
          <input
            id="profile-languages"
            v-model="profileLanguages"
            name="languages"
            type="text"
            class="input"
            :class="{ 'input-error': profileErrors.languages }"
            placeholder="Python, TypeScript, Go"
          >
          <p
            v-if="profileErrors.languages"
            class="field-error"
          >
            {{ profileErrors.languages }}
          </p>
        </div>
        <div class="form-group">
          <label for="profile-topics">Topics (comma-separated)</label>
          <input
            id="profile-topics"
            v-model="profileTopics"
            name="topics"
            type="text"
            class="input"
            placeholder="web, api, machine-learning"
          >
        </div>
        <div class="form-group">
          <label>Skill Level</label>
          <div class="radio-group">
            <label>
              <input
                v-model="profileSkillLevel"
                type="radio"
                name="skill_level"
                value="beginner"
              >
              Beginner
            </label>
            <label>
              <input
                v-model="profileSkillLevel"
                type="radio"
                name="skill_level"
                value="intermediate"
              >
              Intermediate
            </label>
            <label>
              <input
                v-model="profileSkillLevel"
                type="radio"
                name="skill_level"
                value="advanced"
              >
              Advanced
            </label>
          </div>
        </div>
        <div class="form-group">
          <label for="profile-goals">Goals</label>
          <textarea
            id="profile-goals"
            v-model="profileGoals"
            name="goals"
            class="input"
            :class="{ 'input-error': profileErrors.goals }"
            placeholder="What are your open-source contribution goals?"
            rows="3"
          />
          <p
            v-if="profileErrors.goals"
            class="field-error"
          >
            {{ profileErrors.goals }}
          </p>
        </div>
        <p
          v-if="profileSaveError"
          data-testid="profile-save-error"
          class="error-message"
        >
          {{ profileSaveError }}
        </p>
        <button
          type="submit"
          class="btn btn-primary"
        >
          Save Profile
        </button>
      </form>
    </div>

    <!-- Profile Summary -->
    <div
      v-if="store.hasProfile"
      class="profile-summary card"
    >
      <h2>Your Profile</h2>
      <p>Languages: {{ store.profile?.profile.languages.join(', ') }}</p>
      <p>Topics: {{ store.profile?.profile.topics.join(', ') }}</p>
      <p>Level: {{ store.profile?.profile.skill_level }}</p>
      <p>Goals: {{ store.profile?.profile.goals }}</p>
    </div>

    <!-- Filter Form -->
    <form
      v-if="store.hasProfile"
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
      <button
        type="submit"
        class="btn btn-primary"
        :disabled="store.isSearching"
      >
        Search
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
      <button
        v-if="store.isSearching"
        type="button"
        data-testid="cancel-search"
        class="btn btn-secondary"
        @click="handleCancel"
      >
        Cancel
      </button>
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
