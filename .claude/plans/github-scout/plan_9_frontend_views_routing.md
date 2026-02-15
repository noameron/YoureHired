# Plan 9: Frontend Views & Routing

**Branch:** `scout/09-frontend-views-routing`
**Depends on:** plan_8 (needs types, store, service)
**Blocks:** nothing (final plan)

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — "New frontend page (`/scout`) with filter inputs [...] and a developer profile form"
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 10.1-10.8

## Production Files (5)

### 1. CREATE `frontend/src/views/ScoutView.vue`

Follow pattern from `frontend/src/views/PracticeView.vue` — `<script setup>` with composables, reactive state, lifecycle hooks, `AbortController` for SSE cancellation.

**Template sections:**

1. **Profile form** — languages (comma-separated input), topics (comma-separated input), skill level (radio: beginner/intermediate/advanced), goals (textarea). "Save Profile" button. Disabled/hidden once profile saved (shows summary instead with "Edit" toggle).

2. **Filter form** — languages (comma-separated input), star range (two number inputs: min/max), topics (comma-separated input), activity date (date input), license (select: mit/apache-2.0/gpl-3.0/etc or blank). "Search" button. Disabled until profile is saved.

3. **Progress display** — visible during search. Phase indicator (discovering/filtering/analyzing), status message text, cancel button. Uses `AbortController` + `cancelSearch(runId)`.

4. **Results grid** — visible after search completes. Shows warnings banner if any. Renders `ScoutResultCard` for each result. Shows "No matching repos found" if results empty.

**Script setup logic:**

```typescript
// On mount: load existing profile
onMounted(async () => {
  store.profileLoading = true
  try {
    const existing = await getProfile()
    if (existing) store.profile = existing
  } finally {
    store.profileLoading = false
  }
})

// Save profile handler
async function handleSaveProfile(profile: DeveloperProfile) {
  await saveProfile(profile)
  const saved = await getProfile()
  if (saved) store.profile = saved
}

// Search handler
let abortController: AbortController | null = null

async function handleSearch() {
  store.resetSearch()
  store.isSearching = true
  store.error = null
  abortController = new AbortController()

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

// Cancel handler
function handleCancel() {
  abortController?.abort()
  if (store.currentRunId) cancelSearch(store.currentRunId)
  store.resetSearch()
}
```

Uses `<style scoped src="./ScoutView.styles.css"></style>` (separate CSS file).

### 2. CREATE `frontend/src/views/ScoutView.styles.css`

Follow pattern from `frontend/src/views/PracticeView.styles.css` — use design tokens from `assets/design-tokens.css`.

Key layout:
- Full-width page container with max-width
- Profile section and filter section side-by-side or stacked
- Progress section centered with spinner
- Results as a responsive grid of cards

### 3. CREATE `frontend/src/components/ScoutResultCard.vue`

Follow pattern from `frontend/src/components/DrillCard.vue` — props, emits, scoped styles.

```typescript
defineProps<{
  result: AnalysisResult
  repo: RepoMetadata
}>()
```

**Template:**
- Repo name as external link (`<a :href="repo.url" target="_blank">{{ repo.owner }}/{{ repo.name }}</a>`)
- Score badge (color-coded: 8+ green, 5-7 yellow, <5 red)
- Description text
- Reason text
- Contributions list (`<ul>` with each suggestion)
- Metadata row: star count, primary language, open issues, license

Uses inline `<style scoped>` (not a separate CSS file, to stay within 5-file limit).

### 4. MODIFY `frontend/src/router/index.ts`

Add after the `/practice` route object (after line 23):

```typescript
{
  path: '/scout',
  name: 'scout',
  component: () => import('@/views/ScoutView.vue')
}
```

No `beforeEnter` guard — Scout is independent of practice sessions.

### 5. MODIFY `frontend/src/App.vue`

Add a minimal nav bar. Current `App.vue` is just `<RouterView />` — wrap it with a layout:

```vue
<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'

import '@/assets/design-tokens.css'
import '@/assets/base.css'
</script>

<template>
  <nav class="app-nav">
    <RouterLink to="/" class="nav-link">Practice</RouterLink>
    <RouterLink to="/scout" class="nav-link">Scout</RouterLink>
  </nav>
  <RouterView />
</template>

<style>
#app {
  min-height: 100vh;
}

.app-nav {
  display: flex;
  gap: var(--space-md, 1rem);
  padding: var(--space-sm, 0.5rem) var(--space-lg, 2rem);
  border-bottom: 1px solid var(--color-border, #e0e0e0);
}

.nav-link {
  text-decoration: none;
  font-weight: 500;
}

.nav-link.router-link-active {
  font-weight: 700;
}
</style>
```

## Test Files

- `frontend/tests/views/ScoutView.spec.ts`
  - Renders profile form when no profile exists
  - Loads existing profile on mount
  - Shows filter form after profile saved
  - Search button triggers API call
  - Displays progress during search (status messages, phase)
  - Displays results after completion
  - Cancel button aborts stream and calls cancelSearch
  - Shows error message on search failure
  - Shows "No matching repos found" when results empty
  - Shows warnings banner when present

- `frontend/tests/components/ScoutResultCard.spec.ts`
  - Renders repo name as link with correct URL
  - Renders score badge with correct value
  - Score badge color: green for 8+, yellow for 5-7, red for <5
  - Renders contributions list
  - Renders repo metadata (stars, language, issues)
  - Handles missing description gracefully

## Edge Cases

- User navigates to `/scout` before backend running → API calls fail, error state shown
- Profile form: empty languages → validation prevents submission
- Filter form: `min_stars > max_stars` → validation prevents submission
- Cancel mid-search → `AbortController.abort()` + `cancelSearch(runId)` + `store.resetSearch()`
- Empty results → "No matching repos found" message
- Warnings (1000-cap) → banner above results grid
- Profile form submitted with whitespace-only languages → trim before sending
- Score exactly 0 → treated as red badge
- Score exactly 10 → treated as green badge

## Verification

```bash
cd frontend && npm run test:run -- tests/views/ScoutView.spec.ts tests/components/ScoutResultCard.spec.ts
```

**Manual E2E (full stack running):**
1. Navigate to `/scout`
2. Fill and save profile (languages: "Python, Go", topics: "web", skill: intermediate, goals: "Contribute to API frameworks")
3. Set filters (languages: "Python", stars: 100-10000, topics: "fastapi")
4. Click Search → verify SSE progress updates appear
5. View scored results → verify cards show score, reason, contributions
6. Cancel mid-search → verify stream stops and UI resets
7. Navigate to `/` → verify Practice page still works
8. Navigate back to `/scout` → verify profile persists
