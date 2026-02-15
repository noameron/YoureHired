# Change: Add GitHub Scout — AI-Powered Repo Discovery

## Why

Finding open-source repos worth contributing to is a manual, hit-or-miss process. Developers waste time browsing GitHub Explore, reading threads, and stumbling onto repos that may not match their skills or goals. YoureHired already helps candidates practice for roles — GitHub Scout extends this by helping them find real open-source projects to contribute to, sharpening their skills on production codebases that match their tech stack.

## What Changes

- **New frontend page** (`/scout`) with filter inputs (language, stars, topics, activity) and a developer profile form
- **New backend module** for GitHub GraphQL API integration — discovers repos matching user criteria
- **Rule-based filtering engine** that reduces thousands of repos to ~20-50 candidates before AI analysis (V1 warns users if results reach GitHub's 1,000-result cap and suggests narrowing filters)
- **New AI agent** (`repo_analyst`) that scores repos in batches of 5-10 against the user's profile, providing fit scores, reasons, and suggested contributions (batches run concurrently for efficiency)
- **SQLite persistence layer** for storing discovered repos, analysis results, and developer profiles across sessions
- **New API endpoints** for triggering searches, managing profiles, and retrieving results
- **SSE streaming** for real-time progress during discovery and analysis phases

## Impact

- Affected specs: None (all new capabilities)
- New specs: `github-scout-discovery`, `github-scout-analysis`, `github-scout-ui`, `github-scout-persistence`
- Affected code:
  - `backend/app/api/` — new router (`scout.py`)
  - `backend/app/agents/` — new agent (`repo_analyst_agent.py`)
  - `backend/app/services/` — new services (`github_client.py`, `repo_filtering.py`, `scout_analysis.py`, `scout_orchestrator.py`)
  - `backend/app/schemas/` — new schemas (`scout.py`)
  - `backend/app/config.py` — new settings (GitHub token, SQLite path, timeouts)
  - `frontend/src/views/` — new view (`ScoutView.vue`)
  - `frontend/src/stores/` — new store (`scout.ts`)
  - `frontend/src/services/` — new API service functions
  - `frontend/src/router/` — new route (`/scout`)
- New dependency: `aiohttp` or `httpx` for async GitHub GraphQL requests; `aiosqlite` for async SQLite access
