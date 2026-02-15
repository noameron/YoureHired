## 1. Backend: Configuration & Database Setup
- [ ] 1.1 Add `GITHUB_TOKEN`, `SCOUT_DB_PATH`, `scout_analysis_timeout`, `scout_max_repos`, and `scout_max_daily_analyses` to `Settings` in `backend/app/config.py`
- [ ] 1.2 Add `aiosqlite` and `httpx` (if not already present) to backend dependencies
- [ ] 1.3 Create `backend/app/services/scout_db.py` — SQLite initialization, WAL mode, schema creation (tables: `developer_profiles`, `search_runs`, `repositories`, `analysis_results`)
- [ ] 1.4 Write tests for database initialization, schema creation, and WAL mode activation
- [ ] 1.5 Implement repo TTL/pruning — delete repositories not referenced by any analysis result and not seen in the last 30 days (run on startup or daily)

## 2. Backend: Pydantic Schemas
- [ ] 2.1 Create `backend/app/schemas/scout.py` — define request/response models: `DeveloperProfile`, `SearchFilters`, `SearchRunResponse`, `RepoMetadata`, `AnalysisResult`, `ScoutSearchResult`
- [ ] 2.2 Write tests validating schema constraints (star range, language list non-empty, goal max length)

## 3. Backend: Developer Profile API
- [ ] 3.1 Create profile CRUD functions in `scout_db.py` — save, update, get (single-profile mode)
- [ ] 3.2 Create `backend/app/api/scout.py` router with `POST /api/scout/profile` and `GET /api/scout/profile` endpoints
- [ ] 3.3 Include scout router in `backend/app/api/__init__.py`
- [ ] 3.4 Write tests for profile endpoints (save, retrieve, update, 404 when empty)

## 4. Backend: GitHub GraphQL Client
- [ ] 4.1 Create `backend/app/services/github_client.py` — async GraphQL client with auth, rate limit checking, retry with backoff
- [ ] 4.2 Implement `search_repositories()` — constructs search query from filters; when result count reaches 1,000 (GitHub's max), include a warning in the response indicating results may be incomplete and suggest narrowing filters
- [ ] 4.3 Implement `fetch_readmes()` — batch README fetch using GraphQL aliases (up to 20 per query), with truncation to 4,000 tokens
- [ ] 4.4 Write tests for query construction, result-cap warning logic, retry behavior, and README truncation (mock GitHub API responses)

## 5. Backend: Filtering Engine
- [ ] 5.1 Create `backend/app/services/repo_filtering.py` — client-side filter functions
- [ ] 5.2 Implement tutorial/awesome-list detection (name + description pattern matching)
- [ ] 5.3 Implement contribution-signal scoring (good-first-issue count, help-wanted count)
- [ ] 5.4 Implement configurable threshold filters (min issues, star range validation, days since push)
- [ ] 5.5 Write tests for each filter rule with edge cases (repos that almost match, boundary values)

## 6. Backend: Repo Analyst Agent
- [ ] 6.1 Create Pydantic output schema for agent response (`RepoAnalysis` with fit_score, reason, contributions, reject, reject_reason)
- [ ] 6.2 Create `backend/app/agents/repo_analyst_agent.py` — agent accepts a batch of 5-10 repos with scoring rubric, profile-aware instructions, JSON array output enforcement, standard guardrails
- [ ] 6.3 Write tests for agent batch output schema validation — verify array of results, partial batch handling (mock agent responses)

## 7. Backend: Scout Orchestrator Service
- [ ] 7.1 Create `backend/app/services/scout_orchestrator.py` as thin coordinator; split batch analysis logic into `backend/app/services/scout_analysis.py` (groups repos into batches of 5-10, runs batches concurrently via `asyncio.as_completed`)
- [ ] 7.2 Implement SSE event streaming throughout the pipeline (phase transitions, per-batch progress — e.g., "Analyzed 10/34 repos...", completion/error)
- [ ] 7.3 Implement search run tracking — active run status only (no history browsing); create run, update status, record results in DB
- [ ] 7.7 Implement error recovery for partial batch results — when an agent batch fails but previous batches completed, return partial results, mark run as `partial`, and emit SSE event listing skipped repos
- [ ] 7.4 Implement cancellation support via task_registry
- [ ] 7.5 Implement analysis cap (max 50 repos) with sorting by contribution signals
- [ ] 7.6 Write tests for orchestration flow (mock GitHub client + mock agent), cancellation, and error handling

## 8. Backend: Search & Results API Endpoints
- [ ] 8.1 Add `POST /api/scout/search` — validates filters, creates search run, returns run ID; enforce rate limiting (1 concurrent search + 5 searches/hour per IP, return 429 with appropriate messaging)
- [ ] 8.2 Add `GET /api/scout/search/{run_id}/stream` — SSE endpoint streaming orchestrator progress
- [ ] 8.3 Add `GET /api/scout/search/{run_id}/results` — returns completed analysis results
- [ ] 8.4 Add `POST /api/scout/search/{run_id}/cancel` — cancels active search
- [ ] 8.5 Write tests for all search/result endpoints (happy path, not found, cancel, rate limiting 429 responses)

## 9. Frontend: Pinia Store & API Service
- [ ] 9.1 Create `frontend/src/stores/scout.ts` — state for filters, profile, search runs, results, loading/progress states
- [ ] 9.2 Add scout API functions to `frontend/src/services/api.ts` (or new `scout.ts` service) — profile CRUD, search trigger, results fetch, SSE stream handling, cancel
- [ ] 9.3 Create TypeScript types in `frontend/src/types/scout.ts` — matching backend schemas
- [ ] 9.4 Write tests for store actions and API service (mock HTTP responses)

## 10. Frontend: Scout View & Components
- [ ] 10.1 Create `frontend/src/views/ScoutView.vue` — page layout with filter form, profile section, results area
- [ ] 10.2 Create search filter form component — language multi-select, star range inputs, topic tags, activity date, license select
- [ ] 10.3 Create developer profile form component — languages, topics, skill level radio, goals textarea
- [ ] 10.4 Create result card component — repo name/link, score badge, description, reason, contribution suggestions
- [ ] 10.5 Implement streaming progress display — phase indicator, counts, cancel button
- [ ] 10.6 Add `/scout` route to `frontend/src/router/index.ts` (lazy-loaded, no session guard)
- [ ] 10.7 Add navigation link to Scout page visible from all pages
- [ ] 10.8 Write component tests for form validation, result rendering, and progress states

## 11. Integration & Polish
- [ ] 11.1 End-to-end manual test: fill profile → configure filters → run search → view results
- [ ] 11.2 Add `GITHUB_TOKEN` to `.env.example` with documentation comment including required GitHub PAT scopes (public_repo read access)
- [ ] 11.3 Verify rate limit handling with real GitHub API (manual test)
- [ ] 11.4 Add test that `GITHUB_TOKEN` never appears in any API response body or SSE event payload
- [ ] 11.5 Add test that partial-result error recovery works end-to-end (mock a batch failure mid-search)

---

### Dependency Notes
- Tasks 1-2 have no dependencies (can run in parallel)
- Task 3 depends on 1 + 2
- Tasks 4, 5, 6 depend on 2 (schemas); can run in parallel with each other
- Task 7 depends on 4 + 5 + 6 + 3 (all backend components); 7.7 (error recovery) depends on 7.1 (scout_analysis.py)
- Task 8 depends on 7; 8.1 (rate limiting) is self-contained within the endpoint
- Task 9 depends on 2 (TypeScript types mirror Pydantic schemas)
- Task 10 depends on 9
- Task 11 depends on all previous tasks; 11.4 (token security test) can start after 8.1

### Parallelization Opportunities
- **Branch A** (Tasks 1-3): Config + DB + Profile API + repo TTL
- **Branch B** (Tasks 4-5): GitHub client + Filtering — can start after Task 2
- **Branch C** (Task 6): Agent (batch mode) — can start after Task 2
- **Branch D** (Tasks 9-10): Frontend — can start after Task 2 (types), full integration after Task 8
