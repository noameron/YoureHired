import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  SearchFilters,
  AnalysisResult,
  RepoMetadata,
  ScoutSearchResult,
} from '@/types/scout'

export const useScoutStore = defineStore('scout', () => {
  // Search state
  const filters = ref<SearchFilters>({
    languages: [],
    min_stars: 10,
    max_stars: 500000,
    topics: [],
    min_activity_date: null,
    license: null,
    query: '',
  })
  const currentRunId = ref<string | null>(null)
  const searchStatus = ref<string | null>(null)
  const searchPhase = ref<string | null>(null)
  const statusMessage = ref('')
  const isSearching = ref(false)

  // Results state
  const results = ref<AnalysisResult[]>([])
  const repos = ref<RepoMetadata[]>([])
  const warnings = ref<string[]>([])
  const totalDiscovered = ref(0)
  const totalFiltered = ref(0)
  const totalAnalyzed = ref(0)

  // Error state
  const error = ref<string | null>(null)

  // Computed
  const hasResults = computed(() => results.value.length > 0)
  const canSearch = computed(() => filters.value.languages.length > 0)

  function setSearchResult(data: ScoutSearchResult) {
    results.value = data.results
    repos.value = data.repos
    warnings.value = data.warnings
    totalDiscovered.value = data.total_discovered
    totalFiltered.value = data.total_filtered
    totalAnalyzed.value = data.total_analyzed
    searchStatus.value = data.status
  }

  function resetSearch() {
    currentRunId.value = null
    searchStatus.value = null
    searchPhase.value = null
    statusMessage.value = ''
    isSearching.value = false
    results.value = []
    repos.value = []
    warnings.value = []
    error.value = null
    totalDiscovered.value = 0
    totalFiltered.value = 0
    totalAnalyzed.value = 0
  }

  return {
    filters, currentRunId, searchStatus, searchPhase,
    statusMessage, isSearching,
    results, repos, warnings,
    totalDiscovered, totalFiltered, totalAnalyzed,
    error,
    hasResults, canSearch,
    setSearchResult, resetSearch,
  }
})
