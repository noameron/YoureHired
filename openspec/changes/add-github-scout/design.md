## Context

GitHub Scout adds a full discovery-to-analysis pipeline for finding contribution-worthy open-source repos. It introduces a new external dependency (GitHub GraphQL API), a new persistence layer (SQLite), and a new AI agent — making it the first feature in YoureHired that doesn't rely solely on in-memory session state.

**Stakeholders:** Developer users who want to find repos matching their skills.
**Constraints:** GitHub API rate limits (5,000 GraphQL points/hr authenticated), 1,000-result search cap per query, existing YoureHired patterns must be followed.

## Goals / Non-Goals

**Goals:**
- Discover repos via GitHub GraphQL API with user-defined filters
- Filter candidates using server-side qualifiers + client-side rules before AI analysis
- Score and rank repos against a user's developer profile using a single AI agent
- Persist results in SQLite so they survive across sessions
- Provide a web UI page with filter form, profile management, and results display
- Stream progress to the frontend during discovery and analysis

**Non-Goals:**
- Incremental refresh / ETag caching (future enhancement)
- Cost transparency dashboard (future enhancement)
- Issue-level deep-dive matching (future enhancement)
- Multi-agent architecture (start with single agent; split if quality suffers)
- GH Archive / BigQuery integration (future enhancement)
- CLI interface (web-only for V1)

## Decisions

### 1. GitHub GraphQL API as primary data source

**Decision:** Use GitHub's GraphQL API for all repo discovery.
**Why:** One query fetches metadata + languages + issue counts + README for ~20 repos. Replaces 3-5 REST calls per repo. Point-based rate limit (5,000 pts/hr) is generous.
**Alternatives considered:**
- REST API — requires multiple calls per repo, inefficient for bulk discovery
- HTML scraping — violates ToS, fragile, slow
- GH Archive — lacks repo content, requires BigQuery setup

### 2. Two-phase filtering: server-side qualifiers + client-side rules

**Decision:** Apply GitHub search qualifiers first (language, stars, activity, archived, fork), then client-side rules (reject tutorials/awesome-lists, minimum issues, good-first-issue labels).
**Why:** Server-side filters eliminate 90%+ of irrelevant repos for free. Client-side rules catch patterns GitHub can't filter (tutorial detection, contribution signals). This keeps AI agent costs minimal by only analyzing ~20-50 repos.

### 3. Fetch README after client-side filtering

**Decision:** Discovery phase fetches metadata only. README is fetched in a second GraphQL pass for repos that survive client-side filtering.
**Why:** READMEs are large payloads. Fetching them for all discovered repos wastes bandwidth on repos that will be rejected. Two-phase approach saves 50-70% of README transfer.

### 4. Deferred: Time-bucketing to bypass the 1,000-result cap

**Decision (V1):** V1 does not implement time-bucketing. Instead, when a search returns 1,000 results (GitHub's maximum per query), the system warns the user that results may be incomplete and suggests narrowing filters (fewer topics, smaller star range, more recent activity). Time-bucketing is deferred to V2.
**Why (original):** GitHub search returns at most 1,000 results per query. For popular languages/topics, a single query hits this cap. Time-bucketing combined with narrow qualifiers would ensure complete coverage — but adds significant complexity for V1.
**V2 plan:** Split the query into monthly time buckets on the `pushed` date field and execute each bucket separately, merging and deduplicating results by GitHub repository ID.

### 5. Batched AI agent with structured JSON output

**Decision:** Batch 5-10 repos per agent call, run batches concurrently using `asyncio.as_completed`. Each call returns an array of `{ fit_score, reason, contributions[] }` objects.
**Why:** ~40-60% cheaper than per-repo calls due to amortized prompt overhead (system prompt, developer profile, and scoring rubric sent once per batch instead of once per repo). For ~30 repos, this means 3-6 batch calls instead of 30 individual calls.
**Trade-off:** SSE progress granularity changes from per-repo to per-batch. Progress events emit after each batch completes (e.g., "Analyzed 10/34 repos...") rather than after each individual repo.
**Output schema (per batch):**
```json
[
  {
    "repo": "owner/repo-name",
    "fit_score": 8.5,
    "reason": "FastAPI project with open auth issues matching your backend skills",
    "contributions": [
      "Add OAuth2 tests for the Microsoft provider",
      "Refactor dependency injection in auth module"
    ],
    "reject": false,
    "reject_reason": null
  }
]
```

### 6. SQLite for persistence

**Decision:** Use SQLite via `aiosqlite` for storing repos, analysis results, and developer profiles.
**Why:** Zero config, single file, ships with Python. Perfect for a personal/single-user tool. Supports SQL queries for result browsing. The existing session store is in-memory with 24hr TTL — SQLite gives permanent persistence without introducing Postgres overhead.
**Schema highlights:**
- `developer_profiles` — languages, topics, skill level, goals
- `search_runs` — tracks each discovery run (filters used, timestamp, status)
- `repositories` — discovered repo metadata (deduplicated by GitHub ID)
- `analysis_results` — AI agent output per repo per search run

### 7. SSE streaming for progress updates

**Decision:** Reuse the existing SSE pattern from drill generation for streaming progress during discovery and analysis.
**Why:** Discovery (GitHub API calls) and analysis (LLM calls) are long-running. The existing SSE pattern is proven and the frontend already handles streaming events. Event types: `"discovering"`, `"filtering"`, `"analyzing"`, `"complete"`, `"error"`.

### 8. GitHub token via environment variable

**Decision:** Add `GITHUB_TOKEN` to `Settings` in `config.py`, loaded from `.env`.
**Why:** Follows the existing pattern for API keys (e.g., `OPENAI_API_KEY`). Unauthenticated GitHub requests are limited to 60/hr — unusable for discovery. A personal access token provides 5,000/hr.

### 9. Orchestrator decomposition

**Decision:** Split `scout_orchestrator.py` into focused services: `github_client.py` (GitHub API interaction), `repo_filtering.py` (client-side filtering logic), `scout_analysis.py` (batch analysis coordination). The orchestrator remains as a thin coordinator that wires these services together.
**Why:** A monolithic orchestrator handling GitHub API calls, filtering, and AI analysis in one file becomes hard to test and reason about. Separating concerns allows each service to be tested independently and modified without risk to unrelated logic.

### 10. Rate limiting on search endpoint

**Decision:** Enforce a concurrent search limit (1 active search at a time) and an IP-based throttle (5 searches per hour).
**Why:** The `POST /api/scout/search` endpoint is session-independent and triggers AI agent calls that cost money. Without rate limiting, a single user (or bot) could run unlimited searches and rack up unbounded AI spend. Rate limiting prevents runaway costs and ensures fair resource usage.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| GitHub rate limit exhaustion during large searches | Check remaining quota before each batch; abort gracefully with partial results if limit approached |
| 1,000-result cap causes missed repos | V1 warns user and suggests narrowing filters; time-bucketing deferred to V2 |
| README content too large for LLM context | Truncate README to first 4,000 tokens before sending to agent |
| SQLite concurrency issues if multiple searches run | Use WAL mode; queue searches so only one runs at a time per profile |
| Agent produces inconsistent scores across runs | Use a specific scoring rubric in the system prompt with concrete examples |
| GitHub GraphQL schema changes | Pin to current schema version; add integration tests against live API (optional, manual) |
| No authentication on search endpoint | Rate limiting: 1 concurrent search + 5 searches/hour per IP prevents runaway AI spend |
| Unbounded repository table growth | TTL/pruning: delete repos not referenced by any analysis result and not seen in 30 days |

## Migration Plan

No migration needed — this is a greenfield feature. No existing data or APIs are modified.

## Open Questions

1. ~~**Should the Scout page require an active session (company + role) or be independent?**~~ — **Decided: independent.** Users may want to find repos without first selecting a job target. The developer profile serves as the matching context instead.
2. **Maximum repos to analyze per search run?** — Recommendation: cap at 50 to keep LLM costs predictable (~$0.10/run). Also add a daily global cap on total analyses to prevent abuse.
3. **Should results link directly to specific GitHub issues?** — Deferred to V2. The agent suggests contribution areas but doesn't deep-link to issue URLs.
