# Plan 8: Frontend Types, Store & API Service

**Branch:** `scout/08-frontend-types-store-service`
**Depends on:** plan_1 conceptually (TypeScript types mirror Pydantic schemas). Can develop in parallel with backend plans 4-7.
**Blocks:** plan_9

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — "New frontend page", SSE streaming
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 9.1-9.4

## Production Files (3)

### 1. CREATE `frontend/src/types/scout.ts`

Follow pattern from `frontend/src/types/api.ts` (interfaces, discriminated unions).

```typescript
export type SkillLevel = 'beginner' | 'intermediate' | 'advanced'

export interface DeveloperProfile {
  languages: string[]
  topics: string[]
  skill_level: SkillLevel
  goals: string
}

export interface DeveloperProfileResponse {
  id: string
  profile: DeveloperProfile
  created_at: string
  updated_at: string | null
}

export interface SearchFilters {
  languages: string[]
  min_stars: number
  max_stars: number
  topics: string[]
  min_activity_date: string | null
  license: string | null
}

export interface RepoMetadata {
  github_id: number
  owner: string
  name: string
  url: string
  description: string | null
  primary_language: string | null
  languages: string[]
  star_count: number
  fork_count: number
  open_issue_count: number
  topics: string[]
  license: string | null
  pushed_at: string | null
  created_at: string | null
  good_first_issue_count: number
  help_wanted_count: number
}

export interface AnalysisResult {
  repo: string
  fit_score: number
  reason: string
  contributions: string[]
  reject: boolean
  reject_reason: string | null
}

export interface SearchRunResponse {
  run_id: string
  status: string
}

export interface ScoutSearchResult {
  run_id: string
  status: string
  total_discovered: number
  total_filtered: number
  total_analyzed: number
  results: AnalysisResult[]
  repos: RepoMetadata[]
  warnings: string[]
}

// SSE event types (discriminated union)
export interface ScoutStreamStatusEvent {
  type: 'status'
  message: string
  phase?: 'discovering' | 'filtering' | 'analyzing'
}

export interface ScoutStreamCompleteEvent {
  type: 'complete'
  data: ScoutSearchResult
}

export interface ScoutStreamErrorEvent {
  type: 'error'
  message: string
}

export type ScoutStreamEvent =
  | ScoutStreamStatusEvent
  | ScoutStreamCompleteEvent
  | ScoutStreamErrorEvent
```

### 2. CREATE `frontend/src/services/scout.ts`

Follow pattern from `frontend/src/services/api.ts` — native `fetch`, manual SSE parsing with `ReadableStream`, `AbortController`, fire-and-forget cancel.

```typescript
import type {
  DeveloperProfile,
  DeveloperProfileResponse,
  SearchFilters,
  SearchRunResponse,
  ScoutSearchResult,
  ScoutStreamEvent,
} from '@/types/scout'

const API_BASE = '/api'

export async function saveProfile(profile: DeveloperProfile): Promise<{ id: string }> {
  const response = await fetch(`${API_BASE}/scout/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  if (!response.ok) throw new Error(`Failed to save profile: ${response.status}`)
  return response.json()
}

export async function getProfile(): Promise<DeveloperProfileResponse | null> {
  const response = await fetch(`${API_BASE}/scout/profile`)
  if (response.status === 404) return null
  if (!response.ok) throw new Error(`Failed to fetch profile: ${response.status}`)
  return response.json()
}

export async function startSearch(filters: SearchFilters): Promise<SearchRunResponse> {
  const response = await fetch(`${API_BASE}/scout/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filters),
  })
  if (response.status === 429) {
    const data = await response.json()
    throw new Error(data.detail || 'Rate limit exceeded')
  }
  if (!response.ok) throw new Error(`Failed to start search: ${response.status}`)
  return response.json()
}

export async function* streamSearchProgress(
  runId: string,
  signal?: AbortSignal,
): AsyncGenerator<ScoutStreamEvent> {
  // Exact same SSE parsing pattern as streamDrillGeneration in api.ts:54-83
  const url = `${API_BASE}/scout/search/${runId}/stream`
  const response = signal ? await fetch(url, { signal }) : await fetch(url)

  if (!response.ok) throw new Error(`Stream failed: ${response.status}`)

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6)) as ScoutStreamEvent
      }
    }
  }
}

export async function getSearchResults(runId: string): Promise<ScoutSearchResult> {
  const response = await fetch(`${API_BASE}/scout/search/${runId}/results`)
  if (!response.ok) throw new Error(`Failed to fetch results: ${response.status}`)
  return response.json()
}

export async function cancelSearch(runId: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/scout/search/${runId}/cancel`, { method: 'POST' })
  } catch {
    // fire-and-forget: silently ignore errors (matches cancelGeneration pattern in api.ts:90-96)
  }
}
```

### 3. CREATE `frontend/src/stores/scout.ts`

Follow pattern from `frontend/src/stores/userSelection.ts` — Composition API with `defineStore`, `ref`, `computed`.

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  DeveloperProfileResponse,
  SearchFilters,
  AnalysisResult,
  RepoMetadata,
  ScoutSearchResult,
} from '@/types/scout'

export const useScoutStore = defineStore('scout', () => {
  // Profile state
  const profile = ref<DeveloperProfileResponse | null>(null)
  const profileLoading = ref(false)

  // Search state
  const filters = ref<SearchFilters>({
    languages: [],
    min_stars: 10,
    max_stars: 50000,
    topics: [],
    min_activity_date: null,
    license: null,
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
  const hasProfile = computed(() => profile.value !== null)
  const hasResults = computed(() => results.value.length > 0)

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
    profile, profileLoading,
    filters, currentRunId, searchStatus, searchPhase,
    statusMessage, isSearching,
    results, repos, warnings,
    totalDiscovered, totalFiltered, totalAnalyzed,
    error,
    hasProfile, hasResults,
    setSearchResult, resetSearch,
  }
})
```

**Note:** Store does NOT call API directly — the view/composables handle orchestration, just like `PracticeView.vue` does with `streamDrillGeneration`.

## Test Files

- `frontend/tests/services/scout.spec.ts`
  - `saveProfile` sends POST with correct body, returns `{ id }`
  - `getProfile` returns profile on 200, returns `null` on 404
  - `startSearch` sends POST, returns `SearchRunResponse`
  - `startSearch` throws on 429 with detail message
  - `streamSearchProgress` yields events from SSE stream
  - `streamSearchProgress` handles stream end gracefully
  - `getSearchResults` returns results on 200, throws on error
  - `cancelSearch` is fire-and-forget (no throw on failure)
  - Mock `fetch` for all tests (reuse pattern from `frontend/tests/services/api.spec.ts`)

- `frontend/tests/stores/scout.spec.ts`
  - Initial state has empty profile, empty results
  - `hasProfile` is `false` initially, `true` after setting profile
  - `hasResults` is `false` initially, `true` after `setSearchResult`
  - `setSearchResult` populates all result fields
  - `resetSearch` clears all search/result state
  - `resetSearch` does not clear profile

## Edge Cases

- `getProfile()` on 404 → returns `null` (not throw)
- `startSearch()` on 429 → parses `detail` from response JSON, throws `Error` with message
- `streamSearchProgress` network error → async generator throws, caller catches
- `cancelSearch` failure → silently ignored
- Store `resetSearch` preserves profile state (profile is separate from search lifecycle)

## Verification

```bash
cd frontend && npm run test:run -- tests/services/scout.spec.ts tests/stores/scout.spec.ts
```
